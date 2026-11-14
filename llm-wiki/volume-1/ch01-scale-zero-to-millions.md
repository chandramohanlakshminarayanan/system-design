# Scale From Zero to Millions of Users

**Summary**: How a single-server app evolves step by step into a distributed system that serves millions of users.
**Tags**: #system-design #scalability #load-balancing #replication #caching #cdn #sharding #volume-1
**Source**: System Design Volume 1.pdf — Chapter 1 (pp. 5–33)
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

The chapter walks the growth path of a web application one bottleneck at a time.

- **Single server setup** — web, app, DB and cache on one box; a DNS lookup
  returns its IP and it serves everything. Simple but a single point of failure.
- **Database** — separate the database onto its own server so web and data tiers
  scale independently. *Which database:* relational (SQL) for structured,
  relational data; non-relational (NoSQL) for low-latency, huge-scale, or
  unstructured data.
- **Vertical vs horizontal scaling** — vertical (bigger box) is simple but
  capped and still a SPOF; horizontal (more boxes) is the path at scale.
- **Load balancer** — distributes traffic across web servers on a private
  network, hides failures, and enables horizontal scaling.
- **Database replication** — a primary takes writes; replicas serve reads and
  provide redundancy/failover. Improves read throughput and availability.
- **Cache** — a cache tier stores frequent reads in memory. *Considerations:*
  when to use, expiration policy (TTL), consistency, eviction policy, and
  avoiding a single point of failure.
- **CDN** — serves static assets (images, JS, CSS, video) from edge locations
  near users. *Considerations:* cost, cache expiry, fallback, invalidation.
- **Stateless web tier** — move session state out of web servers (into a shared
  store) so any server handles any request; this is what makes autoscaling work.
- **Data centers** — geo-route users (geoDNS) to the nearest data center;
  replicate data across centers for latency and disaster recovery.
- **Message queue** — decouple components and support async processing so slow
  work doesn't block the request path and spikes are buffered.
- **Logging, metrics, automation** — needed as the system grows.
- **Database scaling** — vertical scaling of the DB hits limits, so **shard**
  (horizontal partitioning) by a partition key. Introduces challenges:
  resharding, celebrity/hotspot keys, and join complexity across shards.

## Related Notes

- [[Back-of-the-Envelope Estimation]]
- [[Design Consistent Hashing]]
- [[Design a Key-Value Store]]
- [[The Learning Continues]]
