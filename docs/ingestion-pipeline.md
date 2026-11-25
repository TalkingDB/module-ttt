# Document Ingestion & Background Queue

TTT processes documents asynchronously through a multi-stage background pipeline. This document details the upload constraints, worker queue configuration, and pipeline lifecycle stages.

---

## 1. Upload Constraints & Endpoints

Documents are submitted as `multipart/form-data` to the `/v1/documents` endpoint:

| Parameter | Type | Required | Description | Constraint |
|---|---|---|---|---|
| `file` | File Upload | Yes | Target document | `.pdf` (&le; 100 MB) or `.docx` (&le; 50 MB) |
| `namespace` | String | No | Tenancy partition | Default: `"default"` |

```bash
curl -X POST "http://localhost:8090/v1/documents" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@sample-document.pdf"
```

![Document upload endpoint](../assets/readme/document-upload.png)

### Response (`202 Accepted`)
```json
{
  "job_id": "job::8f2b3e4a-9c71-4a25-b83e-d901f4c3a12e",
  "state": "QUEUED",
  "status_message": "Document accepted for asynchronous indexing"
}
```

---

## 2. Queue Configuration & Concurrency

- **Queue Capacity:** The in-process ingestion queue allows up to **10 concurrent jobs** (`QUEUE_CAPACITY = 10` in `app/core/config.py`).
- **Rejection Behavior:** If the queue is saturated, `/v1/documents` returns `429 Too Many Requests`.
- **Worker Execution:** A dedicated worker background task (`app/services/jobs.py`) pulls jobs from the queue FIFO and processes each document through the 5 pipeline stages.

---

## 3. Pipeline Lifecycle Stages

Every document transitions sequentially through five deterministic processing stages:

```mermaid
flowchart LR
    A["QUEUED"] --> B["PARSING<br>(pdf2docx / layout)"]
    B --> C["EXTRACTION<br>(paragraphs & tables)"]
    C --> D["TREE_GEN<br>(heading outline)"]
    D --> E["INDEXING<br>(n-gram symbols)"]
    E --> F["PERSISTING<br>(SQLite graphs.db)"]
    F --> G["COMPLETED"]
```

1. **`PARSING`**:
   - For PDFs: Converts PDF pages to internal DOCX flow using `pdf2docx` or parses layout primitives.
   - For DOCX: Reads document element tree directly using python-docx.
2. **`EXTRACTION`**:
   - Invokes `package-content-elementizer` to extract headings, paragraphs, tables, rows, and cells.
   - Retains physical coordinates: page number, bounding layout, and reading order.
3. **`TREE_GEN`**:
   - Organizes sections and headings (H1 through H6) into a hierarchical outline tree (`FileIndexModel`).
   - Links paragraphs and tables to their immediate parent heading via directed `part_of` edges.
4. **`INDEXING`**:
   - Tokenizes and lemmatizes text into unigrams, bigrams, and trigrams using spaCy (`en_core_web_sm`).
   - Applies `tokenize_structured` to tables to preserve numerical codes, years, and reference IDs.
   - Computes document-wide inverse document frequency (IDF) weights.
5. **`PERSISTING`**:
   - Writes the constructed NetworkX directed graph into SQLite (`data/graphs.db`).
   - Generates a permanent `result_graph_id` (e.g. `graph::62405fb8028748d58e091228bdd86305`).

![Ingestion completed lifecycle](../assets/readme/ingestion-completed.png)

---

## 4. Polling Job Progress

Clients track progress by polling `GET /v1/jobs/{job_id}`:

```bash
curl -X GET "http://localhost:8090/v1/jobs/job::8f2b3e4a-9c71-4a25-b83e-d901f4c3a12e" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Completed Response (`200 OK`)
```json
{
  "job_id": "job::8f2b3e4a-9c71-4a25-b83e-d901f4c3a12e",
  "state": "COMPLETED",
  "stage": "PERSISTING",
  "status_message": "Document indexed",
  "result_graph_id": "graph::62405fb8028748d58e091228bdd86305",
  "summary": {
    "elements": 13,
    "tables": 0,
    "duration_ms": 74
  },
  "page_count": 1,
  "created_at": "2026-11-23T18:52:16.082Z",
  "updated_at": "2026-11-23T18:52:16.156Z"
}
```

---

## 5. Job Cancellation

An in-flight or queued job can be cancelled prior to completion:

```bash
curl -X POST "http://localhost:8090/v1/jobs/YOUR_JOB_ID/cancel" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

If the job is still queued or running, TTT halts processing and marks the state as `CANCELLED`.
