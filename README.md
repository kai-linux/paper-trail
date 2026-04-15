# paper-trail

Conversational Q&A over your research paper library, with citations that point back to the exact paper, page, and section.

Ingest PDFs → smart section-aware chunking → vector store → ask questions, get answers grounded in the source material.

## Stack

- **[PydanticAI](https://ai.pydantic.dev/)** — agent framework
- **[LanceDB](https://lancedb.com/)** — embedded vector store (no server, just a folder)
- **[Anthropic API](https://docs.anthropic.com/)** — LLM (Claude)
- **[PyMuPDF](https://pymupdf.readthedocs.io/)** — PDF parsing
- **[Voyage AI](https://www.voyageai.com/)** or OpenAI — embeddings (configurable)

## How it works

```
PDF
 └─► pdf_parser   extract text + detect sections (abstract, methods, …)
 └─► chunker      section-aware splits, ~500 tokens, 50-token overlap
 └─► embedder     voyage-3-large or text-embedding-3-small
 └─► lancedb      upsert with metadata (paper_id, section, page, chunk_index)

Question
 └─► embed → vector search → (optional rerank) → PydanticAI agent
 └─► answer with citations: [Author, Title, p.12, Section 3.2]
```

Every chunk stores `paper_id`, `page_number`, `section_name`, and `chunk_index`. The agent's system prompt enforces citations on every answer.

## Quickstart

> Status: scaffolding in progress. See [BUILD_SPEC.md](./BUILD_SPEC.md) for the full design.

```bash
# Install (creates a venv and installs from pyproject)
uv sync

# Configure keys (Anthropic + Voyage by default)
cp .env.example .env && $EDITOR .env

# Ingest one or more papers
paper-trail ingest path/to/paper.pdf

# Ask a question across the library
paper-trail query "what is the chunking strategy used in RAPTOR?"
```

LanceDB is embedded — no Docker, no server. The library lives in `./paper-trail-data/` (override via `PAPER_TRAIL_DB_PATH`).

## Project layout

```
paper_trail/
├── ingest/      pdf_parser, chunker, embedder
├── store/       LanceDB wrapper (embedded vector store)
├── query/       retriever + PydanticAI agent
├── models.py    Paper, Chunk, Citation
└── cli.py
```

## Roadmap

- Multi-modal: extract figures/tables, describe via vision model, embed descriptions
- Citation graph: "find related papers"
- MCP server: query your library from Claude Desktop
- Watch-folder ingest
- Export annotated bibliographies / lit-review drafts

## License

MIT — see [LICENSE](./LICENSE).
