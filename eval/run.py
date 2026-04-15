"""Eval harness for paper-trail.

Loads a QA set (JSON), runs each question through the retriever and the agent,
and prints retrieval + citation accuracy. Writes raw results to a JSON file.

Usage:
    python -m eval.run --qa eval/qa_set.example.json --top-k 5 --out eval/results.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from paper_trail.ingest.embedder import get_embedder
from paper_trail.query.agent import answer
from paper_trail.query.retriever import retrieve
from paper_trail.store.lance import Store

console = Console()


def _matches_any(haystack: str, needles: list[str]) -> bool:
    h = haystack.lower()
    return any(n.lower() in h for n in needles)


def _eval_question(
    q: dict,
    embedder,
    store: Store,
    top_k: int,
    run_agent: bool,
) -> dict:
    expected = q.get("expected_paper_keywords", []) or []
    expect_no_answer = bool(q.get("expect_no_answer", False))

    hits = retrieve(q["question"], embedder, store, top_k=top_k)
    retrieved_titles = [h.get("paper_title", "") for h in hits]
    retrieval_hit = (
        any(_matches_any(t, expected) for t in retrieved_titles) if expected else None
    )

    citation_hit = None
    answer_text = None
    cited_titles: list[str] = []
    refused = None

    if run_agent:
        ans = answer(q["question"])
        answer_text = ans.text
        cited_titles = [c.paper_title for c in ans.citations]
        if expect_no_answer:
            refused = len(ans.citations) == 0
        elif expected:
            citation_hit = any(_matches_any(t, expected) for t in cited_titles)

    return {
        "id": q["id"],
        "question": q["question"],
        "expected_paper_keywords": expected,
        "retrieved_titles": retrieved_titles,
        "retrieval_hit": retrieval_hit,
        "answer_text": answer_text,
        "cited_titles": cited_titles,
        "citation_hit": citation_hit,
        "refused": refused,
    }


def _aggregate(results: list[dict]) -> dict:
    def pct(vals: list[bool]) -> float | None:
        vals = [v for v in vals if v is not None]
        return (sum(vals) / len(vals)) if vals else None

    return {
        "n": len(results),
        "retrieval_hit_rate": pct([r["retrieval_hit"] for r in results]),
        "citation_hit_rate": pct([r["citation_hit"] for r in results]),
        "refusal_rate_on_negatives": pct([r["refused"] for r in results]),
    }


def _render_table(results: list[dict]) -> None:
    table = Table(title="paper-trail eval", show_lines=False)
    table.add_column("id")
    table.add_column("question", overflow="fold", max_width=42)
    table.add_column("retrieval", justify="center")
    table.add_column("citation", justify="center")
    table.add_column("refused", justify="center")
    for r in results:
        table.add_row(
            r["id"],
            r["question"],
            _mark(r["retrieval_hit"]),
            _mark(r["citation_hit"]),
            _mark(r["refused"]),
        )
    console.print(table)


def _mark(v: bool | None) -> str:
    if v is None:
        return "[dim]-[/dim]"
    return "[green]y[/green]" if v else "[red]n[/red]"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa", default="eval/qa_set.example.json")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--out", default="eval/results.json")
    parser.add_argument(
        "--retrieval-only",
        action="store_true",
        help="Skip the agent run; report retrieval-only metrics.",
    )
    args = parser.parse_args()

    qa_path = Path(args.qa)
    if not qa_path.exists():
        console.print(f"[red]QA file not found: {qa_path}[/red]")
        sys.exit(1)
    qa = json.loads(qa_path.read_text())

    embedder = get_embedder()
    store = Store(vector_size=embedder.dim)

    results = []
    for q in qa["questions"]:
        console.print(f"[cyan]>[/cyan] {q['id']}: {q['question']}")
        result = _eval_question(
            q, embedder, store, top_k=args.top_k, run_agent=not args.retrieval_only
        )
        results.append(result)

    console.print()
    _render_table(results)
    console.print()
    summary = _aggregate(results)
    console.print(f"[bold]Summary[/bold]: {summary}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"summary": summary, "results": results}, indent=2))
    console.print(f"[dim]Wrote {out_path}[/dim]")


if __name__ == "__main__":
    main()
