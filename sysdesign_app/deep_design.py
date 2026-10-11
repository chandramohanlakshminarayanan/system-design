"""
Book-style component walkthroughs for the High-level design section.

Each entry maps a chapter id to a list of Component(name, role, detail),
explaining *why each piece exists*, how it works, the design decisions, and
alternatives considered — the kind of detail the ByteByteGo books give.

These are attached to chapters by registry.py, so the big content files stay
manageable and depth can be added chapter by chapter.
"""

from __future__ import annotations

from schema import Component

COMPONENTS: dict[str, list[Component]] = {}


# ---------------------------------------------------------------------------
# Chapter 1 — Scale from Zero to Millions of Users
# ---------------------------------------------------------------------------
COMPONENTS["v1_ch1"] = [
    Component(
        "Load balancer", "Spreads traffic across web servers and hides failures",
        "The load balancer sits between users and a pool of web servers, "
        "distributing requests (round-robin, least-connections, etc.) and health-"
        "checking each server. Clients only ever see the load balancer's public "
        "IP; the web servers live on a private network. This does two things at "
        "once: it lets you **scale horizontally** (add servers to the pool) and it "
        "removes the web tier as a single point of failure — if a server dies, the "
        "balancer stops routing to it and users notice nothing.\n\n"
        "*Decision:* we scale out (many small servers) rather than up (one big "
        "server) because a single machine has a hard ceiling and is itself a SPOF.",
    ),
    Component(
        "Stateless web tier", "Application servers that hold no session state",
        "Each web server processes any request without relying on data from a "
        "previous request on the same box. Session state (who is logged in, cart "
        "contents) is pushed into a shared store (Redis) or a signed token. "
        "Statelessness is what makes horizontal scaling and autoscaling trivial — "
        "any server can handle any user, so you can add/remove servers freely and a "
        "crash loses no session.\n\n"
        "*Alternative considered:* sticky sessions pin a user to one server, but "
        "that unbalances load and loses sessions on failure — so we avoid it.",
    ),
    Component(
        "Database: primary + read replicas", "Primary takes writes; replicas serve reads",
        "A single database handles both reads and writes at first. Because the "
        "workload is ~100:1 reads:writes, we add **read replicas**: the primary "
        "accepts all writes and asynchronously streams changes to replicas, which "
        "serve reads. This absorbs the dominant read load and gives us a failover "
        "target if the primary dies.\n\n"
        "*Trade-off:* replicas lag the primary by a small amount (**replication "
        "lag**), so a read right after a write may be stale. Flows that need "
        "read-your-writes are routed to the primary.",
    ),
    Component(
        "Cache (cache-aside)", "In-memory store for hot reads",
        "A cache such as Redis sits in front of the database. On a read, the app "
        "checks the cache first; on a **miss** it reads the database and populates "
        "the cache; on a **hit** it skips the database entirely. This is the "
        "cache-aside pattern. It's the cheapest latency win available — a memory "
        "lookup (~100 ns) versus a database query (milliseconds).\n\n"
        "*Decisions:* set a **TTL** so data eventually refreshes, and invalidate on "
        "write to bound staleness. Watch for **cache stampede** on hot keys "
        "(many misses at once) — mitigate with request coalescing and staggered TTLs.",
    ),
    Component(
        "CDN", "Serves static assets from edge locations near users",
        "Images, CSS, JS and video are served from a Content Delivery Network — a "
        "global mesh of edge caches. A user in Tokyo fetches assets from a Tokyo "
        "edge, not your origin in Virginia, cutting latency and offloading traffic "
        "from your servers. Assets are versioned so a deploy cache-busts cleanly.\n\n"
        "*Trade-off:* the CDN can serve slightly stale assets until TTL expiry; "
        "versioned filenames avoid that.",
    ),
    Component(
        "Message queue + workers", "Moves slow work off the request path",
        "Slow or spiky tasks (sending email, processing images, fan-out) are pushed "
        "onto a message queue and handled by a separate pool of **workers**. The web "
        "request returns immediately after enqueuing, so user-facing latency stays "
        "low and traffic spikes are absorbed by the queue instead of overwhelming "
        "the servers.\n\n"
        "*Trade-off:* the work now happens asynchronously (eventual completion), "
        "which is fine for tasks that don't need an instant result.",
    ),
    Component(
        "Database sharding", "Partitions data across multiple databases",
        "When a single primary can no longer absorb the **write** load (replicas "
        "only scale reads), we shard: split the data across multiple databases by a "
        "partition key (e.g. user_id). Each shard owns a slice of the data and its "
        "own writes, so write throughput scales with the number of shards.\n\n"
        "*Trade-off:* cross-shard queries and transactions become hard, and "
        "rebalancing shards is operationally painful — so sharding is deferred until "
        "estimation proves it's needed.",
    ),
]


