# Distributed Message Queue

**Summary**: A durable, partitioned, append-only log (Kafka-style) with replication, per-partition ordering, and consumer groups with offsets.
**Tags**: #system-design #message-queue #kafka #partitioning #replication #consumer-groups #volume-2
**Source**: System Design Volume 2.pdf — Chapter 4. NOTE: scanned/image PDF, not machine-readable — knowledge-based summary.
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

> ⚠️ Knowledge-based summary (source PDF not machine-readable).

Decouple producers from consumers, absorb spikes, and enable event-driven
architectures.

- **Partitioned append-only log** — a topic splits into **partitions**, each an
  append-only log written **sequentially** (the key to high throughput).
  Producers append to a partition chosen by key, so messages for a key are
  ordered. Ordering is guaranteed **only within a partition** — the deliberate
  trade that enables parallelism.
- **Replication** — each partition has a leader and follower replicas; a write
  is committed once enough **in-sync replicas (ISR)** ack. `acks=all` is durable
  but slower; `acks=1` is faster with a small loss window on leader failure.
- **Consumer groups + offsets** — partitions are divided among a group's members
  for parallel consumption; each consumer commits an **offset**, enabling resume
  and **replay** from any point. Offsets decouple producers from consumers.
- **Delivery semantics** — at-least-once by default; exactly-once via idempotent
  producers / transactional writes or idempotent consumers.
- **Scaling / cost** — add partitions for parallelism and brokers for capacity;
  retention length sets storage cost (tier old segments); watch for hot
  partitions from skewed keys.

## Related Notes

- [[Metrics Monitoring and Alerting System]]
- [[Ad Click Event Aggregation]]
