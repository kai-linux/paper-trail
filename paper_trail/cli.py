from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from paper_trail.ingest.chunker import chunk_blocks
from paper_trail.ingest.embedder import get_embedder
from paper_trail.ingest.pdf_parser import parse_pdf
from paper_trail.query.agent import answer
from paper_trail.store.lance import Store

console = Console()
EMBED_BATCH = 64


@click.group()
def main() -> None:
    """paper-trail: conversational Q&A over research papers, with citations."""


@main.command()
@click.argument("pdfs", nargs=-1, type=click.Path(exists=True, dir_okay=False, path_type=Path))
def ingest(pdfs: tuple[Path, ...]) -> None:
    """Ingest one or more PDF files."""
    if not pdfs:
        console.print("[yellow]No PDFs provided.[/yellow]")
        return
    embedder = get_embedder()
    store = Store(vector_size=embedder.dim)

    for pdf in pdfs:
        console.print(f"[cyan]Parsing[/cyan] {pdf.name}")
        paper, blocks = parse_pdf(pdf)
        chunks = chunk_blocks(paper.id, blocks)
        paper.num_chunks = len(chunks)
        console.print(f"  {len(blocks)} blocks -> {len(chunks)} chunks")

        if not chunks:
            console.print("[yellow]  No chunks produced; skipping.[/yellow]")
            continue

        console.print(f"[cyan]Embedding[/cyan] {len(chunks)} chunks ({embedder.model})")
        texts = [c.text for c in chunks]
        vecs: list[list[float]] = []
        for i in range(0, len(texts), EMBED_BATCH):
            vecs.extend(embedder.embed(texts[i : i + EMBED_BATCH]))

        console.print("[cyan]Upserting[/cyan] to LanceDB")
        store.upsert_chunks(chunks, vecs, paper)
        console.print(f"[green]done[/green] {paper.title} ({paper.num_pages}p, {paper.num_chunks} chunks)")


@main.command()
@click.argument("question", nargs=-1, required=True)
def query(question: tuple[str, ...]) -> None:
    """Ask a question across the ingested library."""
    q = " ".join(question)
    console.print(f"[cyan]?[/cyan] {q}\n")
    result = answer(q)
    console.print(result.text)
    if result.citations:
        console.print()
        console.rule("[dim]Sources[/dim]")
        for i, cite in enumerate(result.citations, start=1):
            console.print(
                f"[dim][{i}][/dim] [bold]{cite.paper_title}[/bold]"
                f" — p.{cite.page_number}, §{cite.section}"
            )
            if cite.relevant_text:
                console.print(f"    [dim]{cite.relevant_text!r}[/dim]")


@main.command(name="list")
def list_papers() -> None:
    """List ingested papers."""
    embedder = get_embedder()
    store = Store(vector_size=embedder.dim)
    papers = store.list_papers()
    if not papers:
        console.print("[yellow]No papers ingested yet.[/yellow]")
        return
    table = Table(title="Ingested papers")
    table.add_column("ID")
    table.add_column("Title")
    table.add_column("Authors")
    table.add_column("Pages", justify="right")
    table.add_column("Chunks", justify="right")
    for p in papers:
        authors = ", ".join(p.get("authors") or []) or "—"
        table.add_row(
            p["paper_id"][:8],
            p.get("title", "?"),
            authors,
            str(p.get("num_pages", "?")),
            str(p.get("num_chunks", "?")),
        )
    console.print(table)


@main.command()
@click.argument("paper_id")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt.")
def delete(paper_id: str, yes: bool) -> None:
    """Delete a paper (and its chunks) by id or id-prefix."""
    embedder = get_embedder()
    store = Store(vector_size=embedder.dim)
    paper = store.find_paper(paper_id)
    if not paper:
        console.print(f"[red]No paper found matching id prefix {paper_id!r}.[/red]")
        raise click.exceptions.Exit(1)
    console.print(f"Match: [bold]{paper['title']}[/bold] ({paper['paper_id']})")
    if not yes:
        click.confirm("Delete this paper and all its chunks?", abort=True)
    store.delete_paper(paper["paper_id"])
    console.print("[green]deleted[/green]")


if __name__ == "__main__":
    main()
