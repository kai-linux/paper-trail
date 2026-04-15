# Plan

Phased execution plan to take paper-trail from spec to launched OSS project. See [NORTH_STAR.md](./NORTH_STAR.md) for the goal and [STRATEGY.md](./STRATEGY.md) for the bets behind it.

## Phase 1 — Functional MVP — DONE

**Goal:** `paper-trail ingest *.pdf && paper-trail query "..."` returns answers with real citations.

Build order (per `BUILD_SPEC.md`):

1. ✓ `models.py` — Paper, Chunk, Citation, Answer
2. ✓ `ingest/pdf_parser.py` — PyMuPDF, regex + font-size heading detection
3. ✓ `ingest/chunker.py` — section-aware, ~500 tok, 50 tok overlap
4. ✓ `store/lance.py` — embedded LanceDB (chunks + papers tables)
5. ✓ `ingest/embedder.py` — voyage-3 default, OpenAI fallback (env-driven)
6. ✓ `query/retriever.py` — top-k search
7. ✓ `query/agent.py` — PydanticAI agent with structured `Answer` output
8. ✓ `cli.py` — `ingest`, `query`, `list`, `delete`
9. ⏳ Smoke test on 3–5 open-access papers — pending API keys

**Caveat:** end-to-end smoke test against real PDFs is gated on Anthropic + Voyage keys. Static review of all modules complete, chunker + parser + store unit tests passing.

## Phase 2 — Credibility — DONE (modulo a key-gated run)

- ✓ **Eval harness** (`eval/run.py`) — loads a JSON QA set, runs each question through the retriever and the agent, reports retrieval hit-rate + citation hit-rate + refusal rate on negative questions. Writes raw JSON for further analysis.
- ✓ **Sample QA set** (`eval/qa_set.example.json`) — 10 questions over the four well-known papers in `pdfs/README.md`, including a negative ("expected refusal") case.
- ✓ **Bootstrap**: `make demo` curls the four sample PDFs and ingests them. `make eval` runs the harness. `make test` runs unit tests.
- ✓ **Tests**: chunker + pdf_parser + LanceDB roundtrip unit tests (no API keys required).
- ~~Docker compose~~ — no longer needed; LanceDB is embedded.

**Caveat:** the eval harness is built and ready, but actually running it requires API keys + an ingested library. Once keys are in, `make demo && make eval` produces the numbers we want to publish.

## Phase 3 — Visibility surface

- **Web UI** (Quart + static HTML/Tailwind): chat panel left, PDF viewer right, citations clickable and jump to highlighted span. The "shareable moment" surface.
- **VHS-recorded terminal demo** in the README.
- **MCP server** wrapper exposing `search_papers` as an MCP tool, with Claude Desktop config snippet. Strategic distribution play.
- **PyPI release** + **GitHub Actions** (lint, test, build).
- GitHub topics: `rag`, `pydantic-ai`, `lancedb`, `mcp`, `research-papers`, `claude`.

## Phase 4 — Launch

- Blog post: *"Why your RAG is lying to you — enforcing citation faithfulness in PydanticAI."* Include eval numbers.
- Show HN + r/LocalLLaMA + r/MachineLearning, lead with the demo gif.
- Submit to `awesome-mcp-servers` and PydanticAI's example list.

## Out of scope for v1

Multi-modal figure extraction, citation graphs, watch-folder ingest, lit-review export. All listed as stretch in `BUILD_SPEC.md` — they dilute the "RAG with receipts" story. Land them post-launch if the repo gets traction.

## Tradeoff flagged

Phase 3's web UI is the single biggest effort/visibility item. Lighter alternative: skip the UI, lean entirely on the MCP server + slick terminal gif.
