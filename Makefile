.PHONY: install test demo-fetch demo-ingest demo eval clean lint

install:
	uv sync --extra dev

test:
	uv run pytest tests/ -q

lint:
	uv run ruff check paper_trail tests eval

demo-fetch:
	mkdir -p pdfs
	curl -L -o pdfs/attention.pdf      https://arxiv.org/pdf/1706.03762
	curl -L -o pdfs/rag.pdf            https://arxiv.org/pdf/2005.11401
	curl -L -o pdfs/raptor.pdf         https://arxiv.org/pdf/2401.18059
	curl -L -o pdfs/lost-middle.pdf    https://arxiv.org/pdf/2307.03172

demo-ingest:
	uv run paper-trail ingest pdfs/*.pdf

demo: demo-fetch demo-ingest
	@echo
	@echo "Library ready. Try:"
	@echo "  uv run paper-trail query \"how does RAPTOR's hierarchical clustering compare to vanilla RAG?\""

eval:
	uv run python -m eval.run --qa eval/qa_set.example.json

eval-retrieval:
	uv run python -m eval.run --qa eval/qa_set.example.json --retrieval-only

clean:
	rm -rf paper-trail-data eval/results.json
