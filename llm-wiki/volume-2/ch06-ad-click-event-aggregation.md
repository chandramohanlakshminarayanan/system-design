# Ad Click Event Aggregation

**Summary**: Count billions of ad clicks accurately and near-real-time using a fast stream path plus a batch reconciliation path over an immutable raw archive.
**Tags**: #system-design #stream-processing #aggregation #lambda-architecture #exactly-once #volume-2
**Source**: System Design Volume 2.pdf — Chapter 6. NOTE: scanned/image PDF, not machine-readable — knowledge-based summary.
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

> ⚠️ Knowledge-based summary (source PDF not machine-readable).

Aggregate click events by ad and time window for billing and dashboards, where
**accuracy** (money) and **freshness** both matter.

- **Ingestion** — clicks land on a partitioned durable log (message queue),
  partitioned by ad id.
- **Stream path (fast, approximate)** — a stream aggregator maintains per-minute
  per-ad counts for dashboards; dedups on **event id** and uses **watermarks**
  for late/out-of-order events.
- **Batch path (exact, billing-grade)** — raw events are archived to cheap
  object storage; a periodic batch job recomputes from the immutable archive and
  **reconciles/corrects** the aggregated store.
- **Why both (lambda-style)** — stream gives freshness, batch gives money-
  accurate correctness; the raw archive is the safety net that makes correctness
  recoverable.
- **Hazards** — duplicate clicks (dedupe by id), late events (watermarks), and
  hot ads creating skewed partitions (salt/sub-partition the key).

## Related Notes

- [[Distributed Message Queue]]
- [[Metrics Monitoring and Alerting System]]
