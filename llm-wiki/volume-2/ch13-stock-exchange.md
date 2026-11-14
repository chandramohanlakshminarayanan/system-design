# Stock Exchange

**Summary**: Match buy/sell orders with ultra-low deterministic latency and strict fairness using a sequencer, an in-memory single-writer matching engine, and a log-before-match design.
**Tags**: #system-design #stock-exchange #matching-engine #order-book #sequencer #low-latency #volume-2
**Source**: System Design Volume 2.pdf — Chapter 13. NOTE: scanned/image PDF, not machine-readable — knowledge-based summary.
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

> ⚠️ Knowledge-based summary (source PDF not machine-readable).

Match orders against an order book with **price-time priority**, publish market
data, and never lose an order — at microsecond, deterministic latency.

- **Order gateway + sequencer** — orders enter via gateways and pass through a
  single **sequencer** that assigns a **total order**, guaranteeing **fairness**
  (strict arrival order) and **determinism** (replay reproduces the exact book).
- **Matching engine** — runs **in memory, single-writer per symbol** (no lock
  contention → predictable microsecond latency), matching by price-time
  priority. Partitioning by symbol scales throughput while preserving per-symbol
  ordering.
- **Order book** — in-memory bids (desc) and asks (asc, then by time); matching
  pops the best opposing price and fills by time priority.
- **Durability (log-before-match)** — every input is persisted to an append-only
  log **before** matching, so a crash loses nothing and the exact book is rebuilt
  by replay; hot standbys consume the same log for fast failover.
- **Market data publisher** — broadcasts trades and book deltas to subscribers.
- **Trade-off** — sacrifices raw throughput and cost for fairness, determinism,
  and speed (kernel-bypass networking, colocation, minimal GC).

## Related Notes

- [[Digital Wallet]]
- [[Payment System]]
