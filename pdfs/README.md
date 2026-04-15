# pdfs/

Drop PDFs here for local smoke testing. The folder is gitignored (only this README and `.gitkeep` are tracked), so nothing you put in here will be committed.

## Suggested smoke-test corpus

A handful of well-known open-access papers from arXiv:

- *Attention Is All You Need* — https://arxiv.org/pdf/1706.03762
- *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* — https://arxiv.org/pdf/2005.11401
- *RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval* — https://arxiv.org/pdf/2401.18059
- *Lost in the Middle: How Language Models Use Long Contexts* — https://arxiv.org/pdf/2307.03172

Quick download:

```bash
curl -L -o pdfs/attention.pdf      https://arxiv.org/pdf/1706.03762
curl -L -o pdfs/rag.pdf            https://arxiv.org/pdf/2005.11401
curl -L -o pdfs/raptor.pdf         https://arxiv.org/pdf/2401.18059
curl -L -o pdfs/lost-middle.pdf    https://arxiv.org/pdf/2307.03172
```

Then:

```bash
paper-trail ingest pdfs/*.pdf
paper-trail query "how does RAPTOR's hierarchical clustering compare to vanilla RAG?"
```