# ---------------------------------------------------------------------------
# Chapter 4 — Rate Limiter
# ---------------------------------------------------------------------------
COMPONENTS["v1_ch4"] = [
    Component(
        "API gateway (enforcement point)", "Where the limiter runs, in front of all services",
        "The rate limiter is placed in the API gateway so every downstream service "
        "is protected uniformly and no service has to implement limiting itself. "
        "The gateway extracts the client identity (API key, then IP as a fallback), "
        "looks up the matching rule, and decides allow/deny before routing.\n\n"
        "*Alternative considered:* client-side limiting is easily bypassed; a "
        "per-service library duplicates logic and state. Centralizing at the gateway "
        "is the clean choice.",
    ),
    Component(
        "Redis counter store", "Shared, atomic counters across all gateway nodes",
        "Counts live in Redis so that all gateway instances share one source of "
        "truth — otherwise each node would count independently and a client could "
        "exceed the limit N-fold. Check-and-increment runs as a **Lua script** so "
        "the read, compare and write are atomic (no race between concurrent "
        "requests). A TTL on each key auto-expires old windows so memory stays "
        "bounded.\n\n"
        "*Trade-off:* Redis is now a hot dependency on every request — cluster it "
        "and, at extreme QPS, give each node a small local budget it reconciles "
        "periodically to cut round trips.",
    ),
    Component(
        "Algorithm (sliding-window counter)", "Decides whether a request fits under the limit",
        "The default algorithm is the sliding-window counter: it blends the "
        "previous and current fixed-window counts to approximate a true rolling "
        "window, giving near-exact accuracy without storing a timestamp per request. "
        "Token bucket is the alternative when you want to explicitly allow bursts.\n\n"
        "*Trade-off table (see below)* compares token bucket, leaking bucket, fixed "
        "window, sliding-window log and sliding-window counter on burst behavior, "
        "memory and accuracy.",
    ),
    Component(
        "Rule store", "Holds per-tier / per-endpoint limits",
        "Limits (requests, window size, algorithm, scope) are configuration, cached "
        "hot and reloadable without a deploy. This lets you set different limits per "
        "API tier (free vs paid) or per endpoint (a cheap GET vs an expensive "
        "export).",
    ),
    Component(
        "429 response + headers", "Tells clients they're limited and when to retry",
        "When a client exceeds its limit the gateway returns **HTTP 429 Too Many "
        "Requests** with a `Retry-After` header and `X-RateLimit-Limit/Remaining/"
        "Reset` headers, so well-behaved clients back off correctly. On a Redis "
        "outage the limiter **fails open** for general traffic (availability first) "
        "or **fails closed** for sensitive endpoints (protection first) — a "
        "deliberate per-endpoint choice.",
    ),
]


# ---------------------------------------------------------------------------
# Chapter 6 — Key-Value Store
# ---------------------------------------------------------------------------
COMPONENTS["v1_ch6"] = [
    Component(
        "Consistent-hashing partitioner", "Places each key on a node with minimal churn",
        "Keys are mapped onto a hash ring; each key is owned by the next node "
        "clockwise. Virtual nodes smooth the distribution. This is how the store "
        "scales horizontally: adding or removing a node moves only ~1/N of keys "
        "instead of remapping everything.\n\n"
        "*Why:* naive `hash % N` remaps almost all keys on any membership change — "
        "catastrophic for a live cluster.",
    ),
    Component(
        "Replication (N copies)", "Stores each key on the next N nodes for durability",
        "Every key is replicated to the N nodes clockwise from its position. If one "
        "node fails, the data survives on the others, and reads/writes can still be "
        "served. N=3 is the usual durability/cost sweet spot.\n\n"
        "*Trade-off:* replication multiplies storage by N and requires keeping "
        "replicas consistent — handled by quorums and anti-entropy below.",
    ),
    Component(
        "Quorum coordinator (N, W, R)", "Tunes consistency vs latency per operation",
        "Any node can coordinate a request. A write waits for **W** replicas to "
        "acknowledge; a read gathers **R** responses. When **W + R > N**, a read is "
        "guaranteed to see the latest write (strong consistency). Lowering W or R "
        "trades consistency for lower latency and higher availability.\n\n"
        "*Decision:* expose the knobs so callers pick per-operation guarantees "
        "(e.g. W=N,R=1 for read-heavy; W=2,R=2 for balanced strong consistency).",
    ),
    Component(
        "Vector clocks + reconciliation", "Detects and resolves conflicting versions",
        "Concurrent writes to different replicas create divergent versions. Vector "
        "clocks record causality so the system can distinguish a strictly newer "
        "version from a genuine conflict. Real conflicts are resolved by "
        "last-write-wins (simple, can lose data) or returned to the application to "
        "merge (e.g. union shopping carts).",
    ),
    Component(
        "Gossip + Merkle-tree anti-entropy", "Keeps membership and replicas healthy",
        "Nodes exchange membership and failure information peer-to-peer via "
        "**gossip**, avoiding a central registry. Divergent replicas are found and "
        "repaired using **Merkle trees** — hash trees that let two nodes compare "
        "large datasets and pinpoint only the ranges that differ, without scanning "
        "everything. Temporary failures use **hinted handoff** (a healthy node "
        "holds writes for the down node and replays them on recovery).",
    ),
]


