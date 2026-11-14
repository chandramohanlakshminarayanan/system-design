# Hotel Reservation System

**Summary**: Search availability and book rooms without overselling, using atomic inventory transactions, concurrency control, and idempotent bookings.
**Tags**: #system-design #reservation #concurrency #idempotency #inventory #volume-2
**Source**: System Design Volume 2.pdf — Chapter 7. NOTE: scanned/image PDF, not machine-readable — knowledge-based summary.
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

> ⚠️ Knowledge-based summary (source PDF not machine-readable).

Looks like CRUD, but the crux is **concurrency correctness**: never oversell the
last room under simultaneous bookings.

- **Search path** — read-heavy; served from caches/replicas of hotel and rate
  data, which may be slightly stale (the booking transaction is the authority).
- **Reservation path** — an **atomic** check-and-decrement of the (room-type,
  date) inventory rows inside a transaction. Under a race, one request wins.
  - **Optimistic concurrency** (conditional update "decrement only if
    reserved < total", retry the loser) scales better than pessimistic locks.
- **Idempotency** — each booking carries an **idempotency key** so a network-
  timeout retry returns the original result instead of double-booking/charging.
- **Reserve-then-confirm** — reserve inventory first, then confirm payment, with
  a timeout to release abandoned holds.
- **Scaling** — partition inventory by hotel; contention concentrates on popular
  hotels/dates.

## Related Notes

- [[Payment System]]
- [[Distributed Message Queue]]
