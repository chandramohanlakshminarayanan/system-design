# S3-like Object Storage

**Summary**: Durable, near-unlimited object storage by bucket+key, separating a strongly-consistent metadata plane from a data plane using replication or erasure coding.
**Tags**: #system-design #object-storage #erasure-coding #replication #durability #metadata #volume-2
**Source**: System Design Volume 2.pdf — Chapter 9. NOTE: scanned/image PDF, not machine-readable — knowledge-based summary.
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

> ⚠️ Knowledge-based summary (source PDF not machine-readable).

Store arbitrary blobs retrievable by **bucket + key** with extreme durability at
low cost.

- **Metadata vs data plane** — metadata (small, needs strong consistency and
  listing) is separated from the bytes (petabytes, needs throughput and low
  cost). The metadata store itself must shard/cache (billions of objects).
- **Durability**
  - **Replication** (e.g. 3 copies) — simple, fast repair, but 3× storage.
  - **Erasure coding** (k data + m parity) — tolerates m losses at ~1.4×
    overhead (roughly half the cost of 3× replication), at the price of more CPU
    and slower reconstruction.
  - Spread copies/fragments across independent **failure domains**.
- **Immutability & versioning** — objects are immutable; "edits" write new
  versions, which simplifies caching/replication/dedup and enables strong
  read-after-write. Deletes are metadata ops with async space reclamation.
- **Reliability** — a background scrubber verifies checksums and rebuilds lost
  fragments.
- **Multipart upload** for large objects; **per-bucket IAM**, encryption at
  rest, and signed URLs for security.

## Related Notes

- [[Distributed Email Service]]
- [[Design YouTube]]
