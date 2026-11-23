# Text to Tree (TTT)

TTT is a TalkingDB service that turns PDF and DOCX files into structured document graphs. It keeps the document's section hierarchy and makes paragraphs, tables and their contents searchable through an API.

## What TTT does

1. Accepts a document and starts a background job.
2. Parses the file into headings, paragraphs, tables, rows and cells.
3. Builds a tree that represents the document's sections and subsections.
4. Builds a graph of the document elements and adds symbolic indexes for searching.
5. Stores the graph and exposes APIs to retrieve and inspect its content.

### What is a symbolic index?

A [noun phrase](https://dictionary.cambridge.org/grammar/british-grammar/noun-phrases) is a word or group of words that names a person, thing or idea. Examples include **network access policy**, **customer account balance** and **data retention period**.

TTT uses symbols to make terms in a document searchable. It first splits text into tokens (usually words), converts words to their base form (lemmatization), and filters common words in ordinary prose. For example, `connections` can be normalized to `connection`. It then creates:

| Symbol type | Example from `network access policy` |
|---|---|
| Unigram | `network`, `access`, `policy` |
| Bigram | `network_access`, `access_policy` |
| Trigram | `network_access_policy` |

A **symbolic index** is the set of these normalized word symbols connected to the paragraph, table, row or cell where they appear. When a query is submitted, TTT normalizes the query in the same way and uses matching symbols to find relevant document elements.

These groups often overlap with noun phrases, but there is an important distinction: TTT does not currently identify grammatical noun phrases as complete linguistic units. It creates adjacent one, two and three word combinations. For example, the phrase `network access policy` produces the symbols shown above. TTT also applies a small set of domain-specific normalization rules. Read more about [lemmatization in spaCy](https://spacy.io/usage/linguistic-features#lemmatization).

For tables, TTT preserves numbers, years and labels during tokenization. It indexes the table, its rows and its cells, together with available row headers, column headers and document context.

When a query is submitted, TTT applies the same text normalization and ranks matching document elements using symbolic matches and relevance scoring. An LLM can optionally summarize the retrieved content when an LLM provider is configured.

See the implementation: [symbolic index generation](https://github.com/TalkingDB/module-ttt/blob/main/app/services/package_symbol_generator.py), [text tokenization](https://github.com/TalkingDB/module-ttt/blob/main/app/services/package_text_tokenizer.py), [graph indexing](https://github.com/TalkingDB/module-ttt/blob/main/app/services/indexer.py) and [retrieval](https://github.com/TalkingDB/module-ttt/blob/main/app/services/extractor.py).

## What TTT is not

TTT is **not a general-purpose database**. It is a document processing and retrieval service. It uses SQLite internally to store graph data and service records, but it is not intended to replace an application's database.

TTT is not a chatbot or an LLM. It prepares and retrieves document content. Answer generation is a separate step, and optional summarization uses a configured LLM.

TTT does not guarantee that every extracted table, heading or relationship is correct. The result depends on the quality of the source file and document parsing.

## Start using TTT

The quickest way to try TTT is with Docker.

### 1. Start the service

```bash
docker pull talkingdb/ttt
docker run -d --name talkingdb-ttt -p 8090:8090 -v ttt-data:/app/data talkingdb/ttt
```

The Docker volume keeps the SQLite graph data when the container is restarted or replaced.

### 2. Check that it is running

Open [http://localhost:8090/health](http://localhost:8090/health) to check service health. Open [http://localhost:8090/docs](http://localhost:8090/docs) to use the interactive API documentation.

### 3. Create an account and API key

Use the API documentation to call these endpoints in order:

1. `POST /auth/signup` to create an account.
2. `POST /auth/login` to get an access token.
3. `POST /auth/api-keys` to create an API key. Use the login access token as the Bearer token for this request.

Use the returned API key with the **Authorize** control in the API documentation for document and query requests. Protected TTT endpoints expect the API key, not the login access token.

### 4. Upload a document

Call `POST /v1/documents` with a PDF or DOCX file. The response contains a `job_id`. TTT processes the document in the background.

### 5. Wait for indexing to finish

Call `GET /v1/jobs/{job_id}` until the job state is `COMPLETED`. Copy the `result_graph_id` from the response.

### 6. Query the document

Call `POST /v1/queries` with the graph ID and a question or search phrase:

```json
{
  "graph_ids": ["YOUR_GRAPH_ID"],
  "text": "What does the document say about network access policy?",
  "max_results": 10,
  "summarize": false
}
```

The response contains matching document elements and symbols. Set `summarize` to `true` only when an LLM provider is configured.

### 7. View the graph

Open `http://localhost:8090/index/html?graph_id=YOUR_GRAPH_ID` to view the indexed document graph.

## Main API endpoints

| Endpoint | Purpose |
|---|---|
| `POST /v1/documents` | Upload a PDF or DOCX for indexing |
| `GET /v1/jobs/{job_id}` | Check ingestion progress and get the graph ID |
| `POST /v1/queries` | Retrieve matching paragraphs and table content |
| `GET /v1/tree/json?graph_id={graph_id}` | Get the graph as JSON |
| `GET /index/html?graph_id={graph_id}` | View the graph |
| `GET /health` | Check service health |

## Documentation

| Guide | Link |
|---|---|
| Quickstart | [TTT Quickstart](https://docs.talkingdb.io/doc/quickstart-EHLtsm5kYD) |
| API reference | [Interactive API documentation](https://ttt-rc4.talkingdb.io/docs) |
| Installation | [Deployment and installation guide](https://docs.talkingdb.io/doc/installation-hub-oWdyL8X4L3) |
| Troubleshooting | [TTT Troubleshooting](TROUBLESHOOTING.md) |

## Related components

TTT uses [package-content-elementizer](https://github.com/TalkingDB/package-content-elementizer) to parse documents and shared models, clients and helpers from [base-tdb-models](https://github.com/TalkingDB/base-tdb-models), [base-tdb-clients](https://github.com/TalkingDB/base-tdb-clients) and [base-tdb-helpers](https://github.com/TalkingDB/base-tdb-helpers).
