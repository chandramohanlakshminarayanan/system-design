# Distributed Email Service

**Summary**: Send, receive, store, and search email at scale by separating metadata from bulky bodies, indexing asynchronously, and delivering via a retrying queue.
**Tags**: #system-design #email #smtp #imap #search-index #object-storage #volume-2
**Source**: System Design Volume 2.pdf — Chapter 8. NOTE: scanned/image PDF, not machine-readable — knowledge-based summary.
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

> ⚠️ Knowledge-based summary (source PDF not machine-readable).

Gmail-scale send/receive/read/search.

- **Outbound (SMTP)** — mail is queued and delivered to recipient servers with
  **exponential-backoff retries**, honoring greylisting, bouncing only after
  repeated failures. External servers are flaky, so send is a durable queue, not
  a synchronous call.
- **Storage** — separate small, frequently-queried **metadata** (from/to,
  subject, flags, body reference) in a fast store keyed by mailbox from large,
  immutable **bodies/attachments** in object storage (deduplicated). Each scales
  independently; storage is the dominant cost (tier old mail).
- **Read (IMAP/POP)** — serve from the metadata + blob stores.
- **Search** — an **asynchronous** pipeline builds a per-mailbox inverted index,
  so indexing never slows delivery (brand-new mail is briefly unsearchable).
- **Security** — spam/phishing filtering; DKIM/SPF/DMARC for authenticity; TLS
  in transit; encryption at rest; strict per-mailbox access control.

## Related Notes

- [[S3-like Object Storage]]
- [[Distributed Message Queue]]
