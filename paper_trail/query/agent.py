import os
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from paper_trail.ingest.embedder import Embedder, get_embedder
from paper_trail.models import Answer
from paper_trail.query.retriever import retrieve
from paper_trail.store.lance import Store

DEFAULT_MODEL = os.getenv("PAPER_TRAIL_MODEL", "anthropic:claude-sonnet-4-5")

SYSTEM_PROMPT = """You are a research assistant with access to a library of academic papers.

Workflow for every question:
1. Call the search_papers tool one or more times to gather relevant passages.
2. Synthesize an answer ONLY from those passages. Do not use outside knowledge.
3. In `text`, write the answer with inline markers like [1], [2] referring to entries
   in `citations`. Place markers immediately after the claim they support.
4. In `citations`, populate one Citation per cited passage in the same order as the
   markers. Copy paper_id, paper_title, section, and page_number verbatim from the
   search results. Set relevant_text to a short verbatim quote from the passage you
   relied on (one sentence is enough).
5. If the retrieved passages don't contain enough information to answer, say so in
   `text` and return an empty `citations` list. Do not fabricate.
"""


@dataclass
class Deps:
    store: Store
    embedder: Embedder


def build_agent(model: str = DEFAULT_MODEL) -> Agent[Deps, Answer]:
    agent = Agent(
        model,
        deps_type=Deps,
        output_type=Answer,
        system_prompt=SYSTEM_PROMPT,
    )

    @agent.tool
    def search_papers(ctx: RunContext[Deps], query: str, top_k: int = 5) -> str:
        hits = retrieve(query, ctx.deps.embedder, ctx.deps.store, top_k=top_k)
        if not hits:
            return "No relevant passages found."
        rendered = []
        for h in hits:
            rendered.append(
                "paper_id: {pid}\n"
                "paper_title: {title}\n"
                "section: {section}\n"
                "page_number: {page}\n"
                "passage:\n{text}".format(
                    pid=h.get("paper_id", ""),
                    title=h.get("paper_title", "Unknown"),
                    section=h.get("section", "?"),
                    page=h.get("page_number", "?"),
                    text=h.get("text", ""),
                )
            )
        return "\n\n---\n\n".join(rendered)

    return agent


def answer(question: str, model: str = DEFAULT_MODEL) -> Answer:
    embedder = get_embedder()
    store = Store(vector_size=embedder.dim)
    agent = build_agent(model)
    result = agent.run_sync(question, deps=Deps(store=store, embedder=embedder))
    return result.output
