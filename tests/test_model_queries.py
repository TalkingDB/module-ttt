"""Unit tests for the Pydantic models in app.model.queries."""

import pytest
from pydantic import ValidationError

from app.model.queries import MatchedNode, QueryRequest, QueryResponse


class TestQueryRequest:
    def test_valid_payload_with_default_max_results(self):
        req = QueryRequest(graph_ids=["g1"], text="hello")
        assert req.max_results == 10

    def test_empty_graph_ids_raises(self):
        with pytest.raises(ValidationError):
            QueryRequest(graph_ids=[], text="hello")

    def test_empty_text_raises(self):
        with pytest.raises(ValidationError):
            QueryRequest(graph_ids=["g1"], text="")

    def test_text_over_max_length_raises(self):
        with pytest.raises(ValidationError):
            QueryRequest(graph_ids=["g1"], text="x" * 10001)

    def test_max_results_below_range_raises(self):
        with pytest.raises(ValidationError):
            QueryRequest(graph_ids=["g1"], text="hello", max_results=0)

    def test_max_results_above_range_raises(self):
        with pytest.raises(ValidationError):
            QueryRequest(graph_ids=["g1"], text="hello", max_results=101)

    def test_max_results_boundary_values_pass(self):
        low = QueryRequest(graph_ids=["g1"], text="hello", max_results=1)
        high = QueryRequest(graph_ids=["g1"], text="hello", max_results=100)
        assert low.max_results == 1
        assert high.max_results == 100


class TestMatchedNode:
    def test_minimal_valid_payload(self):
        node = MatchedNode(id="n1", graph_id="g1", score=0.87)
        assert node.content is None
        assert node.row_header is None

    def test_missing_required_score_raises(self):
        with pytest.raises(ValidationError):
            MatchedNode(id="n1", graph_id="g1")

    def test_table_cell_fields(self):
        node = MatchedNode(
            id="n1",
            graph_id="g1",
            score=0.5,
            type="table_cell",
            row_header="Revenue",
            col_header="Q4",
            table_id="t1",
            page=12,
        )
        assert node.type == "table_cell"
        assert node.page == 12


class TestQueryResponse:
    def test_valid_payload_with_nested_nodes(self):
        node = MatchedNode(id="n1", graph_id="g1", score=0.9)
        resp = QueryResponse(
            query="revenue",
            graph_ids=["g1"],
            total_results=1,
            processing_time_ms=42,
            elements=[node],
            symbols=[],
        )
        assert resp.total_results == 1
        assert resp.elements[0].id == "n1"

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            QueryResponse(
                query="revenue",
                graph_ids=["g1"],
                total_results=1,
                elements=[],
                symbols=[],
            )
