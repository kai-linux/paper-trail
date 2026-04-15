import os
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from paper_trail.ingest.embedder import Embedder, get_embedder
from paper_trail.query.retriever import retrieve
from paper_trail.store.qdrant import Store

DEFAULT_MODEL = os.getenv("PAPER_TRAIL_MODEL", "anthropic:claude-sonnet-4-5")

SYSTEM_PROMPT = """You are a research assistant with access to a library of academic papers.

When answering questions:
1. Use the search_papers tool one or more times to find relevant passages.
2. Synthesize an answer ONLY from the retrieved passages.
3. ALWAYS cite your sources inline as [Title, p.X, §Section] after each claim.
4. If the retrieved passages don't contain enough information, say so explicitly.
5. Never fabricate citations or content not present in the retrieved chunks.
"""


@dataclass
class Deps:
    store: Store
    embedder: Embedder


def build_agent(model: str = DEFAULT_MODEL) -> Agent[Deps, str]:
    agent = Agent(model, deps_type=Deps, system_prompt=SYSTEM_PROMPT)

    @agent.tool
    def search_papers(ctx: RunContext[Deps], query: str, top_k: int = 5) -> str:
        hits = retrieve(query, ctx.deps.embedder, ctx.deps.store, top_k=top_k)
        if not hits:
            return "No relevant passages found."
        rendered = []
        for h in hits:
            rendered.append(
                f"[{h.get('paper_title', 'Unknown')}, p.{h.get('page_number', '?')}, §{h.get('section', '?')}]\n"
                f"{h.get('text', '')}"
            )
        return "\n\n---\n\n".join(rendered)

    return agent


def answer(question: str, model: str = DEFAULT_MODEL) -> str:
    embedder = get_embedder()
    store = Store(vector_size=embedder.dim)
    agent = build_agent(model)
    result = agent.run_sync(question, deps=Deps(store=store, embedder=embedder))
    return result.output
