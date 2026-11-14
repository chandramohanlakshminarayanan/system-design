# Design a Chat System

**Summary**: Real-time 1:1 and group messaging over WebSocket, with service discovery, a message store, presence, and multi-device sync.
**Tags**: #system-design #chat #websocket #presence #messaging #volume-1
**Source**: System Design Volume 1.pdf — Chapter 12 (pp. 178–199)
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

**Real-time transport options**
- **Polling** — client asks periodically; wasteful.
- **Long polling** — server holds the request until data or timeout; better but
  still awkward, and servers can't tell if a client disconnected.
- **WebSocket** (chosen) — a persistent, bidirectional connection enabling
  server **push**; used for both sending and receiving.

**High-level design** — stateless services (auth, group management, user
profile) behind a load balancer; **stateful chat servers** hold WebSocket
connections; third-party integration for push notifications. Scale across data
centers.

**Data models** — messages stored in a **key-value store** for easy horizontal
scaling and low-latency access. 1:1 messages keyed by `message_id`; group
messages keyed by `(channel_id, message_id)`. Use a **local, per-node sequence /
message ID** that is time-sortable so clients can order and sync.

**Deep dive**
- **Service discovery** — pick the best chat server for a client (e.g. via
  ZooKeeper) based on geography/load.
- **Message flows** — 1:1 flow (sender → chat server → message sync queue →
  KV store → recipient's chat server → recipient). Offline recipients read from
  an offline message queue on reconnect. Group flows fan the message to each
  member's queue.
- **Online presence** — presence servers track online/offline via login,
  disconnect, and **heartbeat**; fan out presence changes to friends.

## Related Notes

- [[Design a News Feed System]]
- [[Design a Search Autocomplete System]]