# ---------------------------------------------------------------------------
# Chapter 8 — URL Shortener
# ---------------------------------------------------------------------------
COMPONENTS["v1_ch8"] = [
    Component(
        "Write service + ID generator", "Creates the short code for a long URL",
        "On create, the write service obtains a unique 64-bit id (Snowflake or a "
        "ranged counter) and **base62-encodes** it into a ~7-character short code, "
        "then stores the `code -> long_url` mapping. Encoding a unique id is "
        "**collision-free by construction**.\n\n"
        "*Alternative considered:* hashing the long URL (e.g. MD5 then truncate) "
        "risks collisions, forcing a read-before-write check and retries — extra "
        "work on the write path. Encoding a unique id avoids all of that.",
    ),
    Component(
        "Read service (redirect path)", "Resolves a short code and redirects — the hot path",
        "This path handles ~100x the traffic of creation. On `GET /{code}` it looks "
        "up the mapping (cache first) and issues an HTTP redirect. Everything here "
        "is optimized for read latency and availability, because redirects must "
        "essentially never fail.\n\n"
        "*Decision:* use **302 (temporary)** by default so every visit flows through "
        "us and clicks can be counted; use **301 (permanent)** where analytics "
        "aren't needed so browsers cache the redirect and offload us.",
    ),
    Component(
        "Cache + CDN", "Absorbs the redirect read load",
        "A Redis cache (and optionally a CDN for very hot links) fronts the "
        "database. Because the working set of popular links is small and reads "
        "dominate, cache hit rates are very high, so the database mostly handles "
        "cold lookups and writes. This is what lets a modest database serve "
        "100k+ redirect QPS.\n\n"
        "*Trade-off:* on link edit/expiry the cache must be invalidated to avoid "
        "serving a stale destination.",
    ),
    Component(
        "URL store (KV / NoSQL)", "Durable mapping of short code to long URL",
        "The mapping is stored in a NoSQL/KV store keyed by short_code for O(1) "
        "lookups, sharded by code so it scales to hundreds of billions of rows. "
        "Rows also carry optional `expires_at` and `click_count`.\n\n"
        "*Alternative considered:* a relational DB gives rich queries but is harder "
        "to shard; for a pure key lookup at this scale, KV wins.",
    ),
]


# ---------------------------------------------------------------------------
# Chapter 11 — News Feed
# ---------------------------------------------------------------------------
COMPONENTS["v1_ch11"] = [
    Component(
        "Post service", "Persists a new post and kicks off distribution",
        "When a user publishes, the post service writes the post to the Post DB "
        "(sharded by post_id) and hands off to the fanout service. Media is stored "
        "in blob storage and served via CDN; the post row just holds a reference.",
    ),
    Component(
        "Fanout service", "Distributes a post into followers' feeds",
        "For normal users, fanout **pushes** the new post id into each follower's "
        "precomputed feed cache (fan-out on write) so reads are cheap. Fanout runs "
        "**asynchronously** off a queue, so publishing returns instantly and write "
        "spikes are smoothed.\n\n"
        "*The celebrity problem:* pushing to tens of millions of followers per post "
        "is infeasible, so celebrity posts are **not** pushed — they're pulled at "
        "read time and merged. This hybrid is the crux of the design.",
    ),
    Component(
        "Feed cache", "Per-user list of precomputed post ids",
        "Each active user has a Redis list of the most recent post ids in their "
        "feed. Reads fetch this list, then hydrate the ids into full posts. The "
        "list is length-capped (e.g. most recent 1,000) and inactive users' feeds "
        "are evicted and regenerated on demand to bound memory.",
    ),
    Component(
        "Feed read + hydration", "Assembles the final feed the user sees",
        "On read, the web tier fetches the user's cached feed ids, **merges in** any "
        "celebrity posts (pull), then hydrates post content (batched, cached). "
        "Optionally a ranking service reorders candidates by an ML score to move "
        "from chronological to ranked feed.\n\n"
        "*Trade-off:* ranking improves relevance but adds read-time latency and "
        "complexity.",
    ),
]


# ---------------------------------------------------------------------------
# Chapter 12 — Chat System
# ---------------------------------------------------------------------------
COMPONENTS["v1_ch12"] = [
    Component(
        "WebSocket connection servers", "Hold millions of persistent client connections",
        "Each client keeps a persistent **WebSocket** to a connection server "
        "(~100k sockets per server), enabling the server to **push** messages for "
        "sub-second delivery rather than the client polling. This persistent-"
        "connection tier — not compute — is the scaling story of a chat system.\n\n"
        "*Trade-off:* more sockets per server is cheaper but a single server failure "
        "drops more users at once (who then reconnect elsewhere).",
    ),
    Component(
        "Service discovery / presence routing", "Maps each user to the server holding their connection",
        "A directory records which connection server currently holds each user's "
        "socket, so the chat service knows where to push a message. When a server "
        "dies, its clients reconnect and re-register. This indirection is what makes "
        "routing a message to an online recipient possible across a large fleet.",
    ),
    Component(
        "Chat service + message store", "Persists messages and delivers them in order",
        "The chat service persists each message to a **KV/wide-column store** keyed "
        "by (conversation_id, message_id) where the id is **time-sortable** "
        "(Snowflake/sequence). This gives per-conversation ordering and lets a "
        "client sync by requesting 'everything after my last-seen id'. Delivery is "
        "at-least-once; clients dedup by id.\n\n"
        "*Offline recipients:* messages are stored and delivered on reconnect, so "
        "nothing is lost while a device is away.",
    ),
    Component(
        "Presence service", "Tracks who is online via heartbeats",
        "Clients send periodic heartbeats; the presence service marks users online/"
        "last-seen and notifies friends of changes. Heartbeat volume is large, so "
        "updates are batched and the frequency coarsened to control load.",
    ),
]


