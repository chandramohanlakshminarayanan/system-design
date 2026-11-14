---
inclusion: manual
name: LLM Wiki
description: How to build and maintain an LLM Wiki (Karpathy-style markdown knowledge base) in this workspace, and how to query it.
---

# LLM Wiki

A reusable workflow for turning source material (documents, PDFs, research,
notes) into a **plain-markdown knowledge base that an LLM can reason over**.
Based on Andrej Karpathy's "LLM wiki" idea: organize knowledge as structured
markdown files optimized for a model to read on your behalf, not for manual
browsing. Point the agent at the folder and ask questions; it reads the
relevant files and gives grounded answers drawn from your own knowledge.

Reference: <https://www.mindstudio.ai/blog/andrej-karpathy-llm-wiki-knowledge-base-claude-code>

## Core principles

- **Markdown only.** Every note is a `.md` file — portable, future-proof, and
  read natively by LLMs. No proprietary formats, no databases, no lock-in.
- **Written for the model, not for browsing.** You describe what you need in
  plain language; the agent finds and synthesizes across the whole wiki. Folder
  hierarchy and tags are hints, not navigation.
- **Consistent internal structure.** Every note starts with a title, a
  one-line summary, and tags, so the model can judge relevance fast without
  reading the whole file.
- **Focused notes.** Prefer many small, single-topic notes over one giant
  catch-all. The more specific each file, the more precisely it can be located
  and applied.
- **Cross-link.** Use `[[Note Title]]` links so related notes form a graph the
  model can traverse.
- **Ground answers in the wiki.** When querying, answer only from wiki content
  unless explicitly asked for general knowledge; if the wiki lacks the info, say
  so; cite the files used.

## Where the wiki lives

- The knowledge base lives in a top-level `llm-wiki/` folder in the workspace.
- Multiple wikis are allowed; name them `llm-wiki-<subject>/` if needed.
- Each wiki has an `index.md` at its root (the entry point / map of contents).

## Folder structure

Keep it simple. A typical wiki:

```
llm-wiki/
├── index.md          # entry point: what this wiki covers + map of notes
├── _templates/
│   └── note.md       # the note template below
├── <topic-folder>/   # broad topic folders (e.g. per source, per theme)
│   └── *.md          # focused notes
└── inbox/            # rough, unfiled notes to triage later
```

Do not over-engineer the hierarchy. Start with a few broad topic folders and
let it grow.

## Note template

Every note follows this shape. The summary + tags are the most important part —
they let the model decide relevance in one glance.

```markdown
# <Title>

**Summary**: One sentence describing this note.
**Tags**: #topic1 #topic2
**Source**: <where this came from — file, page range, URL>
**Created**: <ISO 8601 date>
**Last Updated**: <ISO 8601 date>

---

## Content

Main content in clear markdown: headers, lists, tables, code blocks.

## Related Notes

- [[Other Note Title]]
```

## Writing conventions

- **Summaries, not just content.** A good one-line summary at the top costs ten
  seconds and saves the model from reading irrelevant files.
- **Consistent terminology.** Pick one term per concept (e.g. "RAG" *or*
  "retrieval augmented generation") and add an alias line if a concept has
  multiple names.
- **Keep notes focused.** If a note covers multiple distinct topics, split it.
- **Cite sources.** Record the source document and page range so claims can be
  verified.
- **Preserve accuracy.** When summarizing a source, do not invent facts. If a
  source can't be read (e.g. a scanned/image PDF), say so explicitly in the note
  and mark clearly where content is a paraphrase or a knowledge-based summary
  rather than extracted text.

## Building a wiki from source documents

When asked to create an LLM Wiki from one or more documents:

1. **Inventory the source.** Determine what is extractable (embedded text,
   table of contents, headings) vs. not (scanned images). State the method used.
2. **Choose a decomposition.** One focused note per chapter / section / topic is
   the default. Avoid dumping a whole book into one file.
3. **Create the structure.** `index.md`, a topic folder per source (or per
   theme), and the `_templates/note.md`.
4. **Write each note** using the template: title, one-line summary, tags,
   source + page range, then a clear, focused summary of that section's content.
5. **Cross-link** related notes with `[[...]]` and list them under
   "Related Notes".
6. **Update `index.md`** with a short description of the wiki and a linked map
   of every note (grouped by topic/source), each with its one-line summary.

## Querying the wiki

When the user asks a question against the wiki:

- Read `index.md` first to locate candidate notes by their summaries/tags.
- Read only the relevant notes (use search to shortlist for large wikis).
- Answer strictly from wiki content unless asked otherwise; if it's not there,
  say so.
- Cite which notes the answer drew from.
- For small wikis (roughly under ~100K words), loading everything is fine and
  lets the model make cross-topic connections.

## Maintaining the wiki

- New rough material goes into `inbox/`; periodically triage it into the right
  topic folder with proper summary + tags.
- When updating a note, refresh its **Last Updated** date.
- Keep `index.md` in sync whenever notes are added, moved, or removed.
