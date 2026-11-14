# Design a Search Autocomplete System

**Summary**: Return top-k suggestions for a prefix using a trie with cached top-k, an offline data-gathering pipeline, and sharded storage.
**Tags**: #system-design #autocomplete #trie #top-k #caching #volume-1
**Source**: System Design Volume 1.pdf — Chapter 13 (pp. 200–219)
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

**Scope & estimation** — return the top ~5 most frequent completions for a
prefix, fast (a few ms), read-heavy (a lookup per keystroke → very high QPS).

**High-level components**
- **Data gathering service** — aggregates query frequencies from logs
  (analytics logs → aggregators → weekly aggregated data) offline.
- **Query service** — serves suggestions from a fast store at request time.

**Deep dive**
- **Trie data structure** — a prefix tree; to hit the latency budget, **cache
  the top-k completions at each node** so a lookup is O(prefix length) instead of
  searching the subtree.
- **Trie operations** — create (from aggregated frequencies), update
  (rebuild periodically vs update in place), and get top-k for a prefix.
- **Scale the storage** — **shard** the trie by prefix (e.g. by first
  letters), using a lookup/sharding map to route; add replicas for read
  capacity.
- **Query service optimizations** — AJAX (no page reload), browser caching of
  suggestions, data sampling of logs at scale.

## Related Notes

- [[Design a Web Crawler]]
- [[Design a Chat System]]
