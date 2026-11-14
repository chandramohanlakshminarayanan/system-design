# Design a URL Shortener

**Summary**: Map long URLs to short codes and redirect, using base62 encoding of a unique ID (or hashing), with a cache-heavy read path.
**Tags**: #system-design #url-shortener #base62 #hashing #caching #redirect #volume-1
**Source**: System Design Volume 1.pdf — Chapter 8 (pp. 119–131)
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

**Scope & estimation** — read-heavy (redirects ≫ creations). Example: 100M URLs
created/day ⇒ ~1160 write QPS, ~10× read QPS; keyspace must last years.

**API endpoints**
- `POST /api/v1/data/shorten` (long URL → short URL)
- `GET /api/v1/shortUrl` → 301/302 redirect to the long URL

**URL redirecting** — **301 (permanent)** is cached by the browser (offloads the
server, no click tracking); **302 (temporary)** routes every visit through the
server (enables analytics).

**URL shortening — two approaches**
- **Hash + collision resolution** — hash the long URL (e.g. CRC32/MD5/SHA-1),
  take the first N chars; on collision, append/retry. Needs a
  read-before-write / bloom-filter check.
- **Base62 conversion** — encode a **unique ID** into `[0-9a-zA-Z]`
  (62 characters). Collision-free by construction; 7 chars ≈ 3.5 trillion codes.

**Data model** — a table/KV mapping `shortURL → longURL` (plus id), sharded by
short URL for scale.

**Redirecting deep dive** — cache the mapping (short → long); serve redirects
from cache to handle the read-dominated traffic; load balancers + stateless web
servers front the cache and store.

## Related Notes

- [[Design a Unique ID Generator in Distributed Systems]]
- [[Scale From Zero to Millions of Users]]
