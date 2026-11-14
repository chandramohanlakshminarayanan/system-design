# Google Maps

**Summary**: Serve map tiles (CDN), locate users, and compute routes with ETAs over a road graph using precomputed shortcuts and live traffic.
**Tags**: #system-design #maps #routing #tiles #graph #eta #cdn #volume-2
**Source**: System Design Volume 2.pdf — Chapter 3. NOTE: scanned/image PDF, not machine-readable — knowledge-based summary.
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

> ⚠️ Knowledge-based summary (source PDF not machine-readable).

Three subsystems: rendering (tiles), location/geocoding, and routing + ETA.

- **Map tiles** — the world is pre-rendered into image tiles per zoom level,
  keyed by (z, x, y), stored in object storage and served from the **CDN**, so
  most tile requests never reach origin. Vector tiles shift rendering to the
  client, saving storage.
- **Location / geocoding** — resolve addresses ↔ coordinates.
- **Routing** — the road network is a weighted **graph**; plain Dijkstra is too
  slow at continent scale, so **contraction hierarchies** precompute shortcut
  edges for millisecond queries (at the cost of an expensive periodic rebuild).
- **ETA** — sum edge traversal times, where each edge's time uses its length and
  **current speed** from a streaming pipeline ingesting GPS probes every few
  minutes; historical patterns fill sparse data.
- **Scaling / cost** — tiles scale via CDN; routing scales by sharding the graph
  and caching popular routes; treat trajectories as sensitive data.

## Related Notes

- [[Proximity Service]]
- [[Nearby Friends]]
