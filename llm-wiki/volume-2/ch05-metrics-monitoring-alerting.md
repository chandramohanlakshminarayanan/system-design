# Metrics Monitoring and Alerting System

**Summary**: Collect metrics (pull-based), store them in a time-series DB with compression and downsampling, power dashboards, and evaluate alert rules.
**Tags**: #system-design #monitoring #time-series #alerting #prometheus #volume-2
**Source**: System Design Volume 2.pdf — Chapter 5. NOTE: scanned/image PDF, not machine-readable — knowledge-based summary.
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

> ⚠️ Knowledge-based summary (source PDF not machine-readable).

Ingest metrics from thousands of sources, store as time series, drive dashboards
and fire alerts.

- **Collection** — **pull** (scrape) targets on a schedule, which gives central
  control and turns a failed scrape into a liveness signal; a **push gateway**
  handles short-lived jobs.
- **Time-series storage** — recent samples in an in-memory head block for fast
  ingest/query; older data compressed (delta-of-delta timestamps, XOR values →
  a couple of bytes/sample) into immutable blocks, tiered to object storage.
  Watch out for **label cardinality** explosion.
- **Query service** — serves range queries for dashboards; use recording rules
  to precompute expensive queries.
- **Retention / downsampling** — keep full resolution briefly, then downsample
  (e.g. 5-minute aggregates) for long-term trends — the main cost lever.
- **Alerting** — a rule engine evaluates thresholds; an **alert manager**
  deduplicates, groups, silences, and routes notifications to avoid spam.

## Related Notes

- [[Distributed Message Queue]]
- [[Ad Click Event Aggregation]]
