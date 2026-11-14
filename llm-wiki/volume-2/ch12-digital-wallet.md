# Digital Wallet

**Summary**: High-throughput wallet-to-wallet transfers with strong correctness using event sourcing + CQRS, per-wallet serialization, and sagas for cross-partition transfers.
**Tags**: #system-design #wallet #event-sourcing #cqrs #saga #transfers #volume-2
**Source**: System Design Volume 2.pdf — Chapter 12. NOTE: scanned/image PDF, not machine-readable — knowledge-based summary.
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

> ⚠️ Knowledge-based summary (source PDF not machine-readable).

Move money wallet-to-wallet at high throughput while guaranteeing correctness
(no double-spend), auditability, and deterministic recovery.

- **CQRS** — separate the **command side** (validate a transfer, append events)
  from the **query side** (a materialized balance view for fast reads).
- **Event sourcing** — state is the fold over an append-only **event log**
  (debit A, credit B), giving a full audit trail and deterministic recovery via
  replay. Periodic snapshots avoid replaying from the beginning.
- **Correctness under concurrency** — serialize per-wallet writes (partition by
  wallet + expected-version check) so concurrent debits can't overspend.
- **Sagas** — for transfers spanning partitions/services, run steps with
  **compensating actions** on failure (refund A if crediting B fails), achieving
  atomicity without fragile distributed two-phase commit.
- **Scaling** — partition by wallet for parallelism; hot wallets (a popular
  merchant) are the skew to watch.

## Related Notes

- [[Payment System]]
- [[Stock Exchange]]
