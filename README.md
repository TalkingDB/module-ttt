# Text to Tree (TTT)

TTT is a TalkingDB service that turns PDF and DOCX documents into structured graphs that applications can search and inspect.

## What TTT does

1. Accepts a document and creates a background processing job.
2. Parses the document into structured elements such as headings, paragraphs and tables.
3. Builds a tree that represents the document's section hierarchy.
4. Builds a graph containing the document elements and symbolic indexes for words and phrases.
5. Stores the graph and makes its content available through query and visualization APIs.

When a query arrives, TTT uses symbolic matching and relevance scoring to find useful paragraphs and table content. It can optionally send those matches to a configured LLM to produce a summary.

## What TTT is not

TTT is not an LLM or a chatbot. It does not generate answers by itself.

TTT is not a vector database. Its current retrieval process uses tokenization, unigrams, bigrams, trigrams and IDF based scoring, not embeddings.

TTT is not a general purpose knowledge graph. It represents the structure and content extracted from documents. It does not discover or verify every real world relationship or fact.

## Run with Docker

```bash
docker pull talkingdb/ttt
docker run -p 8090:8090 talkingdb/ttt
```

Open the API documentation at [http://localhost:8090/docs](http://localhost:8090/docs).

The document and query APIs require an API key. Create an account with `POST /auth/signup`, log in with `POST /auth/login`, then create an API key with `POST /auth/api-keys`.

For deployment configuration, use [`.env.example`](.env.example). Configure persistent file storage when uploaded originals need to be retained. Configure an LLM provider only when generated summaries are needed.

## Main API endpoints

| Endpoint | Purpose |
|---|---|
| `POST /v1/documents` | Upload a PDF or DOCX document for processing |
| `GET /v1/jobs/{job_id}` | Check document processing status |
| `POST /v1/queries` | Retrieve relevant content from indexed documents |
| `GET /v1/tree/json?graph_id={graph_id}` | Get the document graph as JSON |
| `GET /index/html?graph_id={graph_id}` | View the document graph |
| `GET /health` | Check service health |

## Related repositories

TTT uses [package-content-elementizer](https://github.com/TalkingDB/package-content-elementizer) to parse documents and shared models, clients and helpers from [base-tdb-models](https://github.com/TalkingDB/base-tdb-models), [base-tdb-clients](https://github.com/TalkingDB/base-tdb-clients) and [base-tdb-helpers](https://github.com/TalkingDB/base-tdb-helpers).
