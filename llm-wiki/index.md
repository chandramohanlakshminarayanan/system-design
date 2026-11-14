# System Design LLM Wiki

**Summary**: An LLM-queryable markdown knowledge base covering the ByteByteGo "System Design Interview – An Insider's Guide", Volumes 1 & 2.
**Tags**: #index #system-design #bytebytego #interview
**Source**: System Design Volume 1.pdf (text-extractable) and System Design Volume 2.pdf (scanned images — Volume 2 notes are knowledge-based summaries).
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## What this wiki covers

Structured notes on all 29 chapters across both volumes. Each note follows the
[[note]] template: title, one-line summary, tags, source (with page range for
Volume 1), and a focused summary of the chapter's content, plus cross-links.

- **Volume 1** notes are grounded in the book's extractable text and table of
  contents (page ranges cited).
- **Volume 2** notes are **knowledge-based summaries** — the Volume 2 PDF is a
  scanned/image document with no machine-readable text, so those notes summarize
  the chapter topics rather than quoting the source. Each is marked accordingly.

## How to query

Point the agent at this `llm-wiki/` folder and ask in plain language, e.g.:
- "How does the book handle the celebrity problem in a news feed?"
- "Compare replication vs erasure coding for object storage."
- "What quorum setting gives strong consistency in the key-value store?"
- "Which chapters cover WebSockets, and how do they use them?"

The agent reads `index.md` to shortlist notes by summary/tags, then reads the
relevant notes and answers from wiki content, citing the notes used.

## Map of notes

### Volume 1 — Foundations & Classic Designs

1. [[Scale From Zero to Millions of Users]] — single server → distributed system, one bottleneck at a time.
2. [[Back-of-the-Envelope Estimation]] — powers of two, latency numbers, availability nines, QPS/storage sizing.
3. [[A Framework for System Design Interviews]] — the 4-step process (scope → high-level → deep dive → wrap up).
4. [[Design a Rate Limiter]] — token/leaking/sliding-window algorithms; distributed Redis counters; 429.
5. [[Design Consistent Hashing]] — hash ring + virtual nodes to minimize key remapping on membership change.
6. [[Design a Key-Value Store]] — Dynamo-style: consistent hashing, replication, quorum, vector clocks, gossip, Merkle trees.
7. [[Design a Unique ID Generator in Distributed Systems]] — Twitter Snowflake 64-bit layout.
8. [[Design a URL Shortener]] — base62 of a unique ID vs hashing; cache-heavy redirects; 301 vs 302.
9. [[Design a Web Crawler]] — URL frontier, BFS, politeness, dedup, traps, robustness.
10. [[Design a Notification System]] — push/SMS/email via queues, workers, retries, dedup.
11. [[Design a News Feed System]] — fan-out on write vs read, hybrid for celebrities, feed cache.
12. [[Design a Chat System]] — WebSockets, service discovery, KV message store, presence.
13. [[Design a Search Autocomplete System]] — trie with cached top-k; offline aggregation; sharding.
14. [[Design YouTube]] — upload → transcode (DAG) → blob storage → CDN adaptive streaming.
15. [[Design Google Drive]] — block-level delta sync, metadata DB, block servers, change notifications.
16. [[The Learning Continues]] — real-world systems and engineering blogs for further study.

### Volume 2 — Advanced Systems & Trade-offs (knowledge-based summaries)

1. [[Proximity Service]] — nearby search via geohash/quadtree spatial indexing, read-heavy.
2. [[Nearby Friends]] — real-time nearby friends via WebSockets + pub/sub + TTL location cache.
3. [[Google Maps]] — tiles (CDN), routing (contraction hierarchies), ETA (live traffic).
4. [[Distributed Message Queue]] — partitioned append-only log, replication (ISR), consumer groups + offsets.
5. [[Metrics Monitoring and Alerting System]] — pull collection, TSDB + downsampling, alert manager.
6. [[Ad Click Event Aggregation]] — stream + batch reconciliation over an immutable raw archive.
7. [[Hotel Reservation System]] — atomic inventory, optimistic concurrency, idempotent booking (no overselling).
8. [[Distributed Email Service]] — SMTP retry queue, metadata/blob split, async search index.
9. [[S3-like Object Storage]] — metadata vs data plane; replication vs erasure coding; immutable versions.
10. [[Real-time Gaming Leaderboard]] — Redis sorted set for O(log n) rank/top-N, durable DB source of truth.
11. [[Payment System]] — idempotency, double-entry ledger, PSP integration, reconciliation.
12. [[Digital Wallet]] — event sourcing + CQRS, per-wallet serialization, sagas for cross-partition transfers.
13. [[Stock Exchange]] — sequencer (fairness/determinism), in-memory single-writer matching, log-before-match.

## Structure

```
llm-wiki/
├── index.md            # this file
├── _templates/note.md  # note template
├── volume-1/           # 16 chapter notes (grounded in book text)
├── volume-2/           # 13 chapter notes (knowledge-based summaries)
└── inbox/              # rough, unfiled notes to triage
```
