# Real-time Gaming Leaderboard

**Summary**: Rank millions of players and answer top-N and "my rank" instantly using a Redis sorted set backed by a durable database.
**Tags**: #system-design #leaderboard #redis #sorted-set #ranking #volume-2
**Source**: System Design Volume 2.pdf — Chapter 10. NOTE: scanned/image PDF, not machine-readable — knowledge-based summary.
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

> ⚠️ Knowledge-based summary (source PDF not machine-readable).

Maintain live scores and answer top-N and a player's rank without sorting
millions of rows per query.

- **Redis sorted set (ZSET)** — the core idea. `ZADD` updates a score in
  O(log n); `ZREVRANGE` returns top-N; `ZREVRANK` gives a player's rank; a range
  around the rank gives neighbors. Converts an O(n log n) sort-per-query into
  cheap logarithmic operations.
- **Score service** — on a score change, update the sorted set (fast queries)
  and persist the authoritative score to the **database** (source of truth).
  Validate scores **server-side** (anti-cheat) — never trust the client.
- **Durability / recovery** — the sorted set is a derived, in-memory view; rebuild
  it from the DB after a cache loss; the DB also supports periodic
  (daily/weekly) board resets.
- **Scaling** — at 100M+ players a single set may not fit; **shard by score
  range**; global top-N merges shard tops and global rank sums per-shard counts.

## Related Notes

- [[Payment System]]
- [[Distributed Message Queue]]
