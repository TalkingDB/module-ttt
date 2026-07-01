import time
import os

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import uuid4

# Called as ``progress(done_units, total_units)`` during indexing.
# Any exception raised by the callback aborts indexing immediately.
ProgressCallback = Callable[[int, int], None]

from tqdm import tqdm

from talkingdb.models.document.document import DocumentModel
from talkingdb.models.document.elements.primitive.paragraph import ParagraphModel
from talkingdb.models.document.elements.primitive.table import TableModel
from talkingdb.models.document.indexes.index import (
    FileIndexModel,
    IndexItem,
    IndexType,
)
from talkingdb.models.graph.graph import GraphModel
from app.services.package_text_tokenizer import TextTokenizer
from app.services.package_symbol_generator import SymbolGenerator
from talkingdb.clients.sqlite import sqlite_conn
from talkingdb.logger.console import logger


class IndexerService:
    def __init__(self, max_workers: int | None = None):
        self.gm = GraphModel.create(GraphModel.make_id(uuid4().hex), True)
        self.tokenizer = TextTokenizer()
        self.symbol_generator = SymbolGenerator()
        self.max_workers = max_workers or (os.cpu_count() * 2)

    def graph_file_index(self, file_index: FileIndexModel) -> GraphModel:
        def walk(node: IndexItem, parent_id: str = None):
            node_id = node.id

            self.gm.graph.add_node(
                node_id,
                label=node.label,
                index=node.index,
            )

            if parent_id:
                self.gm.graph.add_edge(parent_id, node_id, type="part_of")

            for child in node.child:
                walk(child, node_id)

        self.gm.graph.add_node(
            file_index.id,
            label=getattr(file_index, "filename", None),
            index="file@root",
        )

        for top_node in file_index.nodes:
            walk(top_node, file_index.id)

        with sqlite_conn() as conn:
            self.gm.save(conn)

        return self.gm

    def _prepare_table_headers(
        self,
        document: DocumentModel,
        element: TableModel,
        heading_path: List[str],
    ) -> Dict[int, Dict[str, Any]]:

        header_cache = {}

        if not element.rows:
            return header_cache

        for col_idx in range(len(element.rows[0])):

            header_text = ", ".join(
                element.get_header(0, col_idx)
            )

            header_tokens = self.tokenizer.tokenize(header_text, False)
            header_symbols = self.symbol_generator.generate(header_tokens)
            key_id = self.symbol_generator.max_gram(header_tokens)

            header_cache[col_idx] = {
                "header_text": header_text,
                "header_symbols": header_symbols,
                "key_id": key_id,
                "metadata": {
                    "index": IndexType.TABLE_HEADER,
                    "heading_path": heading_path,
                    "filename": document.filename,
                    "page": element.page,
                },
            }

        return header_cache

    def _process_table_row(
        self,
        element: TableModel,
        node_id: str,
        row_idx: int,
        header_cache: Dict[int, Dict[str, Any]],
    ) -> Tuple[
        List[Tuple[str, Dict[str, Any]]],
        List[Tuple[str, str, Dict[str, Any]]],
    ]:

        nodes = []
        edges = []

        row = element.rows[row_idx]

        for col_idx, cell in enumerate(row):

            if col_idx not in header_cache:
                continue

            header_data = header_cache[col_idx]
            header_text = header_data["header_text"]
            header_symbols = header_data["header_symbols"]
            key_id = header_data["key_id"]
            header_metadata = header_data["metadata"]

            # HEADER NODE
            nodes.append(
                (
                    header_text,
                    {
                        "text": header_text,
                        "metadata": header_metadata,
                        "type": "header",
                    },
                )
            )

            edges.append((node_id, header_text, {"type": "part_of"}))

            for symbol_type, symbol_list in header_symbols.items():
                for symbol in symbol_list:
                    nodes.append((symbol, {"type": symbol_type}))
                    edges.append((header_text, symbol, {"type": "contains"}))

            # CELL
            cell_text = cell.to_text()
            if not cell_text:
                continue

            cell_tokens = self.tokenizer.tokenize(cell_text)
            cell_symbols = self.symbol_generator.generate(cell_tokens)

            for symbol_type, symbol_list in cell_symbols.items():
                for symbol in symbol_list:
                    nodes.append((symbol, {"type": symbol_type}))
                    edges.append((header_text, symbol, {"type": "contains"}))

            # KEY VALUE
            val_tokens = self.tokenizer.tokenize(cell_text, False)
            val_id = self.symbol_generator.max_gram(val_tokens)

            nodes.append((key_id, {"text": header_text, "is_key": True}))
            nodes.append((val_id, {"text": cell_text, "is_val": True}))
            edges.append((key_id, val_id, {"type": "key_value"}))

        return nodes, edges

    def _process_element(
        self,
        document: DocumentModel,
        element,
    ) -> Tuple[
        List[Tuple[str, Dict[str, Any]]],
        List[Tuple[str, str, Dict[str, Any]]],
    ]:

        nodes = []
        edges = []

        if isinstance(element, ParagraphModel):

            node_id = element.id
            text = element.to_text()

            tokens = self.tokenizer.tokenize(text)
            symbols = self.symbol_generator.generate(tokens)

            heading_path = document._get_heading_path(element)

            metadata = {
                "index": IndexType.PARA,
                "heading_path": heading_path,
                "filename": document.filename,
                "page": element.page,
            }

            nodes.append(
                (
                    node_id,
                    {
                        "text": text,
                        "metadata": metadata,
                        "type": "paragraph",
                    },
                )
            )

            for symbol_type, symbol_list in symbols.items():
                for symbol in symbol_list:
                    nodes.append((symbol, {"type": symbol_type}))
                    edges.append((node_id, symbol, {"type": "contains"}))

            for line in text.splitlines():
                line = line.strip()
                if ":" not in line:
                    continue

                key_raw, val_raw = [
                    part.strip() for part in line.split(":", 1)
                ]

                if not key_raw or not val_raw:
                    continue

                key_tokens = self.tokenizer.tokenize(key_raw)
                val_tokens = self.tokenizer.tokenize(val_raw, False)

                key_id = self.symbol_generator.max_gram(key_tokens)
                val_id = self.symbol_generator.max_gram(val_tokens)

                nodes.append((key_id, {"text": key_raw, "is_key": True}))
                nodes.append((val_id, {"text": val_raw, "is_val": True}))

                edges.append((key_id, val_id, {"type": "key_value"}))
                edges.append((node_id, key_id, {"type": "contains"}))
                edges.append((node_id, val_id, {"type": "describes"}))

        elif isinstance(element, TableModel):

            node_id = element.caption_ref_id or element.id

            caption_elem = document.get_element_by_id(
                element.caption_ref_id
            )

            table_caption = (
                [caption_elem.to_text()] if caption_elem else []
            )

            text = element.to_html()

            heading_path = (
                document._get_heading_path(element)
                + table_caption
            )

            metadata = {
                "index": IndexType.TABLE,
                "heading_path": heading_path,
                "filename": document.filename,
                "page": element.page,
            }

            nodes.append(
                (
                    node_id,
                    {
                        "text": text,
                        "metadata": metadata,
                        "type": "table",
                    },
                )
            )

        return nodes, edges

    def index_document(
        self,
        document: DocumentModel,
        progress: Optional[ProgressCallback] = None,
    ) -> GraphModel:
        """Index all document elements into the graph.

        ``progress`` receives ``(done_units, total_units)`` updates during
        execution. Exceptions raised by the callback abort indexing.
        """

        start_time = time.time()
        elements = list(document.iter_elements())

        logger.info(f"Starting indexing for {len(elements)} elements")

        all_nodes = []
        all_edges = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:

            futures = []

            for element in elements:

                if isinstance(element, ParagraphModel):

                    futures.append(
                        executor.submit(
                            self._process_element,
                            document,
                            element,
                        )
                    )

                elif isinstance(element, TableModel):

                    futures.append(
                        executor.submit(
                            self._process_element,
                            document,
                            element,
                        )
                    )

                    node_id = element.caption_ref_id or element.id

                    caption_elem = document.get_element_by_id(
                        element.caption_ref_id
                    )

                    table_caption = (
                        [caption_elem.to_text()] if caption_elem else []
                    )

                    heading_path = (
                        document._get_heading_path(element)
                        + table_caption
                    )

                    header_cache = self._prepare_table_headers(
                        document,
                        element,
                        heading_path,
                    )

                    for row_idx, _ in enumerate(element.rows):
                        futures.append(
                            executor.submit(
                                self._process_table_row,
                                element,
                                node_id,
                                row_idx,
                                header_cache,
                            )
                        )

            total = len(futures)
            if progress is not None:
                progress(0, total)

            done = 0
            try:
                for future in tqdm(
                    as_completed(futures),
                    total=total,
                    desc="Indexing tasks",
                    unit="task",
                ):
                    result = future.result()
                    done += 1

                    if result:
                        nodes, edges = result
                        all_nodes.extend(nodes)
                        all_edges.extend(edges)

                    if progress is not None:
                        progress(done, total)
            except BaseException:
                for pending in futures:
                    pending.cancel()
                raise

        logger.info(
            f"Collected {len(all_nodes)} nodes and {len(all_edges)} edges"
        )

        insert_start = time.time()

        self.gm.graph.add_nodes_from(all_nodes)
        self.gm.graph.add_edges_from(all_edges)

        logger.info(
            f"Graph population completed in "
            f"{round(time.time() - insert_start, 2)}s"
        )

        with sqlite_conn() as conn:
            self.gm.save(conn)

        total_time = round(time.time() - start_time, 2)
        logger.info(f"Indexing completed in {total_time}s")

        self.gm.clear()
        return self.gm