# ---------------------------------------------------------------------------
# Chapter 14 — YouTube
# ---------------------------------------------------------------------------
COMPONENTS["v1_ch14"] = [
    Component(
        "Upload flow (pre-signed URLs)", "Client uploads originals straight to blob storage",
        "The client requests a **pre-signed URL** and uploads the original video "
        "**directly to blob storage**, bypassing the app servers so they never sit "
        "in the multi-gigabyte byte path. Large uploads are resumable.\n\n"
        "*Why:* routing video bytes through app servers would make them a bottleneck; "
        "direct-to-storage keeps the control plane and data plane separate.",
    ),
    Component(
        "Transcoding pipeline (DAG)", "Turns the original into multiple renditions",
        "Transcoding is CPU-heavy and parallelizable. It's modeled as a **DAG**: "
        "split the video into segments, transcode segments in parallel across a "
        "worker fleet into several resolutions/codecs (240p…4K) plus a streaming "
        "manifest, then assemble. Failures retry at the segment level.\n\n"
        "*Cost decision:* run on spot/preemptible compute — cheaper, and tasks are "
        "designed to tolerate preemption.",
    ),
    Component(
        "Blob storage", "Durably stores originals and renditions",
        "Originals and all renditions live in object storage (petabyte-scale). Hot, "
        "popular videos stay on fast storage/CDN; cold videos are **tiered** to "
        "cheaper archival storage to control cost.",
    ),
    Component(
        "CDN + adaptive streaming", "Delivers video smoothly to a global audience",
        "Videos are stored as short **chunks** at multiple bitrates with an HLS/DASH "
        "manifest. The player picks the bitrate matching current bandwidth "
        "(**adaptive streaming**) to avoid rebuffering, and fetches chunks from the "
        "nearest **CDN** edge. The CDN serves the overwhelming majority of bytes, so "
        "the origin is rarely touched.\n\n"
        "*Trade-off:* more renditions give smoother adaptation but cost more to "
        "transcode and store.",
    ),
]


# ---------------------------------------------------------------------------
# Chapter 5 — Consistent Hashing
# ---------------------------------------------------------------------------
COMPONENTS["v1_ch5"] = [
    Component(
        "Hash ring", "Maps the hash space onto a circle",
        "Both nodes and keys are hashed onto a ring (0 … 2^m). A key is owned by "
        "the first node encountered clockwise from the key's position. This is the "
        "core trick: membership changes only affect the arc between a node and its "
        "predecessor, not the whole keyspace.",
    ),
    Component(
        "Virtual nodes", "Many ring positions per physical node",
        "Each physical node is placed at ~100–200 positions on the ring. This "
        "smooths distribution (no node owns a giant arc) and spreads a departing "
        "node's keys across many survivors instead of dumping them on one "
        "neighbor.\n\n"
        "*Trade-off:* more virtual nodes give more even load but cost more metadata "
        "and slightly slower lookups.",
    ),
    Component(
        "Lookup + rebalancer", "Routes keys and handles membership changes",
        "A lookup binary-searches the sorted ring positions (O(log n)). On add/"
        "remove, only the affected key range is remapped and, for a data store, "
        "that bounded slice is transferred. Weighted virtual-node counts let bigger "
        "machines take proportionally more of the ring.",
    ),
]


# ---------------------------------------------------------------------------
# Chapter 7 — Unique ID Generator
# ---------------------------------------------------------------------------
COMPONENTS["v1_ch7"] = [
    Component(
        "Timestamp bits (41)", "Make IDs sortable by time",
        "The high 41 bits hold milliseconds since a custom epoch, giving ~69 years "
        "of range and making IDs roughly increasing over time — so they double as a "
        "rough ordering key and preserve index locality.",
    ),
    Component(
        "Datacenter + machine bits (5 + 5)", "Make IDs unique across the fleet",
        "10 bits identify the generating node (up to 1,024 nodes). Assigned once at "
        "startup (often via a coordination service), these bits guarantee two nodes "
        "never mint the same id in the same millisecond without any runtime "
        "coordination.",
    ),
    Component(
        "Sequence counter (12)", "Uniqueness within a single millisecond",
        "Within one millisecond a node increments a 12-bit sequence (4,096 ids/ms). "
        "On overflow the node waits for the next millisecond. A **clock-regression** "
        "guard detects the clock moving backwards (NTP) and pauses generation to "
        "avoid duplicate or out-of-order ids.",
    ),
]


