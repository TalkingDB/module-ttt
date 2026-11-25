# Symbolic Indexing & Graph Construction

TTT replaces opaque, lossy vector embeddings with **deterministic symbolic graph indexing**. This document explains the exact tokenization pipeline, n-gram weights, edge relationship types, and relevance scoring mathematics.

---

## 1. N-Gram Symbol Generation

A [noun phrase](https://dictionary.cambridge.org/grammar/british-grammar/noun-phrases) in grammar is a word or phrase naming a person, place, or concept (e.g., `network access policy`). While indexed terms frequently look like noun phrases, **TTT does not execute a grammatical noun phrase parser**.

Instead, TTT implements **adjacent word n-gram indexing** with [spaCy](https://spacy.io/usage/linguistic-features#tokenization) lemmatization:

```
"Network access policy controls customer authentication."
                           │
                           ▼
[1. Tokenization & Lemmatization] (app/services/package_text_tokenizer.py)
Tokens: ['network', 'access', 'policy', 'control', 'customer', 'authentication']
                           │
                           ▼
[2. N-Gram Symbol Generation] (app/services/package_symbol_generator.py)
```

| Symbol Type | Definition | Generated Example Symbols | Weight (`GRAM_WEIGHTS`) |
|---|---|---|---|
| [Unigram](https://developers.google.com/machine-learning/glossary#n-gram) | Single normalized token | `network`, `access`, `policy`, `control`, `customer`, `authentication` | `1.0` |
| [Bigram](https://developers.google.com/machine-learning/glossary#bigram) | Two adjacent tokens | `network_access`, `access_policy`, `policy_control`, `control_customer`, `customer_authentication` | `2.0` |
| [Trigram](https://developers.google.com/machine-learning/glossary#trigram) | Three adjacent tokens | `network_access_policy`, `access_policy_control`, `policy_control_customer`, `control_customer_authentication` | `3.0` |

---

## 2. Linguistic Processing Steps

- **[Tokenization](https://spacy.io/usage/linguistic-features#tokenization):** Lowercases text, strips punctuation, and segments sentences into discrete word tokens.
- **[Lemmatization](https://spacy.io/usage/linguistic-features#lemmatization):** Maps inflected word variants to base dictionary headwords (e.g., `policies` &rarr; `policy`, `controls` &rarr; `control`).
- **[Stop Words Filtering](https://spacy.io/usage/linguistic-features#language-data):** Removes common functional words (`the`, `is`, `with`, `and`, `of`) from prose sentences so only content-carrying words form symbols.
- **Structured Tokenizer (`tokenize_structured`):** Special tokenizer for tables that preserves slashes, hyphens, numbers, and dates (e.g., `10/2025/01` &rarr; `10_2025_01`), enabling exact cell retrieval.

---

## 3. Directed Graph Topology

TTT builds an in-memory [NetworkX](https://networkx.org/documentation/stable/tutorial.html) directed graph for each document, which is subsequently serialized to SQLite.

```mermaid
graph TD
    Root["file@root<br>(Ask-Microsoft-transparency-FAQ.pdf)"]
    H1["heading:1<br>(Ask Microsoft: Responsible AI FAQ)"]
    H2["heading:2<br>(What are the limitations...?)"]
    P5["paragraph:5<br>(The chatbot uses AI...)"]
    
    SymTri["symbol::trigram<br>(limitation_ask_microsoft)"]
    SymBi["symbol::bigram<br>(ask_microsoft)"]
    SymUni["symbol::unigram<br>(limitation)"]

    Root -->|part_of| H1
    H1 -->|part_of| H2
    H2 -->|part_of| P5

    SymTri -->|contains (weight: 3.0)| P5
    SymBi -->|contains (weight: 2.0)| P5
    SymUni -->|contains (weight: 1.0)| P5
```

### Node Types
- `file@root`: Document root node containing global metadata (filename, page count).
- `heading`: Structural section node (H1 to H6) containing section title and level.
- `paragraph`: Text body element containing text runs and page coordinates.
- `table`: Table container element.
- `table_row`: Row container preserving row header and sequence.
- `table_cell`: Cell container preserving column header, row header, and raw value.
- `symbol`: Lemmatized unigram, bigram, or trigram token node.

### Edge Relationship Types
- `part_of`: Structural hierarchy edge connecting child elements to parent sections (e.g., cell to row, row to table, paragraph to heading).
- `contains`: Directed index edge connecting a symbol to an element where the symbol occurs directly in the text (weight `1.0`).
- `context`: Directed index edge connecting a symbol to an element where the symbol occurs in surrounding table or section context (weight `CONTEXT_MATCH_WEIGHT = 0.4`).

![Symbolic indexing and graph connections](../assets/readme/symbolic-index.png)

---

## 4. Relevance Scoring & IDF Mathematics

When a query is received:
1. The query text is tokenized and lemmatized into query unigrams, bigrams, and trigrams.
2. TTT matches query symbols against symbol nodes in the document graph.
3. For each matched symbol, TTT traverses incoming edges to connected document elements.

The element relevance score is calculated as:

$$\text{Score}(e) = \sum_{s \in \text{MatchedSymbols}(e)} \text{GRAM\_WEIGHT}(s) \times \text{IDF}(s) \times \text{EDGE\_WEIGHT}(s, e)$$

Where:
- $\text{GRAM\_WEIGHT}$: `3.0` for trigrams, `2.0` for bigrams, `1.0` for unigrams.
- $\text{EDGE\_WEIGHT}$: `1.0` for direct `contains` edges; `0.4` for inherited `context` edges.
- $\text{IDF}$ (Inverse Document Frequency):
  $$\text{IDF}(s) = \ln\left(\frac{N}{\text{DF}(s)}\right)$$
  - $N$: Total number of elements in the document graph.
  - $\text{DF}(s)$: Number of elements containing symbol $s$.

Higher-order n-grams provide a deterministic multi-word phrase boost. Rare, distinctive terms receive higher IDF weights than generic terms.

---

## 5. Document Section Hierarchy Tree

Clients can retrieve the full hierarchical outline of a document via `GET /v1/tree/json?graph_id=YOUR_GRAPH_ID`:

![Document tree inspection](../assets/readme/document-tree.png)

The tree JSON preserves:
- Heading hierarchy (H1 &rarr; H2 &rarr; H3 &rarr; paragraphs).
- Provenance: File name, page number, and full `heading_path` breadcrumbs.
