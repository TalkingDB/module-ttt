# TTT vs. Conventional Chunking Strategies

[Docs home](README.md) › TTT vs. chunking

This document provides a comparative analysis of how TTT's structural graph indexing compares to conventional text chunking strategies used in vector-based Retrieval-Augmented Generation ([RAG](https://en.wikipedia.org/wiki/Retrieval-augmented_generation)).

---

## 1. Chunking Strategies Comparison

| Chunking Strategy | How It Works | Relationship to TTT |
|---|---|---|
| [Fixed-size chunking](https://www.pinecone.io/learn/chunking-strategies/) | Splits text at fixed token or character intervals, often with overlapping windows. | **Different.** Fixed chunking breaks sentences and severs table rows. TTT preserves semantic element boundaries (paragraphs, rows, cells). |
| [Recursive chunking](https://weaviate.io/blog/chunking-strategies-for-rag) | Splits iteratively using separators such as double newlines, single newlines and spaces. | **Partial overlap.** Recursive chunking splits text on delimiters but lacks graph relations and section ancestry. |
| [Structure-aware chunking](https://weaviate.io/blog/chunking-strategies-for-rag) | Respects document markup (headings, paragraphs, tables, lists). | **Closest to TTT.** TTT preserves section hierarchy and isolates tables, rows and cells as searchable nodes. |
| [Semantic chunking](https://www.pinecone.io/learn/chunking-strategies/) | Computes vector [embeddings](https://en.wikipedia.org/wiki/Word_embedding) across sentences and splits when similarity falls below a threshold. | **Not used.** TTT relies on structural document boundaries rather than sliding similarity thresholds. |
| [Parent-child chunking](https://weaviate.io/blog/chunking-strategies-for-rag) | Indexes small child chunks for retrieval while returning larger parent context. | **Supported via graph.** TTT maintains explicit `part_of` edges from cells to rows, rows to tables, and paragraphs to section headings. |
| [Contextual / LLM chunking](https://www.pinecone.io/learn/chunking-strategies/) | Prompts an [LLM](https://en.wikipedia.org/wiki/Large_language_model) to prepend document summary or situational context to each chunk. | **Not used during ingestion.** TTT captures deterministic structural context (heading path, page, table headers) without LLM overhead. |
| **TTT Symbolic Graph Indexing** | Parses elements, builds a [NetworkX](https://networkx.org/documentation/stable/tutorial.html) directed graph, extracts [lemmatized](https://en.wikipedia.org/wiki/Lemmatisation) [n-grams](https://en.wikipedia.org/wiki/N-gram), and scores with weighted [IDF](https://scikit-learn.org/stable/modules/feature_extraction.html#tfidf-term-weighting). | **The TTT Approach.** Provides deterministic retrieval with full provenance (filename, page number, heading path, row and column coordinates). |

---

## 2. Fundamental Advantages of TTT

1. **No Hallucination in Retrieval:** Vector similarity models struggle when multiple clauses look semantically similar. TTT uses exact lemmatized n-grams (`limitation_ask_microsoft`, `10_2025_01`), retrieving the exact ground truth element.
2. **Preserves Complete Provenance:** Every retrieved element returns its exact `page`, `filename`, and hierarchical `heading_path`, enabling verified citations in customer chat UIs.
3. **Structured Table Integrity:** Table rows and cells remain connected to their column headers, eliminating the severed-table problem common to text chunking.
4. **Deterministic and Auditable:** Results and scores can be mathematically reproduced, inspected, and debugged via graph inspection tools (`GET /v1/tree/json`).

---

**Related:** [Concepts: provenance](concepts.md#provenance) · [Symbolic indexing](symbolic-indexing.md) · [talkingdb-benchmarks](https://github.com/TalkingDB/talkingdb-benchmarks)
