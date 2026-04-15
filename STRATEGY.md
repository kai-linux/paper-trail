# Strategy

How paper-trail wins attention, trust, and users.

## The core bet

**"RAG with receipts."** The category is crowded; the moat is *citation faithfulness*. Most RAG demos generate plausible answers and bolt citations on as decoration. paper-trail enforces citations as a hard constraint at the agent layer, surfaces them as clickable spans in the UI, and publishes a measurable citation-accuracy number in the README.

If we win on faithfulness, we win the audience that actually cares — researchers — and the audience that decides what gets shared — engineers who recognize a non-trivial RAG technique when they see one.

## Positioning vs alternatives

| Tool         | What it is                  | Where it loses to paper-trail                                  |
| ------------ | --------------------------- | -------------------------------------------------------------- |
| NotebookLM   | Cloud, Google-hosted        | Closed, no local corpus, no API, citations not span-level      |
| ChatPDF      | Per-document chat           | Single doc, no cross-paper synthesis, weak citations           |
| Elicit       | Research SaaS               | Paywalled, opinionated workflow, not hackable                  |
| Vanilla RAG  | LangChain demo notebooks    | No citation enforcement, no PDF-aware chunking, not a product  |

paper-trail's slot: **local-first, open-source, citation-enforced, PDF-native, hackable.**

## Three visibility bets, ranked

1. **MCP server** — the highest-leverage distribution play. Claude Desktop's MCP ecosystem is growing fast and under-served. Shipping a polished MCP server makes paper-trail the default "talk to my paper library" tool inside Claude Desktop, and lands us in `awesome-mcp-servers` lists.
2. **Eval numbers in the README** — publish retrieval precision@k and citation accuracy on a small QA set. Numbers travel further than screenshots in technical communities (HN, r/MachineLearning).
3. **A demo that shows the receipts** — terminal gif or web UI where a citation expands into the highlighted PDF span. The "oh, you can actually click it" moment is what gets shared.

## Differentiation we will defend

- **Section-aware chunking.** Academic PDFs aren't blog posts; respecting section boundaries, figure captions, and reference lists is a real problem and most tools punt on it.
- **Span-level citations.** Not "this paper somewhere" — `[Author, Title, p.12, §3.2]` with a clickable jump.
- **Configurable embedding provider.** voyage-3-large default for quality, OpenAI for cost, swap via env var. Respect user budget.
- **Local-first, runs offline (with local models).** Trust + privacy story for sensitive corpora.

## Distribution channels

- **MCP ecosystem** — `awesome-mcp-servers`, MCP server registries, Claude Desktop showcase
- **PydanticAI examples** — submit as a reference example; PydanticAI is hungry for substantial demos
- **Show HN** — lead with the eval numbers and the "RAG with receipts" framing
- **r/LocalLLaMA, r/MachineLearning** — the demo gif + repo link
- **Twitter/X** — thread with the click-through-to-PDF moment
- **Blog post** — *"Why your RAG is lying to you — enforcing citation faithfulness in PydanticAI"*, published on personal site, cross-posted to dev.to or Hashnode

## Anti-strategy: what we won't do

- **No multi-modal v1.** Figures and tables are a rabbit hole; the citation story is the moat. Ship monomodal first.
- **No knowledge-graph features.** Citation graphs are interesting but dilute the pitch.
- **No SaaS, no hosted version.** Local-first is a strategic position, not a limitation.
- **No premature abstractions.** No plugin systems, no provider-agnostic everything. Hard-code reasonable defaults; make them swappable only when a real second use case shows up.
- **No vibes-based marketing.** Every claim in the README is backed by a number or a runnable demo.

## How we'll know it's working

- GitHub stars on a steady upward slope (not a one-day spike that flatlines)
- Inbound issues and PRs from people who actually use it on their own corpus
- Citations of paper-trail in MCP server lists, RAG roundups, and "tools I use" posts
- At least one external blog post or video that uses paper-trail without prompting

## How we'll know to pivot

- Citation enforcement turns out to be cheap to copy and a competitor ships it within weeks → double down on the MCP + local-first angle, deprioritize citation as the headline
- Researchers don't want a CLI/local tool; they want a hosted UI → reconsider the no-SaaS stance
- MCP adoption stalls → fall back to the standalone CLI + web UI as the primary surface