# ---------------------------------------------------------------------------
# Chapter 9 — Web Crawler
# ---------------------------------------------------------------------------
COMPONENTS["v1_ch9"] = [
    Component(
        "URL frontier", "The prioritized, polite queue of URLs to crawl",
        "The frontier is the crawler's brain. It balances **priority** (crawl "
        "important/fresh pages first) via priority queues, and **politeness** "
        "(limit concurrent requests per host) via per-host queues with timing. A "
        "router maps each URL to the correct host queue.\n\n"
        "*Why it matters:* too aggressive and you get banned; too polite and "
        "throughput collapses.",
    ),
    Component(
        "HTML downloader", "Fetches pages, respecting robots.txt and DNS caching",
        "Stateless, horizontally scalable workers fetch pages. They honor "
        "robots.txt, cache DNS to avoid resolution bottlenecks, and enforce "
        "timeouts so a slow host doesn't block a worker.",
    ),
    Component(
        "Parser + link extractor", "Extracts and normalizes new links",
        "Parses fetched HTML, extracts links, and normalizes them (resolve relative "
        "URLs, strip fragments) before they re-enter the frontier. Parsing is "
        "sandboxed against malicious pages.",
    ),
    Component(
        "Dedup (Bloom filter) + trap detection", "Avoids re-crawling and infinite spaces",
        "A **Bloom filter** tracks seen URLs space-efficiently (accepting a tiny "
        "false-positive rate that skips a few pages). Content hashing skips near-"
        "duplicate pages. Depth/URL-length limits and pattern rules detect **spider "
        "traps** (infinite calendars, session-id URLs).",
    ),
]


# ---------------------------------------------------------------------------
# Chapter 10 — Notification System
# ---------------------------------------------------------------------------
COMPONENTS["v1_ch10"] = [
    Component(
        "Notification API", "Single entry point for all services",
        "Services call one API to send a notification (recipient, channel, "
        "template, data). It validates the request, checks user preferences/opt-"
        "outs, and enqueues per-channel messages. Centralizing here enforces "
        "consistent preference and rate rules.",
    ),
    Component(
        "Message queue", "Decouples producers from channel delivery",
        "Per-channel queues buffer messages between the API and the workers. This "
        "absorbs broadcast spikes (millions of messages instantly) and lets each "
        "channel scale independently, so email backlog doesn't stall push.",
    ),
    Component(
        "Channel workers + providers", "Deliver via APNs/FCM, SMS and email",
        "Workers pull from queues and call the right provider, enforcing each "
        "provider's rate limits. Delivery is **at-least-once** with exponential-"
        "backoff retries; **idempotency keys** dedup so users don't get duplicates. "
        "Poison messages go to a dead-letter queue.",
    ),
    Component(
        "Preference & template store", "Respects opt-outs and formats content",
        "A fast KV lookup on the send path holds per-user, per-channel opt-in state, "
        "quiet hours and device tokens. Templates are injection-safe so user data "
        "can't break out into headers/markup. This is both a UX and a compliance "
        "control.",
    ),
]


# ---------------------------------------------------------------------------
# Chapter 13 — Search Autocomplete
# ---------------------------------------------------------------------------
COMPONENTS["v1_ch13"] = [
    Component(
        "Trie with cached top-K", "Serves suggestions in O(prefix) time",
        "A trie (prefix tree) stores queries; crucially, each node **caches the "
        "top-K completions** for its subtree. A lookup walks to the prefix node and "
        "returns its cached list directly — no subtree search at query time. This "
        "is what meets the sub-10ms budget at ~half a million QPS.\n\n"
        "*Trade-off:* caching top-K per node costs memory and build time, but turns "
        "reads into trivial lookups — the right trade for a read-dominated system.",
    ),
    Component(
        "Query service", "Stateless front end for suggestion lookups",
        "Receives each keystroke's prefix, routes to the correct trie shard, and "
        "returns the cached top-K. Stateless and replicated for high read QPS.",
    ),
    Component(
        "Offline aggregation pipeline", "Computes query popularity from logs",
        "A batch (or streaming) job aggregates query frequencies from logs and "
        "rebuilds the trie periodically, then hot-swaps it. Keeping this heavy work "
        "**offline** means the serving path never does expensive computation. "
        "Sampling logs keeps aggregation affordable at scale.",
    ),
    Component(
        "Sharding by prefix", "Splits the trie across servers",
        "One trie can't fit or serve the full QPS from a single node, so it's "
        "sharded by prefix (e.g. first characters) with a router directing requests, "
        "plus replicas per shard for capacity and availability.",
    ),
]


# ---------------------------------------------------------------------------
# Chapter 15 — Google Drive
# ---------------------------------------------------------------------------
COMPONENTS["v1_ch15"] = [
    Component(
        "Block splitter + content-addressed store", "Delta sync and dedup",
        "Files are split into **blocks**; each block is hashed and stored under its "
        "hash in object storage. An edit uploads only the **changed blocks** (delta "
        "sync), and identical blocks — across versions or users — are stored once "
        "(**dedup**). A one-line edit transfers a few KB, not the whole file.\n\n"
        "*Trade-off:* smaller blocks give finer dedup/diff but more metadata.",
    ),
    Component(
        "Metadata service", "Source of truth for files, versions, permissions",
        "A strongly-consistent, sharded database tracks each file's name, version, "
        "ordered block list and ACLs. Versions are just different block lists, so "
        "history is cheap. Metadata is small and query-heavy; keeping it separate "
        "from bulky block bytes lets each scale independently.",
    ),
    Component(
        "Notification service", "Tells other devices when something changed",
        "When a device commits a change, the notification service signals the "
        "user's other devices (long-poll/streaming) to pull the new metadata and "
        "any missing blocks, converging all devices.",
    ),
    Component(
        "Conflict handling", "Resolves concurrent offline edits",
        "Two devices editing offline diverge. The policy is **last-writer-wins** "
        "with a preserved **conflict copy** so no data is silently lost, while "
        "metadata operations stay strongly consistent so all devices agree on the "
        "current version pointer.",
    ),
]


