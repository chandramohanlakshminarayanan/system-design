# Payment System

**Summary**: Move money correctly and exactly-once using idempotency, a double-entry ledger as source of truth, PSP integration, and reconciliation.
**Tags**: #system-design #payments #ledger #idempotency #reconciliation #psp #volume-2
**Source**: System Design Volume 2.pdf — Chapter 11. NOTE: scanned/image PDF, not machine-readable — knowledge-based summary.
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

> ⚠️ Knowledge-based summary (source PDF not machine-readable).

Process pay-ins/pay-outs integrating external **payment service providers
(PSPs)**; correctness beats availability.

- **Idempotency** — every request carries an **idempotency key**; a state
  machine advances pending → succeeded/failed. A retried request references the
  same payment rather than charging twice (effectively exactly-once).
- **Double-entry ledger** — every movement is two balanced entries (debit +
  credit), so the books always sum to zero and any balance is derivable from
  history. This is the auditable source of truth (an imbalance = a bug).
- **PSP integration** — external providers actually move money; their calls are
  asynchronous and may fail/time out, so the system never assumes success.
- **Reconciliation** — continuously pull PSP statements and match them to ledger
  entries, correcting mismatches (mark succeeded, refund a duplicate, flag for
  review). Guarantees eventual correctness at the cost of a settlement delay.
- **Security** — minimize PCI scope (tokenize cards, keep them with the PSP);
  encryption; immutable audit logs; fraud/risk checks before authorizing.

## Related Notes

- [[Digital Wallet]]
- [[Hotel Reservation System]]
