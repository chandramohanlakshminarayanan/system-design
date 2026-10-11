# System Design Interview Trainer

A Microsoft Learn-style, deeply detailed study app covering **every chapter**
of the ByteByteGo *System Design Interview – An Insider's Guide*, **Volume 1**
(16 chapters) and **Volume 2** (13 chapters) — 29 chapters in total.

It teaches you to solve system design questions the way strong candidates do:
**clarify first, then design deeply**. Each chapter first walks you through the
right clarifying questions (ambiguity, scope, scale, constraints); once you've
worked through them you unlock a complete, end-to-end solution.

## What makes it different

- **Interactive clarify-then-solve flow.** Every chapter opens with the
  clarifying questions you should ask, each with *why it matters* and a
  reveal-able recommended assumption. The full solution stays gated until you
  choose to reveal it — mirroring a real interview.
- **Interview-grade depth.** Each solution covers:
  - Back-of-the-envelope **estimation** (QPS, storage, bandwidth, memory) with
    the actual arithmetic
  - **API design** and **data model** with storage-choice rationale
  - **High-level design** and request flows
  - **Deep dives** on scalability, **cost efficiency**, reliability/availability
    and **security**
  - Explicit **trade-off tables**, **bottlenecks & how to scale further**, and a
    **wrap-up**
- **Microsoft Learn-style UI.** Left table-of-contents tree, a clean reading
  column, a sticky "On this page" outline, breadcrumbs, unit-style section
  headings, callouts, completion tracking and prev/next navigation.
- **Clean professional diagrams.** One Azure-architecture-style SVG per chapter
  (crisp rounded cards, subtle shadows, tidy connectors), downloadable as SVG.

## Project layout

```
sysdesign_app/
├── app.py             # Microsoft Learn-style Streamlit UI + clarify/solve flow
├── schema.py          # Rich chapter data model (Chapter, ClarifyQ, Estimation, …)
├── registry.py        # Assembles all chapters and lookup/navigation helpers
├── content_v1.py      # Deep content for Volume 1 (16 chapters)
├── content_v2.py      # Deep content for Volume 2 (13 chapters)
├── diagrams.py        # One professional diagram per chapter (29 total)
├── diagram_engine.py  # Clean SVG diagram builder (nodes, edges, groups)
├── requirements.txt
└── README.md
```

## Run it

From inside the `sysdesign_app` folder:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the URL Streamlit prints (default http://localhost:8501).

## Using the trainer

1. Pick a chapter from the left table of contents (or the overview cards).
2. Read the **Overview** and study the architecture diagram.
3. Work through **Step 1 · Clarify** — try to answer each question yourself,
   then expand "Show recommended assumption" to compare.
4. Click **Reveal the full solution** to unlock requirements, estimation, API,
   data model, high-level design, deep dives, trade-offs, bottlenecks, security
   and the wrap-up.
5. Mark the chapter complete to track progress; use prev/next to move on.

## Chapters

**Volume 1 — Foundations & Classic Designs:** Scale to Millions of Users ·
Back-of-the-Envelope Estimation · Interview Framework · Rate Limiter ·
Consistent Hashing · Key-Value Store · Unique ID Generator · URL Shortener ·
Web Crawler · Notification System · News Feed · Chat System · Search
Autocomplete · YouTube · Google Drive · The Learning Continues.

**Volume 2 — Advanced Systems & Trade-offs:** Proximity Service · Nearby
Friends · Google Maps · Distributed Message Queue · Metrics Monitoring &
Alerting · Ad Click Event Aggregation · Hotel Reservation · Distributed Email ·
S3-like Object Storage · Real-time Gaming Leaderboard · Payment System ·
Digital Wallet · Stock Exchange.

## Notes

- Content is **original, paraphrased study material** written to interview
  depth — a learning companion, not a reproduction of the book's text.
- Diagrams are generated in pure Python as inline SVG (no browser or binary
  dependency), so they render instantly and export cleanly.
- Volume 1's chapter list comes from the book's own table of contents;
  Volume 2's from its published contents.

## Extending

- **Edit or add a chapter:** update the `CHAPTERS` list in `content_v1.py` or
  `content_v2.py` using the `Chapter` dataclass from `schema.py`. It appears in
  the UI automatically via `registry.py`.
- **Add a diagram:** define a builder in `diagrams.py` and register it in the
  `DIAGRAMS` map under the chapter's `diagram_id`. Chapters without a bespoke
  diagram fall back to a generic three-tier sketch.