# ===========================================================================
# VOLUME 2
# ===========================================================================

COMPONENTS["v2_ch1"] = [
    Component("Spatial index (geohash/quadtree)", "Turns 2D search into cell lookups",
        "Businesses are indexed by a spatial key. Geohash encodes lat/long into a "
        "string whose prefix length sets precision; nearby points share prefixes, "
        "so a radius search maps to a small set of neighboring cells. Quadtrees "
        "adapt cell size to density (deep in cities, shallow in deserts).\n\n"
        "*Trade-off:* geohash is simple and prefix-queryable but has fixed cells "
        "and boundary cases; quadtree/S2 adapt to density at more complexity."),
    Component("Location service (read path)", "Answers 'what's near me' queries",
        "Computes the covering cells for (point, radius), fetches candidate "
        "business ids from those cells, then applies an **exact haversine distance** "
        "filter and sorts. Read-heavy and stateless, replicated for scale."),
    Component("Geo cache + business DB", "Caches hot regions over static data",
        "Business data changes rarely and reads dominate, so index cells and "
        "business details are cached (Redis) with read replicas behind them. Dense-"
        "city queries repeat constantly and hit cache; the DB serves cold cells and "
        "the rare write."),
]

COMPONENTS["v2_ch2"] = [
    Component("WebSocket servers", "Stream location updates in real time",
        "Clients hold persistent WebSockets and push location every ~30s. This "
        "write-heavy stream (hundreds of thousands/sec) is the opposite of the "
        "static proximity service."),
    Component("Redis Pub/Sub fan-out", "Delivers a user's location to their friends",
        "Each update is published to the user's channel; friends' sessions "
        "subscribe and compute distance. Bounding fan-out to **friends** (not all "
        "users) keeps per-update cost tractable; the bus scales horizontally.\n\n"
        "*Trade-off:* pub/sub adds infrastructure to operate, but friend-bounding is "
        "what prevents an all-to-all explosion."),
    Component("Location cache (TTL) + history", "Ephemeral live positions, async durable history",
        "Live positions live in an in-memory cache with a short **TTL** — stop "
        "sharing and you expire off friends' maps quickly (a built-in privacy "
        "feature). Raw history is written asynchronously to a durable store off the "
        "hot path."),
]

COMPONENTS["v2_ch3"] = [
    Component("Tile service + CDN", "Serves pre-rendered map tiles",
        "The world is pre-rendered into image tiles per zoom level, keyed by "
        "(z,x,y), stored in object storage and served from the **CDN** — most tile "
        "requests never reach origin. Versioned tiles cache-bust cleanly.\n\n"
        "*Trade-off:* raster tiles are simple but storage-heavy; vector tiles are "
        "smaller/flexible but shift rendering to the client."),
    Component("Routing service (graph + CH)", "Computes shortest paths interactively",
        "The road network is a weighted graph. Plain Dijkstra is too slow at "
        "continent scale, so **contraction hierarchies** precompute shortcut edges "
        "for millisecond queries.\n\n"
        "*Trade-off:* fast queries at the cost of an expensive (periodic) rebuild "
        "when the graph changes."),
    Component("ETA + live-traffic pipeline", "Blends distance with current speeds",
        "ETA sums edge traversal times, where each edge's time uses its length and "
        "**current speed** from a streaming pipeline that ingests GPS probes every "
        "few minutes, with historical patterns filling sparse data.\n\n"
        "*Trade-off:* fresher traffic means better ETAs but a heavier pipeline."),
]

COMPONENTS["v2_ch4"] = [
    Component("Partitioned append-only log", "The core abstraction",
        "A topic splits into partitions, each an append-only log on disk written "
        "**sequentially** (the key to GB/s throughput). Producers append to a "
        "partition chosen by key, so messages for a key are ordered.\n\n"
        "*Decision:* ordering is guaranteed only **within a partition** — the "
        "deliberate trade that enables parallelism."),
    Component("Replication with ISR", "Durability via leader + followers",
        "Each partition has a leader and follower replicas. A write is committed "
        "once enough **in-sync replicas** acknowledge. `acks=all` is durable but "
        "slower; `acks=1` is faster with a small loss window on leader failure. "
        "Leader failover promotes an in-sync follower."),
    Component("Consumer groups + offsets", "Scalable, replayable consumption",
        "Partitions are divided among a group's members for parallel consumption. "
        "Each consumer commits an **offset**, so it can resume after a crash or "
        "**replay** from any point. Offsets decouple producers from consumers."),
]

