# Text to Tree (TTT)

TTT is a TalkingDB service that turns PDF and DOCX files into structured document graphs. It keeps the document's section hierarchy and makes paragraphs, tables, rows and cells searchable through an API.

TTT is a **document processing and retrieval service**. It is not a general purpose database and is not intended to store or manage an application's primary business data.

## What TTT does

1. Accepts a PDF or DOCX file and starts a background job.
2. Parses the document into headings, paragraphs, tables, rows and cells.
3. Builds a tree that represents the document's section hierarchy.
4. Builds a graph of document elements and connects them to symbolic indexes.
5. Stores the graph and makes its content available through APIs.

A [graph](https://networkx.org/documentation/stable/tutorial.html) is made of **nodes** (the items) and **edges** (the connections between items). In TTT, nodes can represent headings, paragraphs, tables, table rows, table cells and searchable symbols.

## Key terms in plain English

| Term | Simple meaning | Learn more |
|---|---|---|
| Noun phrase | A group of words built around a noun, such as `network access policy` | [Cambridge explanation](https://dictionary.cambridge.org/grammar/british-grammar/noun-phrases) |
| Token and tokenization | A token is a piece of text. Tokenization splits text into those pieces, usually words in TTT | [spaCy explanation](https://spacy.io/usage/linguistic-features#tokenization) |
| Lemma and lemmatization | The base form of a word and the process of converting a word to that form | [spaCy explanation](https://spacy.io/usage/linguistic-features#lemmatization) |
| Stop word | A common word, such as `the` or `is`, that may be skipped when searching ordinary text | [spaCy language data](https://spacy.io/usage/linguistic-features#language-data) |
| N-gram | A sequence of nearby words. A unigram has one word, a bigram has two and a trigram has three | [Google explanation](https://developers.google.com/machine-learning/glossary#n-gram) |
| Symbolic index | TTT's searchable word groups linked to the document elements where they occur | [TTT symbol generator](https://github.com/TalkingDB/module-ttt/blob/main/app/services/package_symbol_generator.py) |
| IDF | A weighting idea that gives more importance to terms found in fewer document elements | [Simple IDF background](https://scikit-learn.org/stable/modules/feature_extraction.html#tfidf-term-weighting) |
| API endpoint | A URL an application calls to use a service | [FastAPI first steps](https://fastapi.tiangolo.com/tutorial/first-steps/) |
| Bearer token | A credential sent in the HTTP `Authorization` header | [FastAPI explanation](https://fastapi.tiangolo.com/tutorial/security/first-steps/) |
| Docker volume | Storage that remains available when a container is removed or replaced | [Docker explanation](https://docs.docker.com/engine/storage/volumes/) |
| LLM | A model that can understand and generate text | [IBM introduction](https://www.ibm.com/think/topics/large-language-models) |

## How symbolic indexing works

The indexed terms can look like [noun phrases](https://dictionary.cambridge.org/grammar/british-grammar/noun-phrases), such as `network access policy` or `customer account balance`. However, TTT does not run a grammatical noun phrase extractor. Instead, it creates searchable word groups from nearby words. This is called **n-gram indexing**. The steps are:

1. **Tokenization:** split text into smaller pieces called [tokens](https://developers.google.com/machine-learning/glossary#token). For this service, tokens are usually words. See [how spaCy tokenizes text](https://spacy.io/usage/linguistic-features#tokenization).
2. **Lemmatization:** convert words to their base form. For example, `connections` becomes `connection`. See [spaCy's explanation](https://spacy.io/usage/linguistic-features#lemmatization).
3. **Stop word filtering:** remove some very common words from ordinary prose, such as `the` and `is`. See [spaCy's explanation of stop words](https://spacy.io/usage/linguistic-features#language-data).
4. **N-gram generation:** create groups of one, two and three adjacent words. Read [Google's simple n-gram explanation](https://developers.google.com/machine-learning/glossary#n-gram).

For `network access policy`, TTT creates these symbols:

| Symbol type | Meaning | Example |
|---|---|---|
| [Unigram](https://developers.google.com/machine-learning/glossary#n-gram) | One word | `network`, `access`, `policy` |
| [Bigram](https://developers.google.com/machine-learning/glossary#bigram) | Two adjacent words | `network_access`, `access_policy` |
| [Trigram](https://developers.google.com/machine-learning/glossary#trigram) | Three adjacent words | `network_access_policy` |

A **symbolic index** is the set of generated symbols connected to the paragraph, table, row or cell where they occur. When a query arrives, TTT generates symbols from the query too, finds matching document elements and ranks the results. The rank uses an [inverse document frequency (IDF) style weight](https://scikit-learn.org/stable/modules/feature_extraction.html#tfidf-term-weighting): symbols that occur in fewer document elements receive more weight. This is an IDF based weighting step, not a full TF-IDF vectorization pipeline. TTT's exact scoring implementation is in the [extractor](https://github.com/TalkingDB/module-ttt/blob/main/app/services/extractor.py).

For tables, TTT indexes the full table, its rows and its cells. It keeps available row headers, column headers, page details and surrounding section or table context. Table indexing is implemented in the [indexer](https://github.com/TalkingDB/module-ttt/blob/main/app/services/indexer.py).

TTT can optionally send retrieved text to a configured [large language model (LLM)](https://www.ibm.com/think/topics/large-language-models) to produce a summary. The LLM is not required to parse, build or search the graph.

## What TTT is not

TTT is **not a database** for an application's customers, orders, products or other business records. It is a service that processes documents and retrieves relevant parts of them. It uses [SQLite](https://www.sqlite.org/whentouse.html) internally to persist graph and service data; that does not make TTT a general purpose database.

TTT is not a chatbot or an LLM. It does not independently hold a conversation or generate an answer by default. It retrieves document content. An application can pass that content to an LLM or use the optional summary feature.

TTT does not guarantee that every heading, table or extracted relationship is correct. Results depend on the source document and the quality of parsing.

## Start using TTT

You need [Docker](https://docs.docker.com/get-started/) to run the service. The steps below use the published TTT image.

### 1. Start TTT

```bash
docker pull talkingdb/ttt
docker run -d --name talkingdb-ttt -p 8090:8090 -v ttt-data:/app/data talkingdb/ttt
```

The [Docker volume](https://docs.docker.com/engine/storage/volumes/) named `ttt-data` keeps the local database files when the container is replaced.

### 2. Check the service

Open these links in your browser:

- [Health check](http://localhost:8090/health) to confirm the service is running.
- [Interactive API documentation](http://localhost:8090/docs) to make requests and inspect responses. FastAPI explains [how interactive API docs work](https://fastapi.tiangolo.com/tutorial/first-steps/#interactive-api-docs).

### 3. Create an account and API key

In the interactive API documentation, call these endpoints in order:

1. `POST /auth/signup` to create an account.
2. `POST /auth/login` to receive a login access token.
3. `POST /auth/api-keys` to create an API key. For this request, send the login token as a [Bearer token](https://fastapi.tiangolo.com/tutorial/security/first-steps/) using the **Authorize** control.

Copy the API key returned by the third request. Use this API key to authorize document and query requests. These protected endpoints expect the API key, not the login access token.

### 4. Upload a document

Call `POST /v1/documents` and upload a PDF or DOCX file. TTT returns a `job_id`, which identifies the background processing task. The upload request can finish while TTT continues processing the document.

### 5. Wait for processing to finish

Call `GET /v1/jobs/{job_id}` until the job state is `COMPLETED`. Copy the `result_graph_id` from the response. The graph ID identifies the searchable graph created for your document.

### 6. Search the document

Call `POST /v1/queries` with the graph ID and a question or search phrase:

```json
{
  "graph_ids": ["YOUR_GRAPH_ID"],
  "text": "What does the document say about network access policy?",
  "max_results": 10,
  "summarize": false
}
```

The response includes matching document elements and symbols. Set `summarize` to `true` only when an LLM provider is configured.

### 7. View the document graph

Open `http://localhost:8090/index/html?graph_id=YOUR_GRAPH_ID` to view the indexed graph.

## Main API endpoints

| Endpoint | Purpose |
|---|---|
| `POST /v1/documents` | Upload a PDF or DOCX for processing |
| `GET /v1/jobs/{job_id}` | Check processing status and get the graph ID |
| `POST /v1/queries` | Retrieve matching paragraphs and table content |
| `GET /v1/tree/json?graph_id={graph_id}` | Return the graph as JSON |
| `GET /index/html?graph_id={graph_id}` | View the graph |
| `GET /health` | Check service health |

An **API endpoint** is a URL where an application can call a service. See [FastAPI's first steps guide](https://fastapi.tiangolo.com/tutorial/first-steps/).

## Documentation and help

| Guide | Link |
|---|---|
| Quickstart | [TTT Quickstart](https://docs.talkingdb.io/doc/quickstart-EHLtsm5kYD) |
| API reference | [Interactive API documentation](https://ttt-rc4.talkingdb.io/docs) |
| Installation | [Deployment and installation guide](https://docs.talkingdb.io/doc/installation-hub-oWdyL8X4L3) |
| Troubleshooting | [TTT Troubleshooting](TROUBLESHOOTING.md) |

## Related components

TTT uses [package-content-elementizer](https://github.com/TalkingDB/package-content-elementizer) to parse documents. It also uses shared models, clients and helpers from [base-tdb-models](https://github.com/TalkingDB/base-tdb-models), [base-tdb-clients](https://github.com/TalkingDB/base-tdb-clients) and [base-tdb-helpers](https://github.com/TalkingDB/base-tdb-helpers).

For implementation details, see [symbol generation](https://github.com/TalkingDB/module-ttt/blob/main/app/services/package_symbol_generator.py), [text tokenization](https://github.com/TalkingDB/module-ttt/blob/main/app/services/package_text_tokenizer.py), [graph indexing](https://github.com/TalkingDB/module-ttt/blob/main/app/services/indexer.py) and [query retrieval](https://github.com/TalkingDB/module-ttt/blob/main/app/services/extractor.py).
