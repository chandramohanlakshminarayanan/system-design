# Design a News Feed System

**Summary**: Publish posts and build personalized feeds using fan-out on write vs read, a hybrid for celebrities, and a feed cache.
**Tags**: #system-design #news-feed #fanout #feed-cache #social #volume-1
**Source**: System Design Volume 1.pdf — Chapter 11 (pp. 166–177)
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

**Scope** — build and serve a personalized, reverse-chronological feed of posts
from people you follow; read-heavy; mobile + web.

**Newsfeed APIs** — `POST /v1/me/feed` (publish) and `GET /v1/me/feed`
(retrieve).

**Feed publishing (high-level)** — request → load balancer → web servers → a set
of services: **post service** (persist to post DB/cache), **fanout service**
(deliver to friends' feeds), **notification service**.

**Newsfeed building** — the **fanout service** populates followers' feed caches.

**Deep dive**
- **Fanout models**
  - **Fan-out on write (push)** — precompute each user's feed at publish time;
    fast reads; expensive for users with many followers (the **hotkey /
    celebrity** problem); wasteful for inactive users.
  - **Fan-out on read (pull)** — build the feed at read time; cheap writes,
    slower reads.
  - **Hybrid** — push for most users, pull for celebrities.
- **Feed publishing deep dive** — web servers, fanout service (with a graph DB
  for the follower relationship and a **message queue** + workers), and a
  **news feed cache** storing `<post_id, user_id>`.
- **Newsfeed retrieval deep dive** — fetch feed post IDs from cache, then
  hydrate full post + user objects (from caches).
- **Cache architecture** — layered caches: news feed, content, social graph,
  action, counters.

## Related Notes

- [[Design a Notification System]]
- [[Design a Chat System]]
