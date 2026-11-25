# Downstream Integration & Fulfillment Chat

This document details how external applications—such as conversational chatbots, enterprise agents, or search portals—integrate with TTT.

---

## 1. Fulfillment Chat Sequence Architecture

Fulfillment Chat demonstrates the recommended integration pattern connecting an external customer UI, TTT, and a conversational LLM:

```mermaid
sequenceDiagram
    autonumber
    actor User as Customer / User
    participant ChatApp as Fulfillment Chat
    participant TTT as TTT Service (module-ttt)
    participant SQLite as SQLite Graph DB
    participant LLM as Configured LLM (LiteLLM)

    User->>ChatApp: "What are the limitations of the assistant?"
    Note over ChatApp: Retrieves pre-indexed graph IDs<br>from collection manifest
    ChatApp->>TTT: POST /v1/queries {graph_ids, text, max_results: 3}
    TTT->>TTT: Tokenize query into n-grams (unigrams, bigrams, trigrams)
    TTT->>SQLite: Traverse symbol nodes & score connected elements
    SQLite-->>TTT: Return matching paragraphs, tables & scores
    TTT-->>ChatApp: Return ranked elements + metadata (page, filename, heading_path)
    ChatApp->>LLM: Send user prompt + exact retrieved excerpts
    LLM-->>ChatApp: Synthesize natural-language answer with citations
    ChatApp-->>User: Display answer with clickable source references
```

---

## 2. Component Responsibilities

| Component | Responsibility |
|---|---|
| **Fulfillment Chat** | Manages user interface, conversation session history, authentication, and orchestrates calls between TTT and the LLM. |
| **TTT (`module-ttt`)** | Ingests documents, maintains section trees, builds symbolic index graphs, and retrieves grounded evidence with relevance scores. |
| **Language Model (LLM)** | Synthesizes a natural-language answer based strictly on retrieved excerpts. (Does not perform document indexing or search). |
| **Document Collection** | Source policy documents, user guides, or manuals uploaded and pre-indexed as stable graph IDs. |

---

## 3. Managing Document Collections

Documents should be **uploaded and indexed once**. Ingestion returns a permanent `result_graph_id`. Applications store these graph IDs in a configuration file or collection manifest rather than uploading files on every user query.

### Static Collection Manifest Example
See [`examples/fulfillment-collection.json`](../examples/fulfillment-collection.json):

```json
{
  "collection_name": "Fulfillment Knowledge Base",
  "documents": [
    {
      "name": "Fulfillment & Dispatch Policy",
      "filename": "fulfillment-policy.pdf",
      "graph_id": "graph::e1b4a7d290c8413f9a7218d6e35c8b01"
    },
    {
      "name": "Customer Returns & Refund Terms",
      "filename": "returns-policy.pdf",
      "graph_id": "graph::b49c017d83fa461298e1f0a25698dd34"
    }
  ]
}
```

---

## 4. Multi-Graph Querying

Queries can span multiple document graphs in a single API call:

```bash
curl -X POST "http://localhost:8090/v1/queries" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "graph_ids": [
      "graph::e1b4a7d290c8413f9a7218d6e35c8b01",
      "graph::b49c017d83fa461298e1f0a25698dd34"
    ],
    "text": "What is the return window for damaged items?",
    "max_results": 5,
    "summarize": false
  }'
```
