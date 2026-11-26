# TTT Troubleshooting

[Docs home](README.md) › Troubleshooting

This guide covers common problems when running TTT locally with Docker and using its API.

## 1. The service does not start

Check that Docker is running:

```powershell
docker version
docker ps -a
```

Check the TTT container logs:

```powershell
docker logs -f talkingdb-ttt
```

If the container name is already in use, remove the old container and start it again:

```powershell
docker rm -f talkingdb-ttt
docker run -d --name talkingdb-ttt -p 8090:8090 -v ttt-data:/app/data talkingdb/ttt
```

If port `8090` is already in use, map another local port to the container's port `8090`:

```powershell
docker run -d --name talkingdb-ttt -p 8091:8090 -v ttt-data:/app/data talkingdb/ttt
```

Then open `http://localhost:8091/docs`.

## 2. The health endpoint or API documentation does not open

Open `http://localhost:8090/health` first. If it does not respond, check `docker ps` and `docker logs talkingdb-ttt`.

When health responds, open `http://localhost:8090/docs`. The interactive API page is served by the running TTT container.

## 3. An API request returns 401 Unauthorized

TTT uses two different credentials:

1. The access token returned by `POST /auth/login` is used to create an API key through `POST /auth/api-keys`.
2. The API key returned by `POST /auth/api-keys` is used for protected document and query endpoints.

In the Swagger **Authorize** dialog, enter the API key as the Bearer credential. Do not use the login access token for `POST /v1/documents` or `POST /v1/queries`.

## 4. The upload is rejected

Check the file type and size.

| Response | Meaning | What to check |
|---|---|---|
| `415 Unsupported Media Type` | Unsupported file extension | TTT currently accepts `.pdf` and `.docx` uploads |
| `413 File Too Large` | The file exceeds its configured size limit | Check `GET /v1/documents/constraints` and the file size settings |
| `429 Too Many Requests` | The ingestion queue is full | Wait and retry after the interval in the `Retry-After` response header |
| `503 Service Unavailable` | Local spool storage is low on disk space | Check free disk space and the configured spool directory |

The default upload limits in the current code are 100 MB for PDF and 50 MB for DOCX. Deployments can override these limits with environment variables.

## 5. The job stays queued, fails or does not complete

After uploading, use `GET /v1/jobs/{job_id}` to inspect the job. Check these fields:

| Field | What it tells you |
|---|---|
| `state` | Whether the job is queued, running, completed, cancelled or failed |
| `stage` | Which processing stage is active or failed |
| `status_message` | A short progress message |
| `error_code` | The failure category when the job fails |
| `error_message` | The user-facing failure explanation |

If a job fails, check the container logs for the corresponding job ID:

```powershell
docker logs talkingdb-ttt
```

Some transient parsing failures can be retried with `POST /v1/jobs/{job_id}/retry`. The API returns a conflict response when a job is not eligible for retry. Otherwise, upload the document again.

## 6. A query returns no useful matches

TTT currently retrieves content through normalized words and adjacent word groups. It does not infer every synonym or paraphrase.

Try a query using important terms that appear in the document. Include the subject, product name, section term or table heading rather than asking only a broad question. Confirm that the upload job reached `COMPLETED` and that the query uses its `result_graph_id`.

For table content, include specific column names, row labels, years or values when possible. The quality of table retrieval depends on whether the parser extracted the table structure correctly.

## 7. The query returns matches but no summary

Retrieval does not require an LLM. A generated summary does.

Set `summarize` to `true` in `POST /v1/queries` and configure an LLM provider and its required credentials in the service environment. If the LLM is not configured or summarization fails, TTT can still return the matched document elements and the summary may be `null`.

## 8. A graph cannot be found or viewed

Check that the document job completed successfully and use the exact `result_graph_id` returned by `GET /v1/jobs/{job_id}`.

Use the graph ID in:

```text
GET /v1/tree/json?graph_id=YOUR_GRAPH_ID
GET /index/html?graph_id=YOUR_GRAPH_ID
```

A missing or incorrect graph ID results in a not-found response.

## 9. Document data disappears after recreating the container

The graph database is stored in `data/graphs.db` inside the container. Start TTT with a named Docker volume mounted at `/app/data` so this data survives container replacement:

```powershell
docker run -d --name talkingdb-ttt -p 8090:8090 -v ttt-data:/app/data talkingdb/ttt
```

TTT can use MinIO for uploaded original-file storage when configured. The SQLite volume and MinIO storage serve different purposes.

## 10. Useful checks

```powershell
# Is the container running?
docker ps

# Read recent service logs
docker logs --tail 200 talkingdb-ttt

# Follow logs while uploading or querying
docker logs -f talkingdb-ttt

# Check the service health
Invoke-RestMethod http://localhost:8090/health
```

For endpoint details, use [the local API documentation](http://localhost:8090/docs) or the [hosted TTT API reference](https://ttt-rc4.talkingdb.io/docs).

---

**Related:** [API reference](api-reference.md) · [Ingestion pipeline](ingestion-pipeline.md) · [Concepts](concepts.md) · [infra-tdb-platform troubleshooting](https://github.com/TalkingDB/infra-tdb-platform/blob/main/docs/troubleshooting.md)
