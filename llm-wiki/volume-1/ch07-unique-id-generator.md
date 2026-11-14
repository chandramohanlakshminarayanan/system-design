# Design a Unique ID Generator in Distributed Systems

**Summary**: Generate unique, roughly time-sortable 64-bit IDs across many machines using the Twitter Snowflake bit layout.
**Tags**: #system-design #unique-id #snowflake #distributed-systems #volume-1
**Source**: System Design Volume 1.pdf — Chapter 7 (pp. 110–118)
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

**Requirements** — IDs must be unique, numeric, fit in 64 bits, ordered by date
(roughly time-sortable), and generatable at high rate.

**Options considered**
- **Multi-master replication** — DB auto-increment with a step of N; hard to
  scale across data centers, IDs don't sort well over time.
- **UUID** — 128-bit, generated independently with negligible collision risk;
  but non-numeric, not sortable, and large.
- **Ticket server** — a central auto-increment server; simple but a single point
  of failure and a bottleneck.
- **Twitter Snowflake** (chosen) — a **64-bit** layout:
  - 1 bit sign (unused)
  - 41 bits **timestamp** (ms since a custom epoch) → ~69 years, makes IDs
    sortable by time
  - 5 bits **datacenter id**
  - 5 bits **machine id** (32 datacenters × 32 machines)
  - 12 bits **sequence** (per-ms counter, 4096 ids/ms/node)

**Deep dive** — the timestamp occupies the high bits so IDs increase over time;
handle **clock synchronization / regression** (NTP moving backwards) and
sequence overflow within a millisecond (wait for the next ms).

## Related Notes

- [[Design a Key-Value Store]]
- [[Design a URL Shortener]]
