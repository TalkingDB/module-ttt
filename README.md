<h1 align="center">Text-To-Tree (TTT)</h1>
<p align="center">
  <img src="assets/banner-img.png" alt="Module-TTT Banner" width="100%">
</p>
<p align="center">
  <img src="https://img.shields.io/github/stars/TalkingDB/module-ttt?style=flat-square&label=STARS&color=555" />
  <img src="https://img.shields.io/github/forks/TalkingDB/module-ttt?style=flat-square&label=FORKS&color=555" />
  <img src="https://img.shields.io/github/issues/TalkingDB/module-ttt?style=flat-square&label=ISSUES&color=dfb317" />
  <img src="https://img.shields.io/github/issues-pr/TalkingDB/module-ttt?style=flat-square&label=PULL%20REQUESTS&color=4c1" />
</p>

<p align="center">
  <img src="https://img.shields.io/github/last-commit/TalkingDB/module-ttt?style=flat-square&label=last%20commit&color=4c1" />
  <img src="https://img.shields.io/github/contributors/TalkingDB/module-ttt?style=flat-square&label=contributors&color=e05d44" />
  <img src="https://img.shields.io/codecov/c/github/Harshitraiii2005/module-ttt?style=flat-square&label=coverage&color=4c1" />
  <img src="https://img.shields.io/badge/language-Python-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/github/license/TalkingDB/module-ttt?style=flat-square&label=License&color=4c1" />
  <img src="https://img.shields.io/badge/release-v2.5.3-4c1?style=flat-square" />
    <img src="https://img.shields.io/badge/OS-linux%2C%20windows%2C%20macOS-2496ED?style=flat-square" />
  <img src="https://img.shields.io/badge/free%20for%20non--commercial%20use-4c1?style=flat-square" />
</p>
---
<h3 align="center">Vectorless, Search & Retrieval - at 1/10th token consumption</h3>

TTT navigates your document structure and retrieves only the sections needed to answer your query before invoking your LLM.

Every answer is grounded in the source document, using up to 90% fewer LLM tokens than conventional approaches.

---

## See the Difference

TTT was benchmarked against OpenAI's managed File Search implementation using GPT-4o across representative enterprise document types.

