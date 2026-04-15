# Paper-Trail - Build Spec

## What it does

Ingest research papers (PDFs), chunk them intelligently (respecting sections, figures, citations), embed into Qdrant, and query conversationally. Returns answers with exact citations pointing back to paper + page + paragraph.

## Stack

PydanticAI + Qdrant + Anthropic API + PyMuPDF

## Architecture

```
paper-trail/
├── paper_trail/
│   ├── __init__.py
│   ├── ingest/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py      # PDF to structured sections
│   │   ├── chunker.py         # Smart chunking (section-aware)
│   │   └── embedder.py        # Text -> vectors via Anthropic/OpenAI
│   ├── store/
│   │   ├── __init__.py
│   │   └── qdrant.py          # Qdrant client wrapper
│   ├── query/
│   │   ├── __init__.py
│   │   ├── retriever.py       # Vector search + reranking
│   │   └── agent.py           # PydanticAI agent for conversational QA
│   ├── models.py              # Pydantic models (Paper, Chunk, Citation)
│   └── cli.py                 # CLI: ingest, query, list papers
├── examples/
│   ├── ingest_papers.py
│   └── query_demo.py
├── tests/
├── pyproject.toml
└── README.md
```

## Data flow

```
PDF upload
  -> pdf_parser.py: extract text, detect sections (abstract, intro, methods, etc.)
  -> chunker.py: split into chunks (~500 tokens), respect section boundaries
  -> embedder.py: generate embeddings (voyage-3 or text-embedding-3-small)
  -> qdrant.py: upsert vectors with metadata (paper_id, section, page, chunk_index)

Query
  -> embedder.py: embed the question
  -> retriever.py: vector search in Qdrant, top-k chunks
  -> (optional) reranker: cross-encoder reranking for precision
  -> agent.py: PydanticAI agent synthesizes answer from chunks
  -> response includes citations: [Paper Title, p.12, Section 3.2]
```

## Key design decisions

- **PDF parsing:** pymupdf (fitz) for text extraction, with fallback to marker or nougat for scanned/complex papers
- **Chunking strategy:** Section-aware recursive splitting. Don't break mid-sentence. Keep section headers attached to chunks. Overlap of ~50 tokens between chunks.
- **Embedding model:** `voyage-3-large` (best for retrieval) or `text-embedding-3-small` (cheaper, OpenAI). Make it configurable.
- **Qdrant:** Run locally via Docker (`docker run -p 6333:6333 qdrant/qdrant`) or use Qdrant Cloud for prod.
- **Citation format:** Every chunk stores `paper_id`, `page_number`, `section_name`, `chunk_index`. The agent's system prompt enforces citation in responses.
- **Collection strategy:** Single collection with `paper_id` payload filter for multi-paper queries.

## Pydantic models (core)

```python
class Paper(BaseModel):
    id: str                    # UUID
    title: str
    authors: list[str]
    filename: str
    ingested_at: datetime
    num_pages: int
    num_chunks: int

class Chunk(BaseModel):
    id: str                    # UUID
    paper_id: str
    text: str
    section: str               # "abstract", "introduction", "3.2 Methods"
    page_number: int
    chunk_index: int           # order within paper
    embedding: list[float] | None = None

class Citation(BaseModel):
    paper_id: str
    paper_title: str
    section: str
    page_number: int
    relevant_text: str         # the chunk snippet used
```

## Agent system prompt (sketch)

```
You are a research assistant with access to a library of academic papers.
When answering questions:
1. Use the search_papers tool to find relevant passages
2. Synthesize an answer from the retrieved context
3. ALWAYS cite your sources as [Author, Title, p.X, Section Y]
4. If the papers don't contain enough info, say so explicitly
5. Never fabricate citations or content not in the retrieved chunks
```

## Dependencies

```toml
dependencies = [
    "pydantic-ai>=0.2.0",
    "qdrant-client>=1.12.0",
    "pymupdf>=1.25.0",
    "anthropic>=0.40.0",
    "voyageai>=0.3.0",         # optional: voyage embeddings
    "rich>=13.0.0",
    "click>=8.0.0",
]
```

## Build order

1. **models.py** - Pydantic models for Paper, Chunk, Citation
2. **pdf_parser.py** - Extract structured text from PDFs (sections, pages)
3. **chunker.py** - Section-aware chunking with overlap
4. **qdrant.py** - Qdrant client: create collection, upsert, search
5. **embedder.py** - Embedding wrapper (configurable provider)
6. **retriever.py** - Search + optional reranking
7. **agent.py** - PydanticAI agent with search_papers tool
8. **cli.py** - `paper-trail ingest paper.pdf` / `paper-trail query "what is..."`
9. **Tests** - unit tests for parser, chunker, retriever
10. **README** - with usage examples and architecture diagram

## Stretch goals

- **Multi-modal:** Extract figures/tables from PDFs, describe them via vision model, embed the descriptions
- **Citation graph:** Track which papers cite which, enable "find related papers" queries
- **MCP server:** Expose paper-trail as an MCP server so Claude Desktop can query your paper library
- **Batch ingest:** Watch a folder, auto-ingest new PDFs
- **Export:** Generate annotated bibliographies or literature review drafts
