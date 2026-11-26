# API reference

[Docs home](README.md) › API reference

Every route the TTT service serves, grouped by what it is for. A running service also serves interactive docs at `/docs` ([Swagger UI](https://swagger.io/tools/swagger-ui/)); a hosted copy is at [ttt-rc4.talkingdb.io/docs](https://ttt-rc4.talkingdb.io/docs). Python users can call all of this through [sdk-talkingdb](https://github.com/TalkingDB/sdk-talkingdb).

All `/v1/*` routes need `Authorization: Bearer <api key>`.

## Get an API key

```bash
# 1. Create an account (password: 8+ characters with an upper case letter, a lower case letter and a number)
curl -X POST http://localhost:8090/auth/signup -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "ChangeMe123"}'

# 2. Log in; the response has an access_token
curl -X POST http://localhost:8090/auth/login -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "ChangeMe123"}'

# 3. Turn the login token into a long lived API key
curl -X POST http://localhost:8090/auth/api-keys -H "Authorization: Bearer $ACCESS_TOKEN"
```

The last call returns `{"api_key": ..., "created_at": ...}`. Keep the key in an environment variable such as `TDB_API_KEY`.

## Routes

| Group | Method and path | What it does | More |
| :--- | :--- | :--- | :--- |
| Health | `GET` or `HEAD /health` | Is the service up | [Troubleshooting](troubleshooting.md) |
| Auth | `POST /auth/signup`, `POST /auth/login`, `POST /auth/api-keys` | Account, login token, API key | Above |
| Documents | `GET /v1/documents/constraints` | Accepted file types and size limits | [Ingestion](ingestion-pipeline.md) |
| Documents | `POST /v1/documents` | Upload a PDF or DOCX; returns a `job_id` (`202`) | [Ingestion](ingestion-pipeline.md) |
| Documents | `GET /v1/documents`, `DELETE /v1/documents/{job_id}` | List and delete your documents | |
| Documents | `GET /v1/documents/{graph_id}/file` | Fetch the original file | |
| Jobs | `GET /v1/jobs/{job_id}` | State, stage, percent, `result_graph_id` | [Ingestion](ingestion-pipeline.md#4-polling-job-progress) |
| Jobs | `POST /v1/jobs/{job_id}/cancel`, `POST /v1/jobs/{job_id}/retry` | Cancel or retry | [Concepts: jobs](concepts.md#jobs-from-upload-to-graph) |
| Queries | `POST /v1/queries` | Ranked passages for a question across one or more graphs | [Retrieval](retrieval-and-demonstrations.md) |
| Tree | `GET /v1/tree/json` | A document's heading outline as JSON | [Symbolic indexing](symbolic-indexing.md#5-document-section-hierarchy-tree) |
| Projects | `/v1/projects` and `/v1/projects/{project_id}/...` | Group documents, rename, logo, project tree | |
| Namespaces | `GET /v1/namespaces`, `GET /v1/namespaces/{namespace}/documents` | Shared collections of documents | |
| Public | `GET /public/namespaces`, `GET /public/namespaces/{namespace}/documents` | Public demo collections, no key needed | |
| Index | `POST /index/document/elements`, `GET /index/html` | Index already parsed elements; view a graph in the browser | [Symbolic indexing](symbolic-indexing.md) |

## Query request and response

`POST /v1/queries` takes:

| Field | Meaning |
| :--- | :--- |
| `graph_ids` | One or more `result_graph_id` values to search |
| `text` | The question |
| `max_results` | How many passages to return |
| `summarize` | `true` to add an [LLM](https://en.wikipedia.org/wiki/Large_language_model) written summary of the passages (needs an LLM configured) |

Each returned element has `id`, `graph_id`, `content`, `type` (`paragraph`, `table`, `table_row`, `table_cell`), `score`, `page`, and for table parts `row_header`, `col_header` and `table_id`. A real request and response are shown in [retrieval and demonstrations](retrieval-and-demonstrations.md).
