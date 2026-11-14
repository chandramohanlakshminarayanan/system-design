# Nearby Friends

**Summary**: Continuously show which friends are nearby in real time using WebSockets, Redis pub/sub fan-out, and a short-TTL location cache.
**Tags**: #system-design #real-time #websocket #pubsub #location #volume-2
**Source**: System Design Volume 2.pdf — Chapter 2. NOTE: scanned/image PDF, not machine-readable — this is a knowledge-based summary, not extracted book text.
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

> ⚠️ Knowledge-based summary (source PDF not machine-readable).

Unlike the mostly-static proximity service, this is **real-time and
write-heavy**: phones stream location every few seconds and the system computes
which friends are within a radius.

- **Persistent connections** — clients hold a **WebSocket** to a connection
  server for low-latency push.
- **Fan-out via pub/sub** — each location update is **published** to the user's
  channel; friends' sessions **subscribe** and compute distance. Bounding
  fan-out to friends (not all users) keeps per-update cost tractable; the bus
  (e.g. Redis pub/sub) scales horizontally.
- **Live location cache with TTL** — recent positions live in memory with a
  short TTL; stop sharing and you expire off friends' maps quickly (a built-in
  privacy feature). Raw history is persisted asynchronously off the hot path.
- **Scaling story** — fan-out volume and concurrent-connection count are the
  challenges; shard users across connection servers and route subscriptions by
  user id.
- **Privacy** — enforce mutual-friend authorization on every subscription;
  minimize and encrypt location history.

## Related Notes

- [[Proximity Service]]
- [[Google Maps]]
