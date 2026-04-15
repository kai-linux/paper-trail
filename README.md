# paper-trail

Conversational Q&A over your research paper library, with citations that point back to the exact paper, page, and section.

Ingest PDFs → smart section-aware chunking → vector store → ask questions, get answers grounded in the source material.

## Stack

- **[PydanticAI](https://ai.pydantic.dev/)** — agent framework
- **[Qdrant](https://qdrant.tech/)** — vector store
- **[Anthropic API](https://docs.anthropic.com/)** — LLM (Claude)
- **[PyMuPDF](https://pymupdf.readthedocs.io/)** — PDF parsing
- **[Voyage AI](https://www.voyageai.com/)** or OpenAI — embeddings (configurable)

## How it works

```
PDF
 └─► pdf_parser   extract text + detect sections (abstract, methods, …)
 └─► chunker      section-aware splits, ~500 tokens, 50-token overlap
 └─► embedder     voyage-3-large or text-embedding-3-small
 └─► qdrant       upsert with metadata (paper_id, section, page, chunk_index)

Question
 └─► embed → vector search → (optional rerank) → PydanticAI agent
 └─► answer with citations: [Author, Title, p.12, Section 3.2]
```

Every chunk stores `paper_id`, `page_number`, `section_name`, and `chunk_index`. The agent's system prompt enforces citations on every answer.

## Quickstart

> Status: scaffolding in progress. See [BUILD_SPEC.md](./BUILD_SPEC.md) for the full design.

```bash
# Run Qdrant locally
docker run -p 6333:6333 qdrant/qdrant

# Install
uv sync

# Ingest a paper
paper-trail ingest path/to/paper.pdf

# Ask a question
paper-trail query "what is the chunking strategy used in RAPTOR?"
```

## Project layout

```
paper_trail/
├── ingest/      pdf_parser, chunker, embedder
├── store/       qdrant client wrapper
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
