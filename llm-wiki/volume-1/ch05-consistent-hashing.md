# Design Consistent Hashing

**Summary**: A hashing scheme that minimizes key remapping when nodes are added or removed, using a hash ring and virtual nodes.
**Tags**: #system-design #consistent-hashing #partitioning #hash-ring #virtual-nodes #volume-1
**Source**: System Design Volume 1.pdf — Chapter 5 (pp. 71–86)
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

**The rehashing problem** — with `hash(key) % N`, changing N (adding/removing a
server) remaps almost every key, causing a storm of cache misses.

**Consistent hashing** — map the hash output onto a **hash ring** (a circular
space). Place **servers** on the ring by hashing their identifiers, and place
**keys** on the ring too. **Server lookup:** from a key's position, go
clockwise to the first server — that server owns the key.

- **Add a server** — only keys between the new server and its predecessor move.
- **Remove a server** — its keys move to the next server clockwise. Everything
  else stays put.

**Two issues in the basic approach** — (1) uneven partition sizes when servers
land unevenly on the ring; (2) non-uniform key distribution / hotspots.

**Virtual nodes** — give each physical server many positions on the ring. This
smooths distribution and spreads a departing server's load across many
survivors. More virtual nodes ⇒ more even load but more metadata.

**Find affected keys** — on membership change, only the keys in the affected arc
must be redistributed.

Used by Amazon Dynamo, Cassandra, Discord, and CDN/partitioning systems.

## Related Notes

- [[Design a Key-Value Store]]
- [[Scale From Zero to Millions of Users]]