COMPONENTS["v2_ch5"] = [
    Component("Collector (pull-based)", "Scrapes metrics from targets",
        "The collector **pulls** (scrapes) targets on a schedule, which gives "
        "central control and turns a failed scrape into a liveness signal. A push "
        "gateway handles short-lived jobs that may not exist at scrape time."),
    Component("Time-series DB", "Compression-optimized numeric store",
        "Recent samples stay in an in-memory head block for fast ingest/query; "
        "older data compresses into immutable blocks (delta-of-delta timestamps, "
        "XOR values → a couple of bytes/sample) and tiers to object storage.\n\n"
        "*Watch out:* high **label cardinality** explodes the number of series — "
        "the classic TSDB killer."),
    Component("Query service + downsampling", "Powers dashboards affordably",
        "Serves range queries for dashboards. Full resolution is kept for a short "
        "window, then **downsampled** (e.g. 5-minute aggregates) for long-term "
        "trends — the main cost lever."),
    Component("Alert manager", "Evaluates rules and routes notifications",
        "Continuously evaluates alert rules, then **deduplicates**, **groups** and "
        "applies silences/inhibition before routing, so a storm of related alerts "
        "doesn't spam responders.\n\n*Trade-off:* aggressive grouping reduces noise "
        "but can delay individual alerts."),
]

COMPONENTS["v2_ch6"] = [
    Component("Durable event log", "Ingests clicks reliably, partitioned",
        "Clicks land on a partitioned durable log (Kafka-style), partitioned by ad "
        "id so aggregation scales.\n\n*Watch out:* a viral ad creates a hot "
        "partition — salt/sub-partition the key."),
    Component("Stream aggregator", "Near-real-time per-minute counts",
        "Consumes the log and maintains per-minute per-ad counts for dashboards. "
        "Fast but can be slightly wrong around failures — which is why the batch "
        "path exists. Dedups on **event id** for effectively exactly-once counting; "
        "**watermarks** handle late/out-of-order events."),
    Component("Raw archive + batch reconciliation", "Billing-grade correctness",
        "Raw events are archived to cheap object storage. A periodic batch job "
        "recomputes counts from the immutable archive and **reconciles/corrects** "
        "the aggregated store. Billing reads these exact numbers.\n\n"
        "*Why both:* stream gives freshness, batch gives money-accurate correctness "
        "— a lambda-style architecture."),
]

COMPONENTS["v2_ch7"] = [
    Component("Search path (cached availability)", "Read-heavy discovery",
        "Search is served from caches/replicas of hotel and rate data and may be "
        "slightly stale — a room shown available might sell out by checkout. The "
        "booking transaction is the final authority."),
    Component("Reservation service (atomic inventory)", "Prevents overselling",
        "Booking runs an **atomic** check-and-decrement on the (room-type, date) "
        "inventory rows inside a transaction. Under a race for the last room, one "
        "request wins.\n\n*Choice:* **optimistic** concurrency (conditional update "
        "'decrement only if reserved < total', retry the loser) scales better than "
        "pessimistic locks."),
    Component("Idempotency layer", "Safe retries",
        "Each booking carries an **idempotency key** stored with the reservation, so "
        "a network-timeout retry returns the original result instead of creating a "
        "second reservation/charge."),
    Component("Reserve-then-confirm", "Holds inventory during payment",
        "Inventory is reserved first, then payment confirmed, with a **timeout** "
        "that releases abandoned holds so rooms aren't stuck."),
]

COMPONENTS["v2_ch8"] = [
    Component("SMTP send queue", "Reliable outbound delivery",
        "Outbound mail is queued and delivered to recipient servers with "
        "**exponential-backoff retries**, honoring greylisting, bouncing only after "
        "repeated failures. External servers are flaky, so send is a durable queue, "
        "not a synchronous call."),
    Component("Metadata store", "Fast mailbox/folder queries",
        "Small, frequently-queried metadata (from/to, subject, flags, body "
        "reference) lives in a store keyed by mailbox for fast folder listing and "
        "sorting."),
    Component("Object storage for bodies/attachments", "Cheap bulk storage",
        "Large, immutable bodies and attachments live in object storage referenced "
        "by metadata, with identical attachments deduplicated. Separating metadata "
        "from blobs lets each scale independently — the dominant cost is here, so "
        "old mail is tiered."),
    Component("Async search index", "Fast search without slowing writes",
        "A pipeline consumes new messages and updates a per-mailbox inverted index. "
        "Indexing **asynchronously** keeps delivery/reads fast.\n\n*Trade-off:* "
        "brand-new mail is briefly unsearchable."),
]

COMPONENTS["v2_ch9"] = [
    Component("API service", "Auth, routing, request handling",
        "Authenticates the PUT/GET/DELETE, then routes to the metadata and data "
        "planes. Objects are treated as **immutable** — 'edits' write new versions "
        "— which simplifies caching, replication and dedup and enables strong "
        "read-after-write."),
    Component("Metadata plane", "Records where each object lives",
        "A scalable, strongly-consistent store tracks each object's location, "
        "version, size and checksum. There are billions of objects, so this plane "
        "must itself shard and cache — it's a hard subsystem in its own right, kept "
        "separate from bulk bytes."),
    Component("Data plane (replication vs erasure coding)", "Durable byte storage",
        "Bytes are stored across many nodes spanning failure domains. **Replication** "
        "(3 copies) is simple and fast to repair but triples storage. **Erasure "
        "coding** (k data + m parity) tolerates m losses at only ~1.4x overhead — "
        "roughly half the cost — at the price of more CPU and slower reconstruction."),
    Component("Background scrubber", "Detects and repairs corruption",
        "Periodically verifies checksums to catch bit rot and rebuilds lost "
        "replicas/fragments, restoring the durability target after failures."),
]

