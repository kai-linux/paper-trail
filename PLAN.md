# Plan

Phased execution plan to take paper-trail from spec to launched OSS project. See [NORTH_STAR.md](./NORTH_STAR.md) for the goal and [STRATEGY.md](./STRATEGY.md) for the bets behind it.

## Phase 1 — Functional MVP

**Goal:** `paper-trail ingest *.pdf && paper-trail query "..."` returns answers with real citations.

Build order (per `BUILD_SPEC.md`):

1. `models.py` — Paper, Chunk, Citation
2. `ingest/pdf_parser.py` — PyMuPDF, section detection
3. `ingest/chunker.py` — section-aware, ~500 tok, 50 tok overlap
4. `store/qdrant.py` — collection + upsert + filtered search
5. `ingest/embedder.py` — voyage-3 default, OpenAI fallback (env-driven)
6. `query/retriever.py` — top-k search (rerank deferred)
7. `query/agent.py` — PydanticAI agent with citation-enforcing system prompt
8. `cli.py` — `ingest`, `query`, `list`
9. Smoke test on 3–5 open-access papers (arXiv)

**Done =** end-to-end happy path works on real PDFs and citations resolve to the correct page + section.

## Phase 2 — Credibility

- **Eval harness**: 10–20 question QA set over the sample corpus; publish retrieval precision@k and citation accuracy in the README. Numbers > vibes.
- **Sample corpus + bootstrap**: `make demo` ingests a curated set (Attention Is All You Need, RAG, RAPTOR, …); first-run experience is 60s.
- **Docker compose**: Qdrant + paper-trail, single `docker compose up`.
- **Tests**: parser/chunker/retriever unit tests + one e2e.

## Phase 3 — Visibility surface

- **Web UI** (Quart + static HTML/Tailwind): chat panel left, PDF viewer right, citations clickable and jump to highlighted span. The "shareable moment" surface.
- **VHS-recorded terminal demo** in the README.
- **MCP server** wrapper exposing `search_papers` as an MCP tool, with Claude Desktop config snippet. Strategic distribution play.
- **PyPI release** + **GitHub Actions** (lint, test, build).
- GitHub topics: `rag`, `pydantic-ai`, `qdrant`, `mcp`, `research-papers`, `claude`.

## Phase 4 — Launch

- Blog post: *"Why your RAG is lying to you — enforcing citation faithfulness in PydanticAI."*
- Show HN + r/LocalLLaMA + r/MachineLearning, lead with the demo gif.
- Submit to `awesome-mcp-servers` and PydanticAI's example list.

## Out of scope for v1

Multi-modal figure extraction, citation graphs, watch-folder ingest, lit-review export. All listed as stretch in `BUILD_SPEC.md` — they dilute the "RAG with receipts" story. Land them post-launch if the repo gets traction.

## Tradeoff flagged

Phase 3's web UI is the single biggest effort/visibility item. Lighter alternative: skip the UI, lean entirely on the MCP server + slick terminal gif.