| **Document** | **Total Queries** | **Avg. Tokens / Query (OpenAI + Vector DB)** | **Avg. Tokens / Query (TTT)** | **Total Tokens Saved** | **Token Reduction** |
|:-------------|------------------:|---------------------------------------------:|------------------------------:|-----------------------:|--------------------:|
| [Microsoft FY2025 Annual Report](https://docs.google.com/document/d/1NRpcdd3_Ua5SM6UzX90w4UhAykgWw6TZ/edit?usp=sharing&ouid=115408291671450200196&rtpof=true&sd=true) | 27 | 17.38k | 850 | 446.26k | **95.11%** |
| [Apple FY2024 Annual Report](https://drive.google.com/file/d/1QuNqBrls1JUUKxOnMqxZh77niK_YJ0b_/view?usp=sharing) | 25 | 16.44k | 1,196 | 381.17k | **92.72%** |
| [OECD Economic Outlook](https://drive.google.com/file/d/1_edl_-zSCtnCpHXpQjc6LfA5UQiXo0ac/view?usp=drive_link) | 22 | 15.83k | 2,479 | 293.75k | **84.34%** |
| [WHO Health Equity Report](https://drive.google.com/file/d/1gDjypJsGdSrxV5lmBcz3e7Q5GLVEyOtm/view?usp=sharing) | 19 | 15.39k | 1,140 | 270.73k | **92.60%** |
| **Total** | **93** | **16.36k** | **1,388** | **1,392k** | **91.52%** |

<p align="center">
  <img src="assets/stats-image.png" alt="Module-TTT Banner" width="100%">
</p>

---

## See It in Action

**Experience a [document assistant chatbot](http://chat.talkingdb.io) powered with ❤️ using TTT.**

<p align="center">
  <img src="assets/demo-working.gif" alt="Module-TTT Banner" width="100%">
</p>

Upload your own document or explore one of our samples and ask questions naturally. Every answer is backed by our structure-aware retrieval engine that navigates your document before the LLM generates a response.

[chat.talkingdb.io](https://chat.talkingdb.io/)

---

## How TTT Thinks

<p align="center">
  <img src="assets/image1.png" alt="Module-TTT Banner" width="100%">
</p>

Conventional chunking strategies can split tables, lists, headings, and other related content across multiple chunks, losing document structure. During retrieval, this often returns multiple partially relevant chunks — increasing irrelevant context and LLM token consumption.

TTT powers retrieval differently. It transforms documents into a **Document Tree** that preserves their structural hierarchy and connects sections, subsections, tables, figures, and other elements. When a query arrives, TTT navigates this structure to retrieve only the relevant document sections before invoking the LLM.

The result is a **vectorless, structure-aware retrieval engine** that preserves document context, reduces unnecessary LLM input, and significantly lowers token consumption while maintaining accurate responses.

---

## Getting Started

Ready to build with TTT? Get the service running locally in minutes, explore the APIs, and submit your first document.

**Quick start:**

Pull and run the latest image:

```bash
docker run -it -p 8090:8090 talkingdb/ttt
```

Once the container is running:

- **API Base URL:** `http://localhost:8090`
- **Swagger Documentation:** `http://localhost:8090/docs`

[Try TalkingDB on Docker Hub](https://hub.docker.com/r/talkingdb/ttt) — Installation, Docker setup, Swagger UI, your first document upload, and first query.

---

## Documentation

Looking for more?

- **[Getting Started](https://docs.talkingdb.io/doc/quickstart-EHLtsm5kYD)** — Installation, configuration, and your first end-to-end query.
- **[API Reference](https://ttt-rc4.talkingdb.io/docs)** — Endpoints, request/response models, and examples.
- **[Architecture](https://docs.talkingdb.io/doc/ttt-level-1-architecture-Z6Uc3F1rzY)** — Document Tree construction, indexing, and retrieval internals.
- **[Deployment Guides](https://docs.talkingdb.io/doc/installation-hub-oWdyL8X4L3)** — Production deployment and infrastructure.

---

## Linked Repositories

TTT is one service inside the broader TalkingDB platform. It depends on, and works alongside, these repositories:

| **Repository** | **Role** |
|:---------------|:---------|
| [`base-tdb-models`](https://github.com/TalkingDB/base-tdb-models) | Shared Pydantic/data models used across all TalkingDB services (jobs, documents, metadata, API responses). |
| [`base-tdb-helpers`](https://github.com/TalkingDB/base-tdb-helpers) | Shared utility layer — storage clients, auth, graph helpers, validation. |
| [`base-tdb-clients`](https://github.com/TalkingDB/base-tdb-clients) | Thin client wrappers for external dependencies (SQLite) used throughout the platform. |
| [`package-content-elementizer`](https://github.com/TalkingDB/package-content-elementizer) | Parses raw documents (PDF, DOCX, and more) into structured elements — the first step in building a TTT tree. |
| [`infra-tdb-platform`](https://github.com/TalkingDB/infra-tdb-platform) | Infrastructure-as-code for the platform's cloud footprint — VMs, networking, DNS. |

---

## Contributing

Interested in contributing to TTT?

See the **[contributor guide](https://docs.talkingdb.io/doc/guides-ofg1QILxjP)** for local development, DevPod setup, and troubleshooting.

---

## Get in Touch

Looking to bring TTT into your own stack and cut down what you're spending on document search and retrieval? Talk to us. We'll help you figure out what that could look like for your team.

<p align="center">
  <a href="https://talkingdb.io/">
    <img src="https://img.shields.io/badge/talkingdb.io-4285F4?style=for-the-badge&logo=googlechrome&logoColor=white" alt="TalkingDB Website">
  </a>
  <a href="https://talkingdb.io/">
    <img src="https://img.shields.io/badge/Try%20TalkingDB-00C7B7?style=for-the-badge&logo=databricks&logoColor=white" alt="Try TalkingDB">
  </a>
  <a href="https://www.linkedin.com/company/talkingdb/about/">
    <img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn">
  </a>
  <a href="mailto:hello@talkingdb.io">
    <img src="https://img.shields.io/badge/Contact%20Us-4285F4?style=for-the-badge&logo=gmail&logoColor=white" alt="Contact Us">
  </a>
</p>
