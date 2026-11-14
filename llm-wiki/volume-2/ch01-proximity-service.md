# Proximity Service

**Summary**: Find nearby businesses within a radius using spatial indexing (geohash / quadtree), optimized for a read-heavy, mostly-static dataset.
**Tags**: #system-design #proximity #geohash #quadtree #spatial-index #volume-2
**Source**: System Design Volume 2.pdf — Chapter 1. NOTE: the Volume 2 PDF is a scanned/image document with no extractable text, so this note is a knowledge-based summary of the chapter's topic, not extracted book text.
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

> ⚠️ Knowledge-based summary (source PDF not machine-readable).

Return businesses near a location within a radius (e.g. "restaurants near me").

- **Core problem** — make 2D geospatial radius search fast and indexable.
- **Spatial indexing options**
  - **Geohash** — encode lat/long into a string; a longer prefix = smaller cell;
    nearby points share prefixes, so a radius maps to a few neighboring cells.
    Simple and prefix-queryable, but fixed cell sizes and boundary edge cases.
  - **Quadtree** — recursively subdivide space, adapting cell size to density
    (deep in dense cities, shallow in sparse areas); more complex to distribute.
  - **Google S2** — maps the sphere to cells via a space-filling curve.
- **Query flow** — compute covering cells for (point, radius) → fetch candidate
  businesses from those cells → filter by exact (haversine) distance → sort.
- **Scaling** — read-heavy over near-static data, so cache index cells and
  business details aggressively and use read replicas; dense-city cells are the
  main hotspot (mitigate with finer cells, result caps, caching).

## Related Notes

- [[Nearby Friends]]
- [[Google Maps]]
