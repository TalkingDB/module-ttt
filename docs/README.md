# TTT documentation

Everything about Text-to-Tree beyond the [README](../README.md), in one place. Pick the path that fits what you want to do.

| If you are | Read in this order |
| :--- | :--- |
| New to TTT | [Concepts](concepts.md) › [the README's four steps](reference.md#run-it-in-four-steps) › [Retrieval and demonstrations](retrieval-and-demonstrations.md) |
| Building an app or agent on TTT | [API reference](api-reference.md) › [Fulfillment chat integration](fulfillment-chat-integration.md) › [sdk-talkingdb](https://github.com/TalkingDB/sdk-talkingdb) |
| Tuning or debugging results | [Symbolic indexing](symbolic-indexing.md) › [Table extraction](table-extraction.md) › [Troubleshooting](troubleshooting.md) |
| Comparing TTT with other [RAG](https://en.wikipedia.org/wiki/Retrieval-augmented_generation) approaches | [TTT vs. chunking](chunking-comparison.md) › [talkingdb-benchmarks](https://github.com/TalkingDB/talkingdb-benchmarks) |

## Every page

| Page | Kind | What it covers |
| :--- | :--- | :--- |
| [Concepts](concepts.md) | Understanding | Elements, the tree, symbols, contains and context links, scoring, jobs, provenance |
| [Ingestion pipeline](ingestion-pipeline.md) | Deep dive | Upload limits, the job queue, each stage from parsing to persisting |
| [Symbolic indexing](symbolic-indexing.md) | Deep dive | [Tokenizing](https://spacy.io/usage/linguistic-features#tokenization), [lemmatizing](https://en.wikipedia.org/wiki/Lemmatisation), [n-gram](https://en.wikipedia.org/wiki/N-gram) symbols, graph shape, the scoring formula |
| [Table extraction](table-extraction.md) | Deep dive | Tables as table, row and cell nodes; querying a single cell |
| [Retrieval and demonstrations](retrieval-and-demonstrations.md) | Example | A real query and response; optional [LLM](https://en.wikipedia.org/wiki/Large_language_model) summary |
| [Fulfillment chat integration](fulfillment-chat-integration.md) | How to | Using TTT from a chat app or agent; document collections |
| [TTT vs. chunking](chunking-comparison.md) | Understanding | Fixed, recursive, semantic and parent child chunking compared with TTT |
| [API reference](api-reference.md) | Reference | Every route, how to get an API key, query fields |
| [Troubleshooting](troubleshooting.md) | Fixing | Startup, auth, uploads, stuck jobs, empty results, lost data |
| [Diagram sources](diagrams/README.md) | Maintaining | How to edit and re-render the diagrams on these pages |

## Pictures in these docs

Screenshots in [`assets/readme/`](../assets/readme/) come from real runs of the service. Diagrams are drawn from the [Mermaid](https://mermaid.js.org/intro/) sources in [`diagrams/`](diagrams/) and committed as light and dark images, so they show on the web, in the GitHub mobile app and in editors.

Also: [Full reference](reference.md), everything that used to be on the front page.
