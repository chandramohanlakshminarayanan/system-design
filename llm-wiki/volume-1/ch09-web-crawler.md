# Design a Web Crawler

**Summary**: Crawl the web at scale from seed URLs using a URL frontier, BFS traversal, politeness, and dedup, while handling traps and robustness.
**Tags**: #system-design #web-crawler #url-frontier #bfs #bloom-filter #politeness #volume-1
**Source**: System Design Volume 1.pdf — Chapter 9 (pp. 132–150)
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

**Scope & estimation** — used for search indexing, archiving, data mining. Size
by pages/month (e.g. 1B pages/month) and average page size for storage/bandwidth.

**High-level flow** — Seed URLs → **URL Frontier** → **HTML Downloader** (via DNS
resolver) → **Content Parser** → **"Content Seen?"** dedup → Content Storage;
extracted links → **URL Extractor** → **"URL Seen?"** filter → back to the
frontier.

**Deep dive**
- **DFS vs BFS** — crawlers use **BFS** (a FIFO queue); DFS can go too deep.
- **URL Frontier** — manages **politeness** (per-host delay, one worker per host
  via a mapping table + back queues) and **priority** (prioritizer by
  importance/PageRank); also freshness and storage (mostly on disk with in-memory
  buffers).
- **HTML Downloader** — respects **robots.txt**; performance via distributed
  crawl, DNS caching, locality, and short timeouts.
- **Robustness** — consistent hashing to distribute load, save crawl state for
  restarts, handle exceptions, validate data.
- **Extensibility** — pluggable modules for new content types.
- **Detect and avoid problematic content** — redundant content (hashes),
  **spider traps** (URL-length limits), and data noise.

## Related Notes

- [[Design Consistent Hashing]]
- [[Design a Search Autocomplete System]]
