# Design a Rate Limiter

**Summary**: Throttle client requests using algorithms like token bucket, with a distributed Redis-backed design that returns 429 and rate-limit headers.
**Tags**: #system-design #rate-limiter #redis #token-bucket #api-gateway #volume-1
**Source**: System Design Volume 1.pdf — Chapter 4 (pp. 51–70)
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

**Where to put it** — client-side is unreliable; a server-side limiter or a
dedicated middleware / API gateway is preferred so all services are protected.

**Algorithms for rate limiting**
- **Token bucket** — tokens refill at a fixed rate; each request spends one;
  allows bursts. Common default.
- **Leaking bucket** — fixed-rate outflow (a FIFO queue); smooths traffic.
- **Fixed window counter** — count per interval; simple but allows a 2× burst
  at window edges.
- **Sliding window log** — timestamps per request; accurate but memory-heavy.
- **Sliding window counter** — hybrid of fixed windows; good accuracy/cost.

**High-level architecture** — counters live in an in-memory store (Redis) using
`INCR`/`EXPIRE`; the limiter checks the counter and allows or rejects.

**Deep dive**
- **Rate limiting rules** — configuration (e.g. domain/limit/window), often in a
  config store.
- **Exceeding the limit** — return **HTTP 429**; optionally enqueue for later.
  Return headers: `X-Ratelimit-Remaining`, `-Limit`, `-Retry-After`.
- **Distributed environment** — two challenges: **race conditions** (fix with
  atomic ops / Lua scripts / locks) and **synchronization** (use a centralized
  store like Redis rather than per-node state).
- **Performance optimization** — multi-data-center, edge enforcement, eventual
  consistency of counters.
- **Monitoring** — verify the algorithm and rules are effective.

## Related Notes

- [[Scale From Zero to Millions of Users]]
- [[Design a Key-Value Store]]