COMPONENTS["v2_ch10"] = [
    Component("Redis sorted set", "O(log n) rank and top-N",
        "Scores live in a sorted set (ZSET). ZADD updates in O(log n); ZREVRANGE "
        "returns top-N; ZREVRANK gives a player's rank. This converts an "
        "O(n log n) sort-per-query into cheap logarithmic operations — the whole "
        "insight of the design.\n\n*Constraint:* the set is in-memory and volatile, "
        "so it must be backed by a durable store."),
    Component("Score service", "Applies updates to cache + DB",
        "On a score change it updates the sorted set (fast queries) and persists the "
        "authoritative score to the database (durability). Validates scores "
        "**server-side** — never trusting the client — as anti-cheat."),
    Component("Durable DB (source of truth)", "Recovery and reset",
        "The database is the source of truth; the sorted set is a derived view that "
        "can be rebuilt after a cache loss. It also supports periodic (daily/weekly) "
        "leaderboard resets."),
    Component("Sharding by score range", "Scales beyond one node",
        "At 100M+ players a single set may not fit; shard by score band across "
        "nodes. Global top-N merges the top of each shard; global rank sums counts "
        "below a score across shards."),
]

COMPONENTS["v2_ch11"] = [
    Component("Payment service + idempotency", "Exactly-once money movement",
        "Every request carries an **idempotency key**; a state machine advances the "
        "payment through pending → succeeded/failed. A retried request references "
        "the same payment rather than charging twice — delivering effectively "
        "exactly-once semantics despite timeouts and retries."),
    Component("Double-entry ledger", "The auditable source of truth",
        "Every money movement is recorded as two balanced entries (debit + credit), "
        "so the books always sum to zero and any balance is derivable from history. "
        "This makes the system auditable and makes bugs detectable (an imbalance = "
        "an error). The ledger — not the PSP response — is internal truth."),
    Component("PSP integration", "Moves real money externally",
        "External payment service providers actually move funds. Their calls are "
        "asynchronous and can fail or time out, so the system never assumes success "
        "and drives payments through explicit status states."),
    Component("Reconciliation job", "Closes the gap with reality",
        "Continuously pulls PSP statements and matches them to ledger entries, "
        "correcting mismatches (mark succeeded, refund a duplicate, flag for "
        "review).\n\n*Trade-off:* guarantees eventual correctness at the cost of a "
        "settlement delay — the right trade for money, which favors consistency "
        "over availability."),
]

COMPONENTS["v2_ch12"] = [
    Component("Command side (CQRS write)", "Validates and appends events",
        "The command side validates a transfer (sufficient funds, valid wallets) "
        "and appends **events** (debit A, credit B) rather than mutating a balance "
        "in place. Per-wallet writes are serialized (partition by wallet + expected-"
        "version check) so concurrent debits can't overspend."),
    Component("Event store (event sourcing)", "Append-only source of truth",
        "State is the fold over an append-only event log, giving a complete audit "
        "trail and **deterministic recovery** (replay events). Periodic snapshots "
        "avoid replaying from the beginning.\n\n*Trade-off:* more moving parts and "
        "eventual consistency between log and read model vs a simple UPDATE."),
    Component("Read model (CQRS query)", "Fast balance/history reads",
        "A materialized balance view is projected from events for fast reads, "
        "separate from the write path. Read-your-writes is honored where needed."),
    Component("Saga orchestrator", "Atomic cross-partition transfers",
        "When source and destination are on different partitions/services, a **saga** "
        "runs the transfer as steps with **compensating actions** on failure "
        "(refund A if crediting B fails), giving atomicity without fragile "
        "distributed two-phase commit."),
]

COMPONENTS["v2_ch13"] = [
    Component("Order gateway + sequencer", "Fairness and determinism",
        "Orders enter through gateways and pass through a single **sequencer** that "
        "assigns a total order. This guarantees **fairness** (strict arrival order) "
        "and **determinism** (replaying the sequenced input reproduces the exact "
        "book and trades).\n\n*Trade-off:* the sequencer is a throughput ceiling per "
        "stream, but it's the source of fairness and replayability."),
    Component("Matching engine (in-memory, single-writer)", "Microsecond matching",
        "Runs in memory with **one writer per symbol**, eliminating lock contention "
        "for predictable microsecond latency. It matches incoming orders against "
        "the order book by **price-time priority**. Partitioning by symbol scales "
        "throughput while preserving per-symbol ordering."),
    Component("Order book", "In-memory bids/asks",
        "A pair of price-sorted structures (bids descending, asks ascending, then by "
        "time). Matching pops the best opposing price and fills by time priority."),
    Component("Event log (log-before-match)", "No order loss, exact recovery",
        "Every input is persisted to an append-only log **before** matching, so a "
        "crash loses nothing and the exact book is rebuilt by replay (determinism "
        "guarantees identical reconstruction). Hot standbys consume the same log for "
        "fast failover.\n\n*Trade-off:* log-before-match adds latency but is "
        "non-negotiable for an exchange."),
    Component("Market data publisher", "Broadcasts trades and book updates",
        "Streams trades and order-book deltas to subscribers via efficient "
        "multicast/pub-sub."),
]
