"""
Deep, interview-grade content for Volume 2 (Chapters 1–13).

Volume 2 focuses on more specialized systems where identifying bottlenecks
and discussing trade-offs dominates. Same clarify-then-solve structure as
Volume 1. Content is original, paraphrased study material.
"""

from __future__ import annotations

from schema import (
    Chapter, ClarifyQ, Requirements, Estimation, EstimationRow,
    APIEndpoint, DataEntity, DeepDive, TradeoffTable, Component,
)

CHAPTERS: list[Chapter] = []

# ===========================================================================
# Chapter 1 — Proximity Service
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v2_ch1", number=1, volume=2,
    title="Proximity Service",
    tagline="Find nearby places within a radius, fast — the engine behind 'restaurants near me'.",
    diagram_id="v2_ch1",
    overview=(
        "A proximity service returns businesses near a location within a radius "
        "(think Yelp discovery). The hard part is turning 2D geospatial search into "
        "something a database can index and answer in milliseconds. The workload is "
        "**overwhelmingly read**, business data changes rarely, and the whole design "
        "hinges on the **spatial index** you choose (geohash, quadtree, or S2)."
    ),
    clarifying=[
        ClarifyQ("Functional scope",
                 "Search by radius, or return the k nearest regardless of distance?",
                 "Radius vs kNN changes the index query pattern and result bounding.",
                 "Radius search (e.g. within 5 km), with configurable radius."),
        ClarifyQ("Scale",
                 "How many businesses and how many searches/sec?",
                 "Read QPS drives caching/replicas; business count drives index granularity.",
                 "~200M businesses, ~5,000 searches/sec, heavy read skew to dense cities."),
        ClarifyQ("Data volatility",
                 "How often do businesses change location/details?",
                 "Rarely-changing data can be aggressively cached and precomputed.",
                 "Business data is near-static; updated infrequently."),
        ClarifyQ("Accuracy",
                 "Is approximate distance ranking acceptable, or exact great-circle?",
                 "Index gives candidates; exact distance filtering is a cheap final step.",
                 "Use the index for candidates, then exact haversine distance to filter/sort."),
    ],
    requirements=Requirements(
        functional=["Return businesses within a radius of a point", "Add/update/read business details"],
        non_functional=["Low-latency search (< ~100 ms)", "Scale reads massively",
                        "Handle dense-area hotspots", "High availability"],
        out_of_scope=["Ranking by rating/relevance (mention as extension)", "Routing/ETA"],
    ),
    estimation=Estimation(
        assumptions=["200M businesses", "5,000 searches/sec peak", "Each search touches a few index cells"],
        rows=[
            EstimationRow("Search QPS", "given", "~ 5,000 QPS"),
            EstimationRow("Business storage", "200M x ~1 KB", "~ 200 GB"),
            EstimationRow("Index cells (geohash-6)", "~1.2 km cells globally", "millions of cells"),
            EstimationRow("Cache hit target", "dense-area reuse", "> 90%"),
        ],
        notes=["Read-heavy + static data = cache almost everything; the DB is a fallback."],
    ),
    apis=[
        APIEndpoint("GET /v1/search?lat=&lng=&radius=", "Return businesses within the radius, sorted by distance."),
        APIEndpoint("GET /v1/business/{id}", "Fetch full business details."),
        APIEndpoint("POST /v1/business", "Add/update a business (rare write path).", "Reindex the affected cell."),
    ],
    data_model=[
        DataEntity("Business", ["id", "name", "lat", "lng", "geohash", "attributes"],
                   store="Relational/document DB for details; replicas for read scale."),
        DataEntity("Geo index", ["cell_id (geohash/quadtree) -> [business_id]"],
                   store="Index keyed by spatial cell; cached in Redis for hot regions."),
    ],
    high_level=(
        "Businesses are indexed by a **spatial key**. With **geohash**, each "
        "location becomes a string whose prefix length sets precision; nearby "
        "points share prefixes, so a radius search maps to a small set of "
        "neighboring cells. A search computes the covering cells for the radius, "
        "fetches candidate business ids from those cells, then applies an **exact "
        "haversine distance** filter and sorts. Because data is static and reads "
        "dominate, the index and hot results are **heavily cached**, with the "
        "database as a fallback for cold cells."
    ),
    request_flows=[
        "Search -> compute covering cells for (point, radius).",
        "Fetch candidate business ids from those cells (cache first).",
        "Exact-distance filter + sort candidates.",
        "Return details (hydrated from cache/replica).",
    ],
    deep_dives=[
        DeepDive("Spatial indexing: geohash vs quadtree vs S2",
                 "**Geohash** encodes lat/long into a string; fixed precision per length, "
                 "simple prefix queries, but cells don't adapt to density and there are "
                 "edge/boundary cases near cell borders. **Quadtree** recursively "
                 "subdivides space, adapting to density (deep in cities, shallow in "
                 "deserts) but is trickier to distribute. **Google S2** maps the sphere to "
                 "a space-filling curve of cells with good neighbor properties. Choice is "
                 "a trade-off of simplicity vs density-adaptivity.",
                 ["Geohash: simple, prefix-friendly, fixed cell size, boundary issues.",
                  "Quadtree: adapts to density, more complex to shard.",
                  "S2: strong geometry, more machinery to adopt."]),
        DeepDive("Handling dense-area hotspots",
                 "A search in Manhattan touches cells with thousands of businesses, while "
                 "a rural search touches almost none. Fixed-size geohash cells make dense "
                 "cells hot and heavy. Mitigations: finer precision in dense areas "
                 "(quadtree), capping results per cell, and caching the popular dense-city "
                 "queries which repeat constantly.",
                 ["Finer cells reduce per-cell load but increase index size and cross-cell queries."]),
        DeepDive("Read scalability & cost",
                 "The service is read-dominated over static data, so the cheapest, most "
                 "effective lever is caching: cache index cell -> ids and business details "
                 "in Redis, and use read replicas behind them. Writes are rare, so "
                 "reindexing on update is cheap. This keeps cost low — you're mostly "
                 "serving memory, not querying databases.",
                 ["Aggressive caching risks slightly stale business info — acceptable given low volatility."]),
        DeepDive("Reliability & security",
                 "Replicate the read path across AZs; the write path can tolerate brief "
                 "downtime since data is static. Validate and geofence write inputs, "
                 "rate-limit search to prevent scraping of the business dataset, and treat "
                 "user location as sensitive (don't log precise coordinates unnecessarily).",
                 ["Rate limiting protects the dataset but must not block legitimate heavy users."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Spatial index choice",
            ["Index", "Density-adaptive", "Distribute", "Complexity"],
            [["Geohash", "No (fixed cells)", "Easy (prefixes)", "Low"],
             ["Quadtree", "Yes", "Harder", "Medium"],
             ["S2 cells", "Yes", "Medium", "Medium-high"]],
        ),
    ],
    bottlenecks=[
        "Dense-city cells become hot — finer precision + caching + result caps.",
        "Search QPS on the DB — cache index and details, use replicas.",
        "Cell-boundary misses — query neighboring cells too.",
    ],
    security=[
        "Treat user coordinates as sensitive PII; minimize retention.",
        "Rate-limit search to deter dataset scraping.",
        "Validate write inputs (coordinates within valid ranges).",
    ],
    wrap_up=(
        "Proximity search is a spatial-indexing problem over static, read-heavy "
        "data. Pick an index (geohash for simplicity, quadtree/S2 for density), "
        "fetch candidates from covering cells, filter by exact distance, and cache "
        "aggressively. Dense-area hotspots are the main scaling challenge."
    ),
))

# ===========================================================================
# Chapter 2 — Nearby Friends
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v2_ch2", number=2, volume=2,
    title="Nearby Friends",
    tagline="Continuously show which friends are near you as everyone moves in real time.",
    diagram_id="v2_ch2",
    overview=(
        "Unlike the (mostly static) proximity service, Nearby Friends is "
        "**real-time and write-heavy**: every user's phone streams location "
        "updates every few seconds, and the system must compute, for each user, "
        "which friends are currently within a radius. The design revolves around "
        "**persistent connections**, a **publish/subscribe** fan-out, and a "
        "short-lived location cache."
    ),
    clarifying=[
        ClarifyQ("Functional scope",
                 "Only friends (bounded set), or any nearby user?",
                 "Friends bound the fan-out per update; arbitrary users is a far bigger search.",
                 "Only mutual friends, so each update fans out to a bounded subscriber set."),
        ClarifyQ("Update frequency",
                 "How often do clients report location?",
                 "Frequency times users sets the write QPS — the dominant load here.",
                 "Every ~30 seconds while the feature is active."),
        ClarifyQ("Scale",
                 "How many active users and average friends each?",
                 "Concurrent users drive connection count; friend count drives fan-out.",
                 "~10M concurrently active, ~200 friends average, ~hundreds nearby at most."),
        ClarifyQ("Freshness vs cost",
                 "How stale can a friend's location be?",
                 "Looser freshness lets you batch updates and cut load.",
                 "A few seconds of staleness is fine; we don't need per-second precision."),
    ],
    requirements=Requirements(
        functional=["Stream user location", "Notify user of friends within radius in real time"],
        non_functional=["Real-time (seconds) updates", "Handle write-heavy load",
                        "Scale to millions of concurrent users", "Bounded per-update fan-out"],
        out_of_scope=["Location history analytics (store async)", "Non-friend discovery"],
    ),
    estimation=Estimation(
        assumptions=["10M active users", "1 update / 30 s", "Avg 200 friends, ~100 nearby subscribers"],
        rows=[
            EstimationRow("Location write QPS", "10M / 30", "~ 333,000 updates/s"),
            EstimationRow("Fan-out messages/s", "333k x ~100 nearby", "~ 33M pushes/s"),
            EstimationRow("Concurrent connections", "10M", "10M WebSockets"),
            EstimationRow("Conn servers (~100k each)", "10M / 100k", "~ 100 servers"),
        ],
        notes=["Fan-out (tens of millions/sec) is the real load — Pub/Sub must scale horizontally."],
    ),
    apis=[
        APIEndpoint("WS /connect", "Persistent connection; client streams location, receives friend updates."),
        APIEndpoint("update_location(lat, lng)", "Sent over the socket every ~30s."),
        APIEndpoint("(push) friend_nearby(friend_id, distance)", "Server pushes when a friend enters/updates within radius."),
    ],
    data_model=[
        DataEntity("Live location", ["user_id", "lat", "lng", "updated_at"],
                   store="In-memory cache with short TTL (Redis) — ephemeral, hot."),
        DataEntity("Friend graph", ["user_id", "friend_id"],
                   store="KV/graph store; cached per active user."),
        DataEntity("Location history", ["user_id", "lat", "lng", "ts"],
                   store="Time-series/columnar store, written asynchronously."),
    ],
    high_level=(
        "Each client holds a **WebSocket** to a connection server. A location "
        "update is **published** to a channel for that user; the user's friends' "
        "sessions **subscribe** to it (via Redis Pub/Sub or a similar bus). A "
        "subscribing session computes distance and, if within radius, pushes a "
        "friend-nearby event to that friend's client. Current locations live in a "
        "**short-TTL cache** (stale entries simply expire), while raw history is "
        "written **asynchronously** to a durable store off the hot path."
    ),
    request_flows=[
        "Client streams location over WebSocket.",
        "Update published to the user's channel.",
        "Friends' subscribed sessions receive it, compute distance.",
        "If within radius -> push friend-nearby to that friend.",
        "History persisted asynchronously; live location cached with TTL.",
    ],
    deep_dives=[
        DeepDive("Real-time fan-out with Pub/Sub",
                 "The core challenge is fanning each location update out to the right "
                 "subscribers with low latency. A **pub/sub** bus decouples publishers "
                 "from subscribers and scales horizontally across connection servers. "
                 "Bounding fan-out to *friends* (not all users) keeps per-update cost "
                 "manageable; without that bound, 10M users would be an all-to-all "
                 "explosion.",
                 ["Pub/sub scales fan-out but adds a bus to operate and monitor.",
                  "Friend-bounding is what makes the fan-out tractable."]),
        DeepDive("Write-heavy load & the TTL cache",
                 "This is the mirror image of the proximity service: writes dominate. "
                 "Storing every update durably on the hot path would crush the database, "
                 "so live locations go into an **in-memory cache with a short TTL** — if a "
                 "user stops updating, their location simply expires and they drop off "
                 "friends' maps. Durable history is written asynchronously in batches.",
                 ["TTL cache is cheap and self-cleaning but loses precise history unless persisted separately."]),
        DeepDive("Connection management & scale",
                 "Millions of persistent connections spread across ~100 connection "
                 "servers. Subscriptions must follow users as they reconnect to different "
                 "servers, so the pub/sub layer routes by user id, not by connection. "
                 "Batching and coarsening update frequency (e.g. skip near-identical "
                 "positions) cuts both write and fan-out volume.",
                 ["Coarser updates save load but reduce location precision."]),
        DeepDive("Privacy & security",
                 "Continuous location is highly sensitive. Enforce mutual-friend "
                 "authorization on every subscription, let users disable sharing "
                 "instantly (TTL means they vanish quickly), minimize history retention, "
                 "and encrypt data in transit and at rest. Never leak exact coordinates "
                 "to non-friends.",
                 ["Short TTL doubles as a privacy feature — stop sharing and you disappear fast."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Location handling",
            ["Concern", "Approach", "Trade-off"],
            [["Live location", "Short-TTL in-memory cache", "Ephemeral, self-cleaning"],
             ["History", "Async durable write", "Slight delay, off hot path"],
             ["Fan-out", "Friend-bounded pub/sub", "Bounded cost vs all-to-all"]],
        ),
    ],
    bottlenecks=[
        "Fan-out volume (tens of millions/sec) — horizontal pub/sub, friend-bounding.",
        "Connection-server capacity — shard users, plan reconnect storms.",
        "Write QPS to history — async batching, coarsen update rate.",
    ],
    security=[
        "Mutual-friend authorization on every subscription.",
        "Instant sharing opt-out (leveraged by short TTL).",
        "Minimize and encrypt location history; treat as sensitive PII.",
    ],
    wrap_up=(
        "Nearby Friends is a real-time, write-heavy fan-out system: persistent "
        "connections, friend-bounded pub/sub, a short-TTL live-location cache, and "
        "async history. The scaling story is fan-out volume and connection count; "
        "the TTL cache elegantly handles both freshness and privacy."
    ),
))

# ===========================================================================
# Chapter 3 — Google Maps
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v2_ch3", number=3, volume=2,
    title="Google Maps",
    tagline="Serve map tiles, locate users, and compute routes with ETAs at planet scale.",
    diagram_id="v2_ch3",
    overview=(
        "A maps platform is really three subsystems: **map rendering** (serving "
        "tiles), **location/geocoding**, and **routing with ETAs** over a global "
        "road network. Tiles are massively cacheable and CDN-served; routing is a "
        "graph problem where precomputation makes interactive shortest-path queries "
        "possible; ETAs blend distance with live traffic."
    ),
    clarifying=[
        ClarifyQ("Functional scope",
                 "Tiles + routing + ETA, or also search, Street View, live navigation?",
                 "Each is a large subsystem; scoping keeps the design focused.",
                 "Map tiles, user location, routing and ETA (turn-by-turn as extension)."),
        ClarifyQ("Scale",
                 "How many map/tile requests and route requests per second?",
                 "Tile load is huge but cacheable; routing is compute-heavy per request.",
                 "Billions of tile requests/day; millions of route requests/day."),
        ClarifyQ("Freshness",
                 "How current must traffic/ETA be? How often does the road graph change?",
                 "Traffic needs near-real-time; the base graph changes slowly.",
                 "Traffic every few minutes; road graph updated periodically (batch)."),
        ClarifyQ("Accuracy vs latency",
                 "Is a near-optimal route acceptable if it's faster to compute?",
                 "Precomputation (contraction hierarchies) trades build time for fast, near-optimal queries.",
                 "Fast, near-optimal routes using precomputed shortcuts."),
    ],
    requirements=Requirements(
        functional=["Render map tiles", "Locate/geocode the user", "Compute routes and ETAs"],
        non_functional=["Interactive latency", "Global scale via CDN",
                        "Near-real-time traffic in ETA", "High availability"],
        out_of_scope=["Street View", "Places search ranking", "Offline maps"],
    ),
    estimation=Estimation(
        assumptions=["1B tile requests/day", "Tiles ~ tens of KB", "5M route requests/day"],
        rows=[
            EstimationRow("Tile QPS", "1B / 86,400", "~ 11,600 QPS (mostly CDN)"),
            EstimationRow("Route QPS", "5M / 86,400", "~ 58 QPS (compute-heavy)"),
            EstimationRow("Tile storage", "planet x zoom levels", "PB-scale, pre-rendered"),
            EstimationRow("Road graph", "~ hundreds of millions of edges", "fits sharded in memory"),
        ],
        notes=["Tiles dominate volume but are cacheable; routing dominates compute per request."],
    ),
    apis=[
        APIEndpoint("GET /tiles/{z}/{x}/{y}.png", "Return a pre-rendered map tile (served from CDN)."),
        APIEndpoint("GET /v1/geocode?q=", "Resolve an address/place to coordinates."),
        APIEndpoint("GET /v1/route?from=&to=", "Return route geometry + ETA."),
    ],
    data_model=[
        DataEntity("Map tile", ["(z, x, y)", "rendered image"],
                   store="Object storage + CDN; highly cacheable, immutable per version."),
        DataEntity("Road graph", ["nodes (intersections)", "edges (roads, weights, restrictions)"],
                   store="Sharded graph store, loaded into memory on routing servers."),
        DataEntity("Traffic", ["edge_id", "current speed", "updated_at"],
                   store="Fast store updated by a streaming pipeline every few minutes."),
    ],
    high_level=(
        "**Tiles:** the world is pre-rendered into image tiles per zoom level, keyed "
        "by (z, x, y), stored in object storage and served from the **CDN** — most "
        "requests never reach origin. **Location:** a geocoding service converts "
        "addresses to coordinates. **Routing:** the road network is a weighted "
        "**graph**; a routing service runs shortest-path (Dijkstra/A*) accelerated "
        "by **precomputed shortcuts** (contraction hierarchies) so queries return in "
        "milliseconds. **ETA** combines edge distances with **live traffic** speeds "
        "updated by a streaming pipeline."
    ),
    request_flows=[
        "Pan/zoom -> fetch tiles by (z,x,y) from CDN edge.",
        "Search -> geocode to coordinates.",
        "Route -> routing service runs A*/CH over the graph.",
        "ETA -> combine edge weights with live traffic speeds.",
    ],
    deep_dives=[
        DeepDive("Map tiles & CDN",
                 "Pre-rendering tiles turns map display into static file serving — cheap, "
                 "cacheable, and edge-served. Tiles are versioned so a map data update "
                 "cache-busts cleanly. Vector tiles (rendered client-side) reduce storage "
                 "and allow styling but shift compute to the device. The CDN is what makes "
                 "billions of tile requests affordable.",
                 ["Raster tiles: simple, storage-heavy.",
                  "Vector tiles: smaller/flexible, client compute."]),
        DeepDive("Routing at scale",
                 "Plain Dijkstra over a continent-sized graph is too slow interactively. "
                 "**Contraction hierarchies** precompute shortcut edges so queries explore "
                 "far fewer nodes, giving millisecond routes at the cost of a heavy "
                 "one-time (periodic) build. The graph is partitioned across servers; a "
                 "route request may cross partitions, handled with boundary nodes.",
                 ["Precomputed shortcuts: fast queries, expensive rebuilds when the graph changes."]),
        DeepDive("ETA & live traffic",
                 "ETA = sum of edge traversal times, where each edge's time comes from its "
                 "length and **current speed**. A streaming pipeline ingests GPS probes "
                 "and updates per-edge speeds every few minutes. Historical patterns fill "
                 "in where live data is sparse. This is where accuracy and freshness "
                 "trade against pipeline cost.",
                 ["Fresher traffic: better ETAs, heavier ingestion pipeline."]),
        DeepDive("Scalability, cost & security",
                 "Tiles scale via CDN; routing scales by sharding the graph and caching "
                 "popular routes. Cost is dominated by tile storage/bandwidth (mitigated "
                 "by CDN caching and vector tiles) and traffic ingestion. Protect user "
                 "trajectories as sensitive data, and rate-limit routing to prevent abuse "
                 "of the expensive compute path.",
                 ["Caching popular routes cuts compute but can serve slightly stale ETAs."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Subsystem strategies",
            ["Subsystem", "Key technique", "Trade-off"],
            [["Tiles", "Pre-render + CDN", "Storage vs client compute (vector)"],
             ["Routing", "Contraction hierarchies", "Fast queries vs rebuild cost"],
             ["ETA", "Streaming traffic", "Freshness vs pipeline cost"]],
        ),
    ],
    bottlenecks=[
        "Routing compute — precompute shortcuts, cache popular routes.",
        "Tile origin load — maximize CDN hit ratio, use vector tiles.",
        "Traffic ingestion volume — sample probes, aggregate per edge.",
    ],
    security=[
        "Treat GPS trajectories as sensitive PII; minimize retention.",
        "Rate-limit the expensive routing endpoint.",
        "Serve tiles/routes over HTTPS; sign premium API access.",
    ],
    wrap_up=(
        "Maps decomposes into tiles (CDN-served static files), geocoding, and graph "
        "routing accelerated by precomputed shortcuts, with ETAs from a live-traffic "
        "stream. Tiles scale by caching; routing scales by precomputation and "
        "sharding. The trade-offs are freshness vs pipeline cost and query speed vs "
        "rebuild cost."
    ),
))


# ===========================================================================
# Chapter 4 — Distributed Message Queue
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v2_ch4", number=4, volume=2,
    title="Distributed Message Queue",
    tagline="A durable, partitioned, ordered log — the Kafka-style backbone of async systems.",
    diagram_id="v2_ch4",
    overview=(
        "A distributed message queue decouples producers from consumers, absorbs "
        "spikes, and enables event-driven architectures. The reference design is a "
        "**partitioned, append-only log** with **replication** for durability, "
        "**ordering within a partition**, and **consumer groups** tracking offsets "
        "so consumers can scale out and replay. Understanding these four ideas is "
        "the whole chapter."
    ),
    clarifying=[
        ClarifyQ("Delivery semantics",
                 "At-least-once, at-most-once, or exactly-once?",
                 "This drives ack/offset handling and dedup requirements.",
                 "At-least-once by default; exactly-once via idempotent consumers where needed."),
        ClarifyQ("Ordering",
                 "Is global ordering required, or per-key/partition enough?",
                 "Global ordering kills parallelism; per-partition ordering is the norm.",
                 "Ordering within a partition (by key); no global order."),
        ClarifyQ("Durability & retention",
                 "How long are messages retained, and can consumers replay?",
                 "Retention + replay make the log a source of truth, not just a buffer.",
                 "Retain for days; consumers can replay from any offset."),
        ClarifyQ("Scale",
                 "Throughput and message size?",
                 "High throughput needs many partitions and sequential-IO storage.",
                 "Millions of messages/sec, KB-scale messages."),
    ],
    requirements=Requirements(
        functional=["Publish/subscribe by topic", "Consumer groups", "Offset tracking & replay"],
        non_functional=["High throughput", "Durability via replication",
                        "Ordering within partitions", "Horizontal scalability"],
        out_of_scope=["Stream processing framework (built on top)"],
    ),
    estimation=Estimation(
        assumptions=["1M messages/sec", "Message ~ 1 KB", "Replication factor 3", "Retain 3 days"],
        rows=[
            EstimationRow("Ingest throughput", "1M x 1 KB", "~ 1 GB/s"),
            EstimationRow("With replication", "1 GB/s x 3", "~ 3 GB/s write IO"),
            EstimationRow("Storage for 3 days", "1 GB/s x 86,400 x 3", "~ 260 TB (x3 replicas)"),
            EstimationRow("Partitions (for parallelism)", "throughput / per-partition limit", "hundreds-thousands"),
        ],
        notes=["Sequential append IO is the key to hitting GB/s on commodity disks."],
    ),
    apis=[
        APIEndpoint("produce(topic, key, value)", "Append a message; key determines the partition."),
        APIEndpoint("subscribe(topic, group)", "Join a consumer group; partitions are assigned to members."),
        APIEndpoint("commit(offset)", "Record consumption progress for replay/resume."),
    ],
    data_model=[
        DataEntity("Partition (log)", ["append-only sequence of (offset, key, value, ts)"],
                   store="Segmented files on disk, written sequentially; replicated to followers."),
        DataEntity("Consumer offset", ["group", "topic", "partition", "committed_offset"],
                   store="Durable offset store (internal topic or metadata store)."),
    ],
    high_level=(
        "A **topic** is split into **partitions**, each an **append-only log** on "
        "disk. Producers append to a partition chosen by the message key (so all "
        "messages for a key are ordered). Each partition has a **leader** and "
        "**follower replicas**; a write is durable once enough in-sync replicas "
        "acknowledge it. **Consumer groups** divide partitions among members for "
        "parallel consumption, and each consumer tracks an **offset** it commits, "
        "enabling resume and replay. Sequential disk IO + the OS page cache is what "
        "makes throughput enormous."
    ),
    request_flows=[
        "Producer -> partition (by key) -> leader appends -> replicated to followers.",
        "Write acked when in-sync replicas confirm.",
        "Consumer group members each own some partitions and pull sequentially.",
        "Consumers commit offsets; can rewind to replay.",
    ],
    deep_dives=[
        DeepDive("The append-only log & ordering",
                 "The append-only log is the core abstraction: writes are sequential "
                 "(fast), and each message gets a monotonic **offset** within its "
                 "partition. Ordering is guaranteed **only within a partition** — that's "
                 "the deliberate trade that enables parallelism. Route related messages to "
                 "the same partition (by key) when you need them ordered.",
                 ["Per-partition ordering enables parallelism; global ordering would serialize everything."]),
        DeepDive("Durability & replication",
                 "Each partition is replicated to N nodes. A configurable number of "
                 "**in-sync replicas (ISR)** must acknowledge a write before it's "
                 "considered committed — more acks means stronger durability but higher "
                 "write latency. Leader failover promotes an in-sync follower, so a node "
                 "loss doesn't lose committed data.",
                 ["acks=all: durable, slower.",
                  "acks=1: faster, small loss window on leader failure."]),
        DeepDive("Delivery semantics",
                 "Default is **at-least-once**: a consumer may reprocess messages after a "
                 "crash before committing an offset. **Exactly-once** requires idempotent "
                 "producers (dedup by sequence) and transactional writes, or idempotent "
                 "consumers keyed on message id. **At-most-once** commits before "
                 "processing and can drop messages.",
                 ["At-least-once + idempotent consumers is the pragmatic exactly-once."]),
        DeepDive("Scalability, cost & security",
                 "Add partitions to add parallelism, and add brokers to add capacity; "
                 "consumer groups scale up to the partition count. Retention length "
                 "directly sets storage cost — tune it or tier old segments to cheap "
                 "storage. Secure with per-topic ACLs, TLS between clients and brokers, "
                 "and encryption at rest.",
                 ["More partitions: more parallelism, more metadata and rebalancing cost.",
                  "Longer retention: more replay ability, more storage cost."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Durability vs latency (acks)",
            ["Setting", "Durability", "Write latency"],
            [["acks=all (ISR)", "Strongest", "Higher"],
             ["acks=1 (leader)", "Moderate", "Low"],
             ["acks=0", "Weakest", "Lowest"]],
        ),
    ],
    bottlenecks=[
        "Hot partition (skewed key) — rekey or increase partitions.",
        "Consumer lag — scale consumers up to partition count; investigate slow processing.",
        "Rebalancing storms when members change — use cooperative rebalancing.",
        "Disk throughput — rely on sequential IO; add brokers.",
    ],
    security=[
        "Per-topic ACLs for produce/consume.",
        "TLS in transit; encryption at rest.",
        "Quotas per client to prevent noisy-neighbor overload.",
    ],
    wrap_up=(
        "A distributed message queue is a replicated, partitioned append-only log. "
        "Partitions give parallelism and per-partition ordering; replication with "
        "ISR gives tunable durability; consumer groups and offsets give scalable, "
        "replayable consumption. Tune acks, partitions and retention to balance "
        "durability, throughput and cost."
    ),
))

# ===========================================================================
# Chapter 5 — Metrics Monitoring and Alerting System
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v2_ch5", number=5, volume=2,
    title="Metrics Monitoring and Alerting System",
    tagline="Ingest, store, query and alert on time-series metrics at scale (Prometheus-style).",
    diagram_id="v2_ch5",
    overview=(
        "A monitoring system collects metrics from thousands of sources, stores "
        "them efficiently as **time series**, powers dashboards, and fires alerts "
        "when rules trigger. The design decisions are the **collection model** "
        "(pull vs push), a **time-series database** tuned for append-heavy numeric "
        "data, and **retention/downsampling** to keep storage affordable."
    ),
    clarifying=[
        ClarifyQ("Data type",
                 "Metrics only, or also logs and traces?",
                 "Logs/traces are different systems (high-cardinality text vs numeric series).",
                 "Numeric time-series metrics; logs/traces out of scope."),
        ClarifyQ("Scale",
                 "How many metrics/series and at what resolution?",
                 "Cardinality x resolution x retention sets storage and ingest load.",
                 "~10M active series, 10s resolution, thousands of sources."),
        ClarifyQ("Collection model",
                 "Pull from targets or have targets push?",
                 "Pull gives central control and health visibility; push suits ephemeral jobs.",
                 "Pull-based scraping, with a push gateway for short-lived jobs."),
        ClarifyQ("Retention",
                 "How long at full resolution, and can we downsample old data?",
                 "Full-resolution forever is unaffordable; downsampling is essential.",
                 "Full resolution ~2 weeks, downsampled for long-term."),
    ],
    requirements=Requirements(
        functional=["Ingest metrics", "Store time series", "Query for dashboards", "Evaluate alert rules"],
        non_functional=["High ingest throughput", "Fast range queries",
                        "Affordable long-term storage", "Reliable alerting"],
        out_of_scope=["Log aggregation", "Distributed tracing"],
    ),
    estimation=Estimation(
        assumptions=["10M active series", "1 sample / 10 s", "Each sample ~ 16 bytes compressed"],
        rows=[
            EstimationRow("Ingest rate", "10M / 10 s", "~ 1M samples/s"),
            EstimationRow("Raw bytes/s", "1M x 16 B", "~ 16 MB/s"),
            EstimationRow("Storage / day (compressed)", "16 MB/s x 86,400", "~ 1.3 TB/day"),
            EstimationRow("With downsampling", "old data aggregated", "far less long-term"),
        ],
        notes=["Time-series compression (delta-of-delta, XOR) shrinks samples to a few bytes each."],
    ),
    apis=[
        APIEndpoint("(scrape) GET /metrics on targets", "Collector pulls metrics from each target periodically."),
        APIEndpoint("POST /push (gateway)", "Short-lived jobs push metrics to a gateway that's then scraped."),
        APIEndpoint("GET /api/query?expr=&range=", "Query time series for dashboards."),
    ],
    data_model=[
        DataEntity("Time series", ["series_id = metric + labels", "sequence of (timestamp, value)"],
                   store="Time-series DB: recent data in memory, compressed blocks on disk/object storage."),
        DataEntity("Alert rule", ["expression", "threshold", "for-duration", "routing"],
                   store="Config store, evaluated by the alert engine."),
    ],
    high_level=(
        "A **collector** gathers metrics — primarily by **pulling** (scraping) "
        "targets on a schedule, with a **push gateway** for ephemeral jobs. Samples "
        "are written to a **time-series database** optimized for append-heavy "
        "numeric data: recent points stay in memory for fast writes/queries, then "
        "compress into immutable blocks on disk and eventually object storage. A "
        "**query service** powers dashboards, and an **alert engine** continuously "
        "evaluates rules over the data, deduplicating and routing notifications "
        "through an alert manager."
    ),
    request_flows=[
        "Collector scrapes targets (or reads push gateway).",
        "Samples appended to the TSDB (memory -> compressed blocks).",
        "Dashboards query ranges via the query service.",
        "Alert engine evaluates rules; alert manager dedupes and routes.",
    ],
    deep_dives=[
        DeepDive("Pull vs push collection",
                 "**Pull** (scrape) lets the system control scrape frequency, detect a "
                 "target being down (a failed scrape is itself a signal), and discover "
                 "targets via service discovery. **Push** suits short-lived/batch jobs "
                 "that may not exist when a scrape happens. Most systems are pull-first "
                 "with a push gateway for the exceptions.",
                 ["Pull: central control + down-detection, but needs reachability to targets.",
                  "Push: works for ephemeral jobs, but you lose easy liveness detection."]),
        DeepDive("Time-series storage & compression",
                 "TSDBs exploit the shape of the data: timestamps advance regularly and "
                 "values change slowly, so **delta-of-delta** timestamp encoding and "
                 "**XOR** value compression shrink each sample to a couple of bytes. "
                 "Recent data lives in an in-memory head block for fast ingest/query; "
                 "older data is written as immutable compressed blocks.",
                 ["High label cardinality explodes the number of series — the classic TSDB killer."]),
        DeepDive("Retention & downsampling (cost)",
                 "Keeping every 10-second sample forever is unaffordable. Keep full "
                 "resolution for a short window, then **downsample** (e.g. to 5-minute "
                 "aggregates) for long-term trends, and tier cold blocks to object "
                 "storage. This is the main cost lever and a common interview follow-up.",
                 ["Downsampling saves storage but loses fine-grained history for old periods."]),
        DeepDive("Reliable alerting",
                 "Alerts must fire even during partial outages and must not spam. The "
                 "**alert manager** deduplicates identical alerts, **groups** related "
                 "ones, applies silences/inhibition, and routes to the right channel. "
                 "Rule evaluation should be resilient so a single bad rule or missing "
                 "data doesn't suppress everything.",
                 ["Aggressive grouping reduces noise but can delay or hide individual alerts."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Storage tiers",
            ["Tier", "Resolution", "Cost", "Use"],
            [["In-memory head", "Full", "High", "Recent ingest/query"],
             ["Compressed blocks", "Full", "Medium", "Weeks of history"],
             ["Downsampled/object", "Aggregated", "Low", "Long-term trends"]],
        ),
    ],
    bottlenecks=[
        "Label cardinality explosion — limit/normalize labels.",
        "Ingest throughput — shard the TSDB by series.",
        "Expensive dashboard queries — precompute/recording rules, cache.",
        "Alert-rule evaluation load — scale the evaluator, shard rules.",
    ],
    security=[
        "Authn/authz on query and admin APIs.",
        "Protect metrics that may reveal sensitive business data.",
        "TLS for scrape and query traffic.",
    ],
    wrap_up=(
        "Monitoring is an ingest-and-query time-series system: pull-based collection, "
        "a compression-heavy TSDB with tiered storage, downsampling for cost, and a "
        "dedup/grouping alert manager. Cardinality control and retention/downsampling "
        "are the decisive scaling and cost levers."
    ),
))


# ===========================================================================
# Chapter 6 — Ad Click Event Aggregation
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v2_ch6", number=6, volume=2,
    title="Ad Click Event Aggregation",
    tagline="Count billions of ad clicks accurately and near-real-time for billing and dashboards.",
    diagram_id="v2_ch6",
    overview=(
        "Ad click aggregation counts click events, grouped by ad and time window, "
        "for **billing** and **dashboards**. Because it drives money, **accuracy** "
        "is paramount — you cannot over- or under-count — yet advertisers want "
        "**near-real-time** numbers. The design uses a fast **stream** path for "
        "fresh counts and a slower **batch** path to reconcile and guarantee "
        "correctness, plus careful handling of **duplicates** and **late events**."
    ),
    clarifying=[
        ClarifyQ("Accuracy vs latency",
                 "Which matters more — exact counts or instant numbers?",
                 "Money demands exactness; a stream+batch (lambda-style) design serves both.",
                 "Near-real-time approximate, reconciled to exact by batch for billing."),
        ClarifyQ("Aggregation granularity",
                 "Per-minute, per-ad? Any other dimensions (region, campaign)?",
                 "Dimensions multiply the number of aggregation keys and storage.",
                 "Per-minute per-ad, with a few extra dimensions."),
        ClarifyQ("Scale",
                 "How many click events per second?",
                 "Volume decides partitioning of the stream and storage sizing.",
                 "~1M clicks/sec peak, billions/day."),
        ClarifyQ("Correctness hazards",
                 "How do we handle duplicate clicks and late/out-of-order events?",
                 "Dedup and windowing/watermarks are essential for money-grade accuracy.",
                 "Dedup by event id; use watermarks + reprocessing for late events."),
    ],
    requirements=Requirements(
        functional=["Ingest click events", "Aggregate per-minute per-ad", "Serve counts to dashboards & billing"],
        non_functional=["Accurate (billing-grade)", "Near-real-time", "Scalable to millions/sec",
                        "Fault-tolerant / reprocessable"],
        out_of_scope=["Fraud detection modeling (mention as security)", "Ad serving itself"],
    ),
    estimation=Estimation(
        assumptions=["1M clicks/sec peak", "Event ~ 100 bytes", "Retain raw 30 days"],
        rows=[
            EstimationRow("Ingest rate", "1M x 100 B", "~ 100 MB/s"),
            EstimationRow("Raw storage / day", "100 MB/s x 86,400", "~ 8.6 TB/day"),
            EstimationRow("Aggregated rows/min", "# ads x dimensions", "far smaller than raw"),
            EstimationRow("Raw for 30 days", "8.6 TB x 30", "~ 260 TB"),
        ],
        notes=["Store raw events cheaply (object storage) so batch can recompute exact numbers."],
    ),
    apis=[
        APIEndpoint("(ingest) click events -> log", "Clicks land on a partitioned durable log (message queue)."),
        APIEndpoint("GET /v1/stats?ad_id=&from=&to=", "Return aggregated counts for dashboards/billing."),
    ],
    data_model=[
        DataEntity("Raw click event", ["event_id", "ad_id", "user/context", "timestamp"],
                   store="Durable log + archived to object storage (cold, for reconciliation)."),
        DataEntity("Aggregated count", ["ad_id", "minute", "dimensions", "count"],
                   store="Aggregation DB (fast reads for dashboards/billing)."),
    ],
    high_level=(
        "Clicks are written to a **partitioned durable log** (a message queue). A "
        "**stream aggregator** consumes the log and maintains **per-minute per-ad** "
        "counts, giving near-real-time numbers to dashboards. In parallel, raw "
        "events are **archived** to cheap object storage. A periodic **batch job** "
        "recomputes counts from the raw archive and **reconciles** the aggregated "
        "store — correcting for duplicates, late events, or stream failures. Billing "
        "reads the reconciled, exact numbers; dashboards can read the fast stream "
        "numbers."
    ),
    request_flows=[
        "Click -> durable partitioned log.",
        "Stream aggregator -> per-minute counts -> aggregation DB (fast, approximate).",
        "Raw events archived to object storage.",
        "Batch job recomputes from raw -> reconciles/corrects aggregation DB (exact).",
    ],
    deep_dives=[
        DeepDive("Stream + batch (why both)",
                 "The stream path is fast but can be wrong (a crash may double- or "
                 "under-count around the failure). The batch path is slow but "
                 "authoritative because it recomputes from the immutable raw archive. "
                 "Running both — a **lambda-style** architecture — gives fresh numbers "
                 "for dashboards and exact numbers for billing. The raw archive is the "
                 "safety net that makes correctness recoverable.",
                 ["Stream only: fast but not billing-safe.",
                  "Batch only: exact but not real-time.",
                  "Both: complexity for freshness + correctness."]),
        DeepDive("Exactly-once & deduplication",
                 "Because it's money, you must avoid double counting. Each click carries "
                 "a unique **event id**; aggregators dedup on it (e.g. via a keyed store "
                 "or idempotent updates). Combined with **checkpointed offsets**, this "
                 "gives effectively exactly-once aggregation even across restarts.",
                 ["Dedup state costs memory/storage but is non-negotiable for billing."]),
        DeepDive("Late & out-of-order events",
                 "Mobile clients report clicks late (offline, retries). **Watermarks** "
                 "let the stream decide when a minute-window is 'closed enough' to emit, "
                 "while still allowing the batch job to fold in stragglers and correct the "
                 "window. Without this, late events silently corrupt the counts.",
                 ["Longer watermark delays: fewer corrections but more result latency."]),
        DeepDive("Scalability, cost & security",
                 "Partition the log by ad id (or a composite key) so aggregation scales "
                 "horizontally; watch for hot ads (a viral campaign) creating skewed "
                 "partitions. Raw retention in object storage is the main cost — keep it "
                 "long enough to reconcile and audit. Fraud/invalid-click filtering "
                 "protects both advertisers and revenue integrity.",
                 ["Longer raw retention: better auditability, more storage cost.",
                  "Hot ads skew partitions — sub-partition or salt the key."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Freshness vs correctness",
            ["Path", "Freshness", "Correctness", "Consumer"],
            [["Stream", "Seconds", "Approximate", "Dashboards"],
             ["Batch reconcile", "Hours", "Exact", "Billing"],
             ["Combined (lambda)", "Both", "Both", "Everyone"]],
        ),
    ],
    bottlenecks=[
        "Hot ad partitions — salt/sub-partition the key.",
        "Dedup state size — window it and offload to a fast store.",
        "Batch recompute time — incremental reconciliation over recent windows.",
    ],
    security=[
        "Filter fraudulent/invalid clicks to protect revenue and advertisers.",
        "Immutable raw archive for audit and dispute resolution.",
        "Access controls on billing-grade aggregates.",
    ],
    wrap_up=(
        "Ad click aggregation pairs a fast stream path (fresh, approximate) with a "
        "batch reconciliation path (exact, billing-grade) over an immutable raw "
        "archive, using event-id dedup and watermarks for correctness. The archive "
        "is what makes money-accurate counts recoverable; hot ads and late events "
        "are the main hazards."
    ),
))

# ===========================================================================
# Chapter 7 — Hotel Reservation System
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v2_ch7", number=7, volume=2,
    title="Hotel Reservation System",
    tagline="Search availability and book rooms without ever overselling.",
    diagram_id="v2_ch7",
    overview=(
        "A hotel reservation system lets users search availability and reserve "
        "rooms. It looks CRUD-simple, but the crux is **concurrency correctness**: "
        "under simultaneous bookings for the last room, the system must never "
        "**oversell**. That single constraint drives the choice of transactions, "
        "concurrency control, and idempotent booking."
    ),
    clarifying=[
        ClarifyQ("Functional scope",
                 "Search + book + cancel? Dynamic pricing? Payments in scope?",
                 "Payments and pricing are large adjacent systems; booking correctness is the core.",
                 "Search, reserve, cancel; treat pricing/payment as separate services."),
        ClarifyQ("Consistency",
                 "Is overbooking ever acceptable (airline-style), or strictly never?",
                 "This decides how strict the inventory transaction must be.",
                 "Never oversell — inventory updates must be atomic and correct."),
        ClarifyQ("Scale",
                 "How many hotels/rooms and booking QPS?",
                 "Read (search) QPS dwarfs write (book) QPS, shaping caching vs transaction design.",
                 "~1M hotels; search QPS high, booking QPS modest but contended on hot dates."),
        ClarifyQ("Retries",
                 "How do we handle client retries and double-submits?",
                 "Without idempotency, a retry can create duplicate reservations/charges.",
                 "Idempotency keys so a retried booking is applied once."),
    ],
    requirements=Requirements(
        functional=["Search availability & rates", "Reserve a room", "Cancel a reservation"],
        non_functional=["Never oversell (strong consistency on inventory)",
                        "Scale search reads", "Idempotent, safe retries", "High availability"],
        out_of_scope=["Dynamic pricing engine", "Payment processing internals"],
    ),
    estimation=Estimation(
        assumptions=["1M hotels, avg 100 rooms", "Search:book ratio ~ 1000:1"],
        rows=[
            EstimationRow("Room-inventory rows", "1M x 100 x dates", "billions of (room-type, date) rows"),
            EstimationRow("Search QPS", "read-heavy", "tens of thousands QPS"),
            EstimationRow("Booking QPS", "search/1000", "tens QPS, spiky on hot dates"),
        ],
        notes=["Contention concentrates on popular hotels/dates — that's where correctness is tested."],
    ),
    apis=[
        APIEndpoint("GET /v1/search?location=&checkin=&checkout=", "Return available hotels/room types with rates."),
        APIEndpoint("POST /v1/reservations", "Reserve a room; requires an idempotency key.", "Atomic inventory decrement."),
        APIEndpoint("DELETE /v1/reservations/{id}", "Cancel; returns inventory."),
    ],
    data_model=[
        DataEntity("Room inventory", ["hotel_id", "room_type", "date", "total", "reserved"],
                   store="Relational DB with transactions; the source of truth for availability."),
        DataEntity("Reservation", ["id", "user_id", "hotel_id", "room_type", "dates", "status", "idempotency_key"],
                   store="Relational DB, transactional with inventory update."),
    ],
    high_level=(
        "**Search** is read-heavy and served from **caches/replicas** built over "
        "hotel and rate data. **Booking** is the correctness-critical write: it "
        "**atomically** checks and decrements inventory for the requested "
        "(room-type, date) rows within a **transaction**, and records the "
        "reservation with an **idempotency key** so retries don't double-book. "
        "Hotel, rate and reservation concerns are separate services, but the "
        "inventory update must be a single atomic operation to prevent overselling."
    ),
    request_flows=[
        "Search -> read availability from cache/replica.",
        "Reserve -> begin transaction -> check-and-decrement inventory for each date.",
        "If all dates available -> commit reservation; else abort and report unavailable.",
        "Idempotency key ensures a retried request is applied exactly once.",
    ],
    deep_dives=[
        DeepDive("Preventing overselling (concurrency control)",
                 "When two requests race for the last room, one must win. **Pessimistic "
                 "locking** (SELECT ... FOR UPDATE) serializes access but reduces "
                 "throughput under contention. **Optimistic concurrency** (version/"
                 "conditional update: decrement only if `reserved < total`) scales better "
                 "and simply retries the loser. Either way the check-and-decrement must be "
                 "atomic in one transaction.",
                 ["Pessimistic locks: simple correctness, lower concurrency.",
                  "Optimistic updates: higher throughput, must handle retry on conflict."]),
        DeepDive("Idempotency for safe retries",
                 "Network timeouts make clients retry bookings. Without protection, a "
                 "retry can create a second reservation (and charge). An **idempotency "
                 "key** stored with the reservation makes the operation apply exactly "
                 "once — a retry returns the original result instead of booking again. "
                 "This is essential wherever money or inventory is involved.",
                 ["Idempotency keys add a lookup/storage step but prevent duplicate bookings."]),
        DeepDive("Read scalability vs write correctness",
                 "Search reads vastly outnumber bookings, so serve them from caches and "
                 "replicas that can be slightly stale (a room shown available may sell out "
                 "by checkout — the booking transaction is the authority). Keeping the "
                 "consistency-critical work confined to the small booking path lets the "
                 "read path scale freely.",
                 ["Cached availability may be briefly stale — the booking transaction is the final arbiter."]),
        DeepDive("Reliability, cost & security",
                 "Reserve inventory first, then confirm payment, releasing the hold on "
                 "timeout so rooms aren't stuck. Partition inventory by hotel to scale and "
                 "isolate hot properties. Protect against booking-bot abuse with rate "
                 "limits, and safeguard guest PII with encryption and access control.",
                 ["Hold-then-pay avoids overselling but needs a timeout to release abandoned holds."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Concurrency control",
            ["Approach", "Under contention", "Throughput", "Complexity"],
            [["Pessimistic lock", "Serializes safely", "Lower", "Low"],
             ["Optimistic (conditional update)", "Retries losers", "Higher", "Medium"],
             ["Reserve-then-confirm", "Holds inventory", "Good", "Medium"]],
        ),
    ],
    bottlenecks=[
        "Contention on hot hotels/dates — optimistic updates + row-level granularity.",
        "Search QPS — cache and replicate availability.",
        "Abandoned holds locking inventory — timeout-based release.",
    ],
    security=[
        "Idempotency + auth to prevent duplicate/fraudulent bookings.",
        "Encrypt guest PII; restrict access.",
        "Rate-limit to deter booking bots and scraping.",
    ],
    wrap_up=(
        "The hotel system is a correctness problem wearing a CRUD costume: search "
        "scales via caches/replicas, but booking must atomically check-and-decrement "
        "inventory in a transaction with an idempotency key to guarantee no "
        "overselling and safe retries. Contention on hot dates is where the design "
        "earns its keep."
    ),
))


# ===========================================================================
# Chapter 8 — Distributed Email Service
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v2_ch8", number=8, volume=2,
    title="Distributed Email Service",
    tagline="Send, receive, store and search email at Gmail scale.",
    diagram_id="v2_ch8",
    overview=(
        "An email service sends outbound mail via **SMTP**, receives inbound mail, "
        "stores it durably, and lets users read (**IMAP/POP**) and **search** it. "
        "At scale the interesting parts are separating **metadata from large "
        "bodies/attachments**, building a **search index** without slowing the "
        "write path, and dealing with **spam** and unreliable external mail servers."
    ),
    clarifying=[
        ClarifyQ("Functional scope",
                 "Full send/receive/read/search, or a subset?",
                 "Search and attachments add significant storage/indexing subsystems.",
                 "Send, receive, read (IMAP/POP) and full-text search with attachments."),
        ClarifyQ("Scale",
                 "How many users and messages/day; average mailbox size?",
                 "Mailbox size x users sets storage; message rate sets ingest/index load.",
                 "Hundreds of millions of users, billions of messages/day, GB mailboxes."),
        ClarifyQ("Consistency",
                 "Must a sent/received message appear instantly everywhere?",
                 "Slight indexing delay is fine; delivery must be reliable and eventually consistent.",
                 "Reliable delivery; search index may lag by seconds (async)."),
        ClarifyQ("Reliability",
                 "What happens when a recipient mail server is down?",
                 "Outbound must queue and retry per SMTP norms rather than dropping mail.",
                 "Queue and retry with backoff; bounce after repeated failures."),
    ],
    requirements=Requirements(
        functional=["Send (SMTP)", "Receive inbound mail", "Read (IMAP/POP)", "Full-text search", "Attachments"],
        non_functional=["Reliable delivery with retries", "Durable storage",
                        "Fast search", "Scale to hundreds of millions of mailboxes"],
        out_of_scope=["Calendar/contacts", "Rich webmail UI"],
    ),
    estimation=Estimation(
        assumptions=["300M users", "10 messages/user/day", "Avg message 50 KB (with attachments)"],
        rows=[
            EstimationRow("Messages/day", "300M x 10", "~ 3B/day"),
            EstimationRow("Write QPS", "3B / 86,400", "~ 35,000 QPS"),
            EstimationRow("Storage/day", "3B x 50 KB", "~ 150 TB/day"),
            EstimationRow("Total mailbox storage", "300M x GBs", "exabyte-scale"),
        ],
        notes=["Bodies/attachments dominate storage; metadata is small but query-heavy."],
    ),
    apis=[
        APIEndpoint("SMTP submit", "Outbound send; queued and retried to recipient servers."),
        APIEndpoint("IMAP/POP fetch", "Read mailbox contents and sync folders."),
        APIEndpoint("GET /v1/search?q=", "Full-text search across a user's mail."),
    ],
    data_model=[
        DataEntity("Message metadata", ["message_id", "mailbox", "from/to", "subject", "flags", "body_ref", "ts"],
                   store="Distributed store keyed by mailbox for fast folder/list queries."),
        DataEntity("Message body / attachment", ["blob"],
                   store="Object storage (large, immutable); deduplicate identical attachments."),
        DataEntity("Search index", ["mailbox", "tokens -> message_ids"],
                   store="Inverted index, built asynchronously per mailbox."),
    ],
    high_level=(
        "**Outbound**: a client submits mail via SMTP; it's placed on a **send "
        "queue** and delivered to recipient servers with retries/backoff. "
        "**Inbound**: received mail is written to the recipient's mailbox. **Storage** "
        "separates small **metadata** (fast folder/list queries) from large "
        "**bodies/attachments** in object storage. **Reads** go through IMAP/POP over "
        "the metadata + blob stores. A **search index** is built **asynchronously** "
        "so indexing never slows delivery. Spam filtering runs in the inbound path."
    ),
    request_flows=[
        "Send -> SMTP submit -> send queue -> deliver to recipient server (retry on failure).",
        "Receive -> spam filter -> write metadata + store body blob.",
        "Read -> IMAP/POP -> metadata store + fetch body from object storage.",
        "Index -> async pipeline updates the inverted index.",
    ],
    deep_dives=[
        DeepDive("Metadata vs blob separation",
                 "Message metadata is small, frequently queried (list a folder, sort by "
                 "date, filter unread) and benefits from a fast, indexed store. Bodies and "
                 "attachments are large and immutable and belong in **object storage**, "
                 "referenced by the metadata. Splitting them lets each scale on its own "
                 "axis and keeps mailbox listing fast.",
                 ["Separation adds an indirection (fetch body by ref) but scales far better."]),
        DeepDive("Asynchronous search indexing",
                 "Indexing every message synchronously would slow delivery and reads. "
                 "Instead, an **async pipeline** consumes new messages and updates an "
                 "**inverted index** per mailbox. Search then hits the index, not raw "
                 "mail. The trade-off is a short delay before a new message is "
                 "searchable — acceptable for email.",
                 ["Async indexing keeps writes fast but makes brand-new mail briefly unsearchable."]),
        DeepDive("Reliable delivery to flaky servers",
                 "External recipient servers go down or throttle. SMTP delivery therefore "
                 "**queues and retries with exponential backoff**, respecting greylisting, "
                 "and only **bounces** after repeated failures over a retry window. This "
                 "is why the send path is a durable queue, not a synchronous call.",
                 ["Long retry windows improve deliverability but hold messages longer."]),
        DeepDive("Scale, cost & security",
                 "Storage (bodies/attachments) is the dominant cost at exabyte scale — "
                 "dedup identical attachments and tier old mail to cheaper storage. "
                 "Security is central: spam/phishing filtering, DKIM/SPF/DMARC for "
                 "authenticity, TLS for transport, and encryption at rest. Mailboxes are "
                 "highly sensitive, so access control and audit are mandatory.",
                 ["Attachment dedup saves storage but must respect per-user isolation."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Storage & indexing",
            ["Data", "Store", "Why"],
            [["Metadata", "Fast indexed store", "Frequent folder/list queries"],
             ["Bodies/attachments", "Object storage", "Large, immutable, cheap"],
             ["Search", "Async inverted index", "Fast search without slowing writes"]],
        ),
    ],
    bottlenecks=[
        "Storage growth from bodies/attachments — dedup + tiering.",
        "Search index size and build load — shard per mailbox, async.",
        "Outbound queue backlog to slow servers — isolate and rate-limit per destination.",
    ],
    security=[
        "Spam/phishing filtering on inbound; DKIM/SPF/DMARC for authenticity.",
        "TLS in transit; encryption at rest; strict per-mailbox access control.",
        "Careful attachment dedup to prevent cross-user leakage.",
    ],
    wrap_up=(
        "A distributed email service separates fast metadata from bulky object-"
        "stored bodies, indexes search asynchronously, and delivers outbound mail "
        "through a durable retrying queue. Storage cost and search scale are the "
        "engineering challenges; spam, authenticity and privacy make security "
        "first-class."
    ),
))

# ===========================================================================
# Chapter 9 — S3-like Object Storage
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v2_ch9", number=9, volume=2,
    title="S3-like Object Storage",
    tagline="Durable, effectively unlimited object storage addressed by bucket + key.",
    diagram_id="v2_ch9",
    overview=(
        "Object storage stores arbitrary blobs retrievable by **bucket + key**, with "
        "extreme **durability** and near-unlimited scale at low cost. The defining "
        "design choices are separating the **metadata plane** from the **data "
        "plane**, and how you achieve durability — **replication** (simple, storage-"
        "hungry) versus **erasure coding** (cheaper, more compute)."
    ),
    clarifying=[
        ClarifyQ("Functional scope",
                 "PUT/GET/DELETE + list + versioning? Multipart uploads?",
                 "Versioning and multipart change metadata and write flow.",
                 "PUT/GET/DELETE, list, versioning, and multipart for large objects."),
        ClarifyQ("Durability target",
                 "How many nines of durability?",
                 "Very high durability (11 nines) dictates replication/erasure strategy across zones.",
                 "~11 nines durability; survive disk, node and zone failures."),
        ClarifyQ("Object size distribution",
                 "Mostly small objects, large objects, or both?",
                 "Small objects stress metadata; large objects stress data placement/bandwidth.",
                 "Wide range; optimize for both with multipart for large."),
        ClarifyQ("Consistency",
                 "Read-after-write consistency for new objects?",
                 "Modern object stores offer strong read-after-write; older were eventual.",
                 "Strong read-after-write for PUTs of new objects."),
    ],
    requirements=Requirements(
        functional=["PUT/GET/DELETE by key", "List objects", "Versioning", "Multipart upload"],
        non_functional=["~11 nines durability", "Massive scale, low cost/GB",
                        "High throughput", "Strong read-after-write"],
        out_of_scope=["File-system semantics (rename, partial edits)"],
    ),
    estimation=Estimation(
        assumptions=["100 PB stored", "Erasure coding overhead ~1.4x vs 3x replication"],
        rows=[
            EstimationRow("Raw with 3x replication", "100 PB x 3", "~ 300 PB"),
            EstimationRow("Raw with erasure coding", "100 PB x ~1.4", "~ 140 PB"),
            EstimationRow("Savings from EC", "300 - 140", "~ 160 PB (huge cost cut)"),
            EstimationRow("Metadata entries", "billions of objects", "large but small per-row"),
        ],
        notes=["Erasure coding roughly halves storage cost versus 3x replication for the same durability."],
    ),
    apis=[
        APIEndpoint("PUT /{bucket}/{key}", "Store an object (single or multipart)."),
        APIEndpoint("GET /{bucket}/{key}", "Retrieve an object (optionally a version)."),
        APIEndpoint("DELETE /{bucket}/{key}", "Delete or create a delete-marker (with versioning)."),
        APIEndpoint("GET /{bucket}?list", "List objects by prefix."),
    ],
    data_model=[
        DataEntity("Object metadata", ["bucket", "key", "version", "size", "checksum", "location refs", "created_at"],
                   store="Metadata service backed by a scalable, strongly consistent DB."),
        DataEntity("Object data", ["chunks / erasure fragments"],
                   store="Data nodes across failure domains; replicated or erasure-coded."),
    ],
    high_level=(
        "The **API service** authenticates the request and routes it. The "
        "**metadata plane** records where each object's data lives (which data "
        "nodes/fragments) and its version, size and checksum. The **data plane** "
        "stores the bytes across **many data nodes spanning failure domains** "
        "(disks, nodes, zones), using **replication** or **erasure coding** for "
        "durability. Large objects use **multipart** upload — split into parts, "
        "stored independently, and stitched via metadata. Objects are **immutable**; "
        "'edits' write a new version. Background processes verify checksums and "
        "**repair** lost fragments."
    ),
    request_flows=[
        "PUT -> API auth -> allocate placement -> write data (replicas/EC) across zones -> commit metadata.",
        "GET -> metadata lookup -> read data (or reconstruct from EC fragments) -> return.",
        "DELETE -> metadata delete/marker -> async reclaim of data.",
        "Background -> scrub checksums, rebuild missing fragments.",
    ],
    deep_dives=[
        DeepDive("Metadata vs data plane separation",
                 "Metadata (small, needs strong consistency and listing/lookup) is a "
                 "different problem than storing petabytes of bytes. Splitting them lets "
                 "the metadata service optimize for consistency and query, while the data "
                 "plane optimizes for throughput and cost. The metadata store itself must "
                 "scale (sharded/distributed) since there are billions of objects.",
                 ["Separation is essential to scale, but metadata becomes its own hard subsystem."]),
        DeepDive("Durability: replication vs erasure coding",
                 "**Replication** (e.g. 3 copies) is simple and fast to read/repair but "
                 "triples storage. **Erasure coding** splits an object into k data + m "
                 "parity fragments across nodes; you can lose up to m fragments and still "
                 "reconstruct, at only ~1.4x overhead — roughly half the cost of 3x "
                 "replication for similar durability. The trade is CPU (encode/decode) and "
                 "slower repair (must read k fragments).",
                 ["Replication: cheap CPU, expensive storage, fast repair.",
                  "Erasure coding: cheap storage, more CPU, slower reconstruction."]),
        DeepDive("Consistency & immutability",
                 "Treating objects as **immutable** (new writes create new versions) makes "
                 "caching, replication and dedup vastly simpler and enables strong "
                 "read-after-write: once metadata commits pointing at fully-written data, "
                 "the object is visible and won't change under readers. Deletes are "
                 "metadata operations with async space reclamation.",
                 ["Immutability simplifies correctness but requires versioning + GC for updates/deletes."]),
        DeepDive("Reliability, cost & security",
                 "Spread fragments/replicas across independent **failure domains** so no "
                 "single disk/node/zone loss risks data. **Background scrubbing** detects "
                 "bit rot via checksums and rebuilds fragments. Cost is controlled by "
                 "erasure coding and **storage tiers** (hot vs archival). Security: "
                 "per-bucket IAM policies, encryption at rest, signed URLs for temporary "
                 "access.",
                 ["Archival tiers slash cost but add retrieval latency/fees."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Durability strategy",
            ["Strategy", "Storage overhead", "CPU", "Repair speed"],
            [["3x replication", "3.0x", "Low", "Fast"],
             ["Erasure coding (e.g. 10+4)", "~1.4x", "Higher", "Slower"]],
        ),
    ],
    bottlenecks=[
        "Metadata service scale (billions of objects) — shard and cache.",
        "Erasure-coding repair load — throttle and prioritize rebuilds.",
        "Hot objects — cache/CDN in front.",
        "Listing large buckets — prefix indexing / pagination.",
    ],
    security=[
        "Per-bucket IAM policies and least privilege.",
        "Encryption at rest; signed URLs for scoped, time-limited access.",
        "Checksums to detect corruption; audit access logs.",
    ],
    wrap_up=(
        "Object storage splits a strongly-consistent metadata plane from a cost-"
        "optimized data plane, achieves durability via replication or (cheaper) "
        "erasure coding across failure domains, and treats objects as immutable "
        "versions. Erasure coding and tiering are the big cost levers; metadata "
        "scale and repair are the operational challenges."
    ),
))


# ===========================================================================
# Chapter 10 — Real-time Gaming Leaderboard
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v2_ch10", number=10, volume=2,
    title="Real-time Gaming Leaderboard",
    tagline="Rank millions of players and answer top-N and 'my rank' instantly.",
    diagram_id="v2_ch10",
    overview=(
        "A leaderboard maintains live scores and answers two queries fast: the "
        "**top-N** players and a **specific player's rank**. Naively computing rank "
        "means sorting millions of scores per query — far too slow. The elegant "
        "answer is a **sorted set** (as in Redis), which gives O(log n) score "
        "updates and rank/range queries, backed by a durable database as the source "
        "of truth."
    ),
    clarifying=[
        ClarifyQ("Functional scope",
                 "Global leaderboard, or per-game/segment/time-window boards?",
                 "Multiple boards multiply the data structures and update fan-out.",
                 "Global + periodic (daily/weekly) boards; design generalizes."),
        ClarifyQ("Queries",
                 "Top-N, a player's absolute rank, and neighbors around them?",
                 "Each maps to sorted-set operations; neighbors need range-around-rank.",
                 "Top-N, exact player rank, and +/- neighbors."),
        ClarifyQ("Scale",
                 "How many players and score updates/sec?",
                 "Update rate and player count decide sharding and whether one sorted set fits.",
                 "~100M players, high update rate during peak play."),
        ClarifyQ("Accuracy/freshness",
                 "Must rank be exact and instantly updated?",
                 "Exact live rank favors the sorted set; approximate rank allows cheaper structures.",
                 "Exact and near-instant for the active window."),
    ],
    requirements=Requirements(
        functional=["Update a player's score", "Get top-N", "Get a player's rank (and neighbors)"],
        non_functional=["Real-time updates", "Fast rank/top-N (sub-ms to ms)",
                        "Scale to 100M players", "Durable source of truth"],
        out_of_scope=["Anti-cheat modeling (mention as security)", "Matchmaking"],
    ),
    estimation=Estimation(
        assumptions=["100M players", "Score entry ~ tens of bytes in sorted set"],
        rows=[
            EstimationRow("Sorted-set memory", "100M x ~64 B", "~ 6+ GB per board"),
            EstimationRow("Update cost", "ZADD", "O(log n)"),
            EstimationRow("Top-N cost", "ZREVRANGE 0 N", "O(log n + N)"),
            EstimationRow("Rank cost", "ZREVRANK", "O(log n)"),
        ],
        notes=["A single sorted set may exceed one node's memory at 100M — shard by score range if so."],
    ),
    apis=[
        APIEndpoint("POST /v1/scores {player, delta|value}", "Update score (ZADD)."),
        APIEndpoint("GET /v1/leaderboard/top?n=", "Top-N players (ZREVRANGE)."),
        APIEndpoint("GET /v1/leaderboard/rank/{player}", "Player rank + neighbors (ZREVRANK + range)."),
    ],
    data_model=[
        DataEntity("Leaderboard (sorted set)", ["member = player_id", "score"],
                   store="Redis sorted set (ZSET) — O(log n) updates and rank queries."),
        DataEntity("Score record (source of truth)", ["player_id", "score", "updated_at"],
                   store="Durable DB; the sorted set is a fast derived view."),
    ],
    high_level=(
        "On a score change, the **score service** updates the player's entry in a "
        "**Redis sorted set** (ZADD) and persists the authoritative score to the "
        "**database**. **Top-N** is a single ZREVRANGE; a player's **rank** is "
        "ZREVRANK, and **neighbors** are a range around that rank — all O(log n) "
        "against the in-memory structure. The durable DB lets you rebuild the sorted "
        "set after a cache loss and supports periodic (daily/weekly) board resets."
    ),
    request_flows=[
        "Score update -> ZADD in sorted set + persist to DB.",
        "Top-N -> ZREVRANGE 0..N.",
        "Player rank -> ZREVRANK; neighbors -> range around rank.",
        "Recovery/reset -> rebuild sorted set from the DB.",
    ],
    deep_dives=[
        DeepDive("Why a sorted set",
                 "The whole problem is answering rank without sorting on every query. A "
                 "**sorted set** keeps members ordered by score with a skip-list/hash "
                 "combo, giving O(log n) inserts and O(log n) rank lookups plus O(log n + "
                 "N) range reads. It converts an O(n log n) sort-per-query into cheap "
                 "logarithmic operations — the key insight of the chapter.",
                 ["In-memory sorted set is fast but volatile — must be backed by a durable store."]),
        DeepDive("Scaling beyond one node",
                 "At 100M+ players a single sorted set may not fit in one node's memory or "
                 "handle the update rate. **Shard by score range** across nodes (each owns "
                 "a band), or partition by segment/region; global top-N then merges the "
                 "top of each shard. Rank across shards requires summing counts below a "
                 "player's score in each shard.",
                 ["Sharding scales memory/throughput but makes global rank a merge/aggregation."]),
        DeepDive("Durability & recovery",
                 "The sorted set is a **derived, in-memory view**; the database is the "
                 "source of truth. If Redis is lost, rebuild the set from the DB. Writes "
                 "go to both — update the DB for durability and the sorted set for fast "
                 "queries — so a crash never loses scores, only requires a rebuild.",
                 ["Dual-writing adds a step but decouples durability from query speed."]),
        DeepDive("Freshness, cost & security",
                 "Memory is the cost driver: tens of bytes per player per board, times "
                 "many boards/windows. Cap active boards, expire old windows, and keep "
                 "only active players hot. Security centers on **anti-cheat**: validate "
                 "score submissions server-side (never trust the client), rate-limit "
                 "updates, and detect anomalous jumps.",
                 ["More boards/time-windows: richer product, more memory.",
                  "Server-side validation adds latency but is essential against cheating."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Rank query approaches",
            ["Approach", "Update", "Rank query", "Notes"],
            [["Sort on demand", "O(1)", "O(n log n)", "Too slow at scale"],
             ["Sorted set (ZSET)", "O(log n)", "O(log n)", "The standard answer"],
             ["Sharded sorted sets", "O(log n)", "O(shards)", "For very large boards"]],
        ),
    ],
    bottlenecks=[
        "Single sorted set memory/throughput — shard by score range.",
        "Global rank across shards — aggregate counts per shard.",
        "Hot updates for top players — batch/coalesce writes.",
    ],
    security=[
        "Validate scores server-side; never trust client-submitted values.",
        "Rate-limit updates; flag anomalous score jumps (anti-cheat).",
        "Authorize who can write scores.",
    ],
    wrap_up=(
        "A leaderboard is a sorted-set problem: ZADD for updates, ZREVRANGE/ZREVRANK "
        "for top-N and rank, all O(log n), backed by a durable DB as source of truth. "
        "Shard by score range when a single set is too big, and validate scores "
        "server-side to prevent cheating."
    ),
))

# ===========================================================================
# Chapter 11 — Payment System
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v2_ch11", number=11, volume=2,
    title="Payment System",
    tagline="Move money correctly, exactly once, and auditably — integrating external providers.",
    diagram_id="v2_ch11",
    overview=(
        "A payment system processes pay-ins and pay-outs, integrating external "
        "**payment service providers (PSPs)** that actually move money. The "
        "non-negotiables are **correctness** (never double-charge, never lose "
        "money), **exactly-once** semantics via idempotency, and a fully "
        "**auditable ledger** that can be **reconciled** against providers. This is "
        "a system where consistency beats availability."
    ),
    clarifying=[
        ClarifyQ("Functional scope",
                 "Pay-in only, or also pay-outs, refunds, and multi-currency?",
                 "Each flow adds ledger entries and reconciliation cases.",
                 "Pay-in and pay-out with refunds; single currency to start."),
        ClarifyQ("Consistency",
                 "Can we ever double-charge or lose a payment?",
                 "Never — this mandates idempotency and a ledger as source of truth.",
                 "Strict correctness; prefer failing safe over duplicating money movement."),
        ClarifyQ("External providers",
                 "Do we integrate PSPs (Stripe, banks), and are they reliable?",
                 "PSPs are asynchronous and can fail/timeout, requiring retries + reconciliation.",
                 "Yes — PSPs move the money; we orchestrate and reconcile."),
        ClarifyQ("Scale",
                 "How many payments/sec?",
                 "Correctness dominates, but throughput sizes the ledger and queue.",
                 "Thousands of payments/sec; correctness over raw throughput."),
    ],
    requirements=Requirements(
        functional=["Process pay-in/pay-out", "Refunds", "Record every movement in a ledger"],
        non_functional=["Exactly-once (no double charge)", "Auditable & reconcilable",
                        "Reliable despite PSP failures", "Strong consistency"],
        out_of_scope=["Fraud/risk scoring models (mention as security)", "Ledger analytics"],
    ),
    estimation=Estimation(
        assumptions=["1,000 payments/sec", "Each payment => several ledger entries", "Retain ledger for years"],
        rows=[
            EstimationRow("Payment QPS", "given", "~ 1,000/s"),
            EstimationRow("Ledger writes/sec", "1,000 x ~2-4 entries", "~ 2,000-4,000/s"),
            EstimationRow("Ledger growth", "millions/day, retained for years", "large, append-only"),
        ],
        notes=["The ledger is append-only and retained long-term for audit and compliance."],
    ),
    apis=[
        APIEndpoint("POST /v1/payments", "Initiate a payment with an idempotency key.", "Idempotency key makes retries safe."),
        APIEndpoint("GET /v1/payments/{id}", "Query payment status (async settlement)."),
        APIEndpoint("POST /v1/payments/{id}/refund", "Issue a refund (recorded in the ledger)."),
    ],
    data_model=[
        DataEntity("Payment", ["id", "amount", "currency", "status", "idempotency_key", "psp_ref"],
                   store="Strongly consistent DB; status transitions are tracked."),
        DataEntity("Ledger entry (double-entry)", ["txn_id", "account", "debit/credit", "amount", "ts"],
                   store="Append-only ledger; every movement is a balanced pair of entries."),
    ],
    high_level=(
        "A payment request carries an **idempotency key**. The **payment service** "
        "records intent in the **double-entry ledger** (each movement is a balanced "
        "debit/credit), then calls the **PSP** to move real money. Because PSP calls "
        "are asynchronous and can fail, the payment moves through explicit **status "
        "states** (pending -> succeeded/failed), retrying safely thanks to "
        "idempotency. A continuous **reconciliation** job compares the ledger with "
        "PSP statements to catch and correct any discrepancy. The ledger — not the "
        "PSP response — is the internal source of truth."
    ),
    request_flows=[
        "Payment request (with idempotency key) -> dedup check.",
        "Record intent in the ledger (double-entry).",
        "Call PSP to move money; update status on callback/poll.",
        "Reconciliation compares ledger vs PSP; correct discrepancies.",
    ],
    deep_dives=[
        DeepDive("The double-entry ledger",
                 "Every money movement is recorded as **two balanced entries** (a debit "
                 "and a matching credit), so the books always sum to zero and every "
                 "balance is derivable from the immutable entry history. This makes the "
                 "system auditable, makes bugs detectable (imbalance = error), and turns "
                 "'what is this account's balance?' into a sum over entries.",
                 ["Append-only double-entry is auditable and self-checking but requires careful modeling of every flow."]),
        DeepDive("Exactly-once via idempotency",
                 "Networks and PSPs time out, and clients retry. An **idempotency key** "
                 "stored with the payment ensures a retried request references the same "
                 "payment rather than creating a new charge. Combined with a state machine "
                 "(a payment can only advance through valid transitions), this delivers "
                 "effectively exactly-once money movement.",
                 ["Idempotency + state machine prevents double charges but requires disciplined status handling."]),
        DeepDive("Handling PSP failures & reconciliation",
                 "The PSP is external and its response may be lost even when the charge "
                 "succeeded. So the system never assumes; it **reconciles** by pulling PSP "
                 "statements and matching them to ledger entries, correcting mismatches "
                 "(mark succeeded, refund a duplicate, flag for manual review). This "
                 "closes the gap between 'we think it happened' and 'it actually happened'.",
                 ["Reconciliation guarantees eventual correctness but introduces a settlement delay."]),
        DeepDive("Consistency, cost & security",
                 "This system favors **consistency over availability** — better to hold or "
                 "fail a payment than to duplicate money. Ledger writes are transactional. "
                 "Security is paramount: PCI-DSS scope minimization (tokenize card data, "
                 "let the PSP hold it), encryption, strict access control and audit logs, "
                 "and fraud/risk checks before authorizing.",
                 ["Favoring consistency can delay/refuse payments during incidents — the right trade for money."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Correctness mechanisms",
            ["Mechanism", "Prevents", "Cost"],
            [["Idempotency key", "Double charges on retry", "Extra lookup/state"],
             ["Double-entry ledger", "Silent imbalances", "Modeling discipline"],
             ["Reconciliation", "PSP/ledger drift", "Settlement delay"]],
        ),
    ],
    bottlenecks=[
        "Ledger write throughput — partition by account, keep entries append-only.",
        "PSP latency/failures — async status + retries + reconciliation.",
        "Reconciliation volume — incremental matching over recent windows.",
    ],
    security=[
        "Minimize PCI scope: tokenize card data, keep it with the PSP.",
        "Encrypt sensitive data; strict access control + immutable audit logs.",
        "Fraud/risk scoring before authorization; idempotency to resist replay.",
    ],
    wrap_up=(
        "A payment system is a correctness-first design: an append-only double-entry "
        "ledger as the source of truth, idempotency keys and a state machine for "
        "exactly-once money movement, and continuous reconciliation against external "
        "PSPs. It deliberately favors consistency over availability."
    ),
))


# ===========================================================================
# Chapter 12 — Digital Wallet
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v2_ch12", number=12, volume=2,
    title="Digital Wallet",
    tagline="High-throughput wallet-to-wallet transfers with strong correctness and auditability.",
    diagram_id="v2_ch12",
    overview=(
        "A digital wallet holds balances and moves money **wallet-to-wallet** at "
        "high throughput while guaranteeing correctness: no money created or "
        "destroyed, correct under concurrency, and fully recoverable/auditable. The "
        "chapter builds up from naive balance updates to **event sourcing + CQRS** "
        "for auditability and scale, and **sagas** for transfers spanning services."
    ),
    clarifying=[
        ClarifyQ("Functional scope",
                 "Balance transfers only, or top-up/withdraw and multi-currency?",
                 "Cross-boundary flows (bank, card) add external integration and sagas.",
                 "Wallet-to-wallet transfers primarily, with top-up/withdraw."),
        ClarifyQ("Correctness",
                 "How strict must balance correctness be under concurrency?",
                 "Money must be exact; concurrent debits on the same wallet must not overspend.",
                 "Strict: no double-spend, balances always reconcilable."),
        ClarifyQ("Throughput",
                 "How many transfers/sec?",
                 "High throughput pushes toward event-sourced, partitioned processing.",
                 "Up to ~1M transfers/sec at peak (design for scale)."),
        ClarifyQ("Auditability & recovery",
                 "Do we need a full history and the ability to rebuild state?",
                 "Event sourcing gives a complete, replayable audit trail.",
                 "Yes — full audit trail and deterministic state reconstruction."),
    ],
    requirements=Requirements(
        functional=["Transfer between wallets", "Top-up / withdraw", "Query balance & history"],
        non_functional=["Strong correctness (no double-spend)", "High throughput",
                        "Full auditability", "Deterministic recovery"],
        out_of_scope=["FX/pricing engine", "KYC onboarding flows"],
    ),
    estimation=Estimation(
        assumptions=["1M transfers/sec peak", "Each transfer => 2 balance changes + events"],
        rows=[
            EstimationRow("Transfer TPS", "given", "~ 1,000,000/s"),
            EstimationRow("Events/sec", "1M x several", "millions of events/s"),
            EstimationRow("Event log growth", "append-only", "very large, retained for audit"),
        ],
        notes=["Event sourcing turns balances into a fold over an append-only event log."],
    ),
    apis=[
        APIEndpoint("POST /v1/transfers", "Transfer amount from wallet A to wallet B (idempotency key)."),
        APIEndpoint("GET /v1/wallets/{id}/balance", "Read current balance (query side)."),
        APIEndpoint("GET /v1/wallets/{id}/history", "Read event history / statement."),
    ],
    data_model=[
        DataEntity("Command / transfer", ["id", "from", "to", "amount", "idempotency_key", "status"],
                   store="Command side; validated then turned into events."),
        DataEntity("Event", ["event_id", "wallet_id", "type (debit/credit)", "amount", "seq", "ts"],
                   store="Append-only event store — the source of truth."),
        DataEntity("Balance (read model)", ["wallet_id", "balance", "version"],
                   store="Materialized view projected from events for fast reads."),
    ],
    high_level=(
        "The wallet service uses **CQRS**: the **command side** validates a transfer "
        "(sufficient funds, valid wallets) and appends **events** (debit A, credit "
        "B) to an **append-only event store**; the **query side** maintains a "
        "materialized **balance** view projected from those events for fast reads. "
        "Balances are always derivable by **replaying events**, giving auditability "
        "and deterministic recovery. Transfers that span services or partitions use "
        "a **saga**: a sequence of local steps with compensating actions if a later "
        "step fails, achieving atomicity without distributed two-phase commit."
    ),
    request_flows=[
        "Transfer command -> validate (funds, wallets, idempotency).",
        "Append debit + credit events to the event store.",
        "Projection updates the balance read model.",
        "Cross-partition transfer -> saga with compensations on failure.",
    ],
    deep_dives=[
        DeepDive("Event sourcing & CQRS",
                 "Instead of mutating a balance in place, the wallet **appends events** "
                 "(money entered/left) and derives the balance by folding them. This gives "
                 "a complete **audit trail**, deterministic **recovery** (replay events), "
                 "and separates the write path from an optimized read model (**CQRS**). "
                 "The cost is eventual consistency between the event log and the read "
                 "model, and more moving parts than a simple UPDATE.",
                 ["Event sourcing: auditable + recoverable, but read models lag and complexity rises.",
                  "In-place balance UPDATE: simple, but loses history and is harder to audit."]),
        DeepDive("Correctness under concurrency",
                 "Concurrent debits on the same wallet must not overspend. Serialize "
                 "per-wallet writes (e.g. by partitioning events by wallet id and using an "
                 "expected-version/optimistic check on append) so two transfers can't both "
                 "spend the same funds. Cross-wallet atomicity comes from the event pair "
                 "(debit+credit) being committed together or via a saga.",
                 ["Per-wallet serialization guarantees correctness but caps per-wallet throughput."]),
        DeepDive("Distributed transfers with sagas",
                 "When source and destination live on different partitions/services, a "
                 "single ACID transaction isn't available. A **saga** executes the "
                 "transfer as steps (reserve from A, credit B) with **compensating "
                 "actions** (refund A) if a step fails, providing atomicity semantics "
                 "without locking across services (avoiding fragile 2PC).",
                 ["Sagas avoid distributed locks but require carefully designed compensations."]),
        DeepDive("Throughput, cost & security",
                 "Partitioning by wallet id lets independent wallets process in parallel, "
                 "scaling to very high TPS; hot wallets (a popular merchant) are the "
                 "skew to watch. The event log grows unbounded — snapshot balances "
                 "periodically so recovery doesn't replay from the beginning. Security: "
                 "idempotency to resist replay, encryption, and immutable audit logs.",
                 ["Snapshots speed recovery but add a snapshot-consistency concern.",
                  "Hot wallets limit parallelism — may need special handling."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "State management",
            ["Approach", "Auditability", "Read speed", "Complexity"],
            [["In-place balance UPDATE", "Low", "High", "Low"],
             ["Event sourcing + CQRS", "High", "High (read model)", "High"],
             ["Event sourcing + snapshots", "High", "High", "High (recovery faster)"]],
        ),
    ],
    bottlenecks=[
        "Hot wallets serialize per-wallet writes — special-case or shard sub-balances.",
        "Event log growth — periodic snapshots + archival.",
        "Read-model lag — bound projection latency; read-your-writes where needed.",
    ],
    security=[
        "Idempotency keys to resist duplicate/replayed transfers.",
        "Immutable event log for audit; encryption at rest.",
        "Authorization on every transfer; anomaly detection for fraud.",
    ],
    wrap_up=(
        "A digital wallet uses event sourcing + CQRS for auditability, deterministic "
        "recovery and fast reads, serializes per-wallet writes for correctness, and "
        "uses sagas for cross-service transfers. Partition by wallet for throughput, "
        "snapshot for fast recovery, and keep idempotency and audit central."
    ),
))


# ===========================================================================
# Chapter 13 — Stock Exchange
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v2_ch13", number=13, volume=2,
    title="Stock Exchange",
    tagline="Match buy/sell orders with deterministic, ultra-low latency and strict fairness.",
    diagram_id="v2_ch13",
    overview=(
        "A stock exchange matches buy and sell **orders** against an **order book** "
        "with **price-time priority**, publishes **market data**, and must never "
        "lose an order — all at **ultra-low, deterministic latency**. The design "
        "centers on an **in-memory matching engine** fed by a **sequencer** that "
        "imposes a total order for fairness and determinism, with an event log for "
        "recovery."
    ),
    clarifying=[
        ClarifyQ("Functional scope",
                 "Limit + market orders? Cancels/modifies? Which order types?",
                 "Order types define the matching logic and book structure.",
                 "Limit and market orders with cancel/modify; price-time priority."),
        ClarifyQ("Latency",
                 "What latency and determinism are required?",
                 "Exchanges need microsecond, deterministic latency — favoring in-memory single-writer designs.",
                 "Microsecond-scale, deterministic; fairness is mandatory."),
        ClarifyQ("Correctness/fairness",
                 "Must matching be strictly fair and never lose orders?",
                 "A global order (sequencer) ensures fairness and reproducibility; a log ensures no loss.",
                 "Strict price-time fairness; every order durably logged."),
        ClarifyQ("Scale",
                 "How many orders/sec per symbol?",
                 "Throughput per symbol decides partitioning (one engine per symbol/shard).",
                 "Hundreds of thousands to millions of orders/sec across symbols."),
    ],
    requirements=Requirements(
        functional=["Accept/cancel/modify orders", "Match with price-time priority", "Publish market data"],
        non_functional=["Ultra-low deterministic latency", "Strict fairness",
                        "No order loss (durable log)", "Recoverable book state"],
        out_of_scope=["Clearing/settlement (downstream)", "Regulatory reporting details"],
    ),
    estimation=Estimation(
        assumptions=["1M orders/sec across symbols", "Per-symbol engine in memory"],
        rows=[
            EstimationRow("Order throughput", "given", "~ 1,000,000/s"),
            EstimationRow("Match latency target", "in-memory", "microseconds"),
            EstimationRow("Event log rate", "orders + trades", "millions of events/s"),
            EstimationRow("Order book memory", "open orders per symbol", "fits in RAM"),
        ],
        notes=["In-memory + single-writer per symbol is what achieves microsecond determinism."],
    ),
    apis=[
        APIEndpoint("submit(order)", "Send a limit/market order via the order gateway."),
        APIEndpoint("cancel(order_id)", "Cancel a resting order."),
        APIEndpoint("(feed) market data", "Stream of trades and order-book updates to subscribers."),
    ],
    data_model=[
        DataEntity("Order", ["order_id", "symbol", "side", "price", "qty", "type", "ts", "seq"],
                   store="Sequenced input; persisted to the event log before matching."),
        DataEntity("Order book (per symbol)", ["bids sorted desc", "asks sorted asc (price, then time)"],
                   store="In-memory structure owned by a single matching thread per symbol."),
        DataEntity("Trade / event log", ["append-only sequence of orders, cancels, trades"],
                   store="Durable log for recovery and replay of the book."),
    ],
    high_level=(
        "Orders arrive through **gateways** and pass through a **sequencer** that "
        "assigns a **total order** — this is what makes matching **fair** (strict "
        "arrival order) and **deterministic** (replayable). Each **matching engine** "
        "runs **in memory, single-writer per symbol**, matching incoming orders "
        "against the **order book** by **price-time priority**. Every order and "
        "resulting trade is appended to a durable **event log** first, so the exact "
        "book can be **reconstructed** after a crash by replaying the log. A "
        "**market-data publisher** broadcasts trades and book updates to subscribers."
    ),
    request_flows=[
        "Order -> gateway -> sequencer assigns global sequence.",
        "Order appended to durable event log (no loss).",
        "Matching engine matches against the in-memory book (price-time priority).",
        "Trades + book deltas -> market data feed; state replayable from the log.",
    ],
    deep_dives=[
        DeepDive("Sequencer: fairness + determinism",
                 "A single **sequencer** imposes a total order on all inputs. This "
                 "guarantees **fairness** (orders are processed strictly in arrival order, "
                 "not by who has the faster server post-gateway) and **determinism** "
                 "(replaying the sequenced input reproduces the exact same book and "
                 "trades). Determinism is what lets you recover and audit precisely.",
                 ["A single sequencer is a throughput ceiling per stream but is the source of fairness/determinism."]),
        DeepDive("In-memory single-writer matching",
                 "Matching runs in memory with **one writer per symbol**, eliminating lock "
                 "contention and giving predictable microsecond latency. The order book is "
                 "a pair of price-sorted structures; matching pops the best opposing price "
                 "and fills by time priority. Partitioning by symbol scales throughput "
                 "horizontally (independent engines) without breaking per-symbol ordering.",
                 ["Single-writer removes locks (fast, deterministic) but caps per-symbol throughput.",
                  "Per-symbol partitioning scales out while preserving ordering."]),
        DeepDive("Durability & recovery (event log)",
                 "Because losing an order is unacceptable, every input is **persisted to "
                 "an append-only log before matching**. After a failure, the engine "
                 "**replays** the log to rebuild the exact in-memory book — deterministic "
                 "matching guarantees the reconstructed state is identical. Hot standbys "
                 "can consume the same log for fast failover.",
                 ["Log-before-match adds latency but guarantees no order loss and exact recovery."]),
        DeepDive("Latency, cost & security",
                 "Ultra-low latency drives choices most systems never make: in-memory "
                 "data, kernel-bypass networking, colocated hardware, minimal GC. This is "
                 "costly and specialized. Security and integrity are paramount: strict "
                 "authentication of participants, immutable audit logs for regulators, and "
                 "safeguards (circuit breakers, price bands) against runaway/erroneous "
                 "orders.",
                 ["Chasing microseconds is expensive and specialized — justified only where latency is the product."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Matching engine design",
            ["Choice", "Benefit", "Cost"],
            [["Single-writer per symbol", "No locks, deterministic", "Per-symbol throughput cap"],
             ["In-memory book", "Microsecond latency", "Needs log for durability"],
             ["Sequencer", "Fairness + replay", "A serialization point"]],
        ),
    ],
    bottlenecks=[
        "Sequencer/single-writer throughput — partition by symbol.",
        "Log write latency on the hot path — fast durable log, batch/pipeline.",
        "Market-data fan-out — efficient multicast/pub-sub to subscribers.",
    ],
    security=[
        "Strong authentication of trading participants.",
        "Immutable audit trail for compliance and dispute resolution.",
        "Circuit breakers / price bands to contain erroneous or runaway orders.",
    ],
    wrap_up=(
        "A stock exchange is a determinism-and-fairness machine: a sequencer imposes "
        "total order, an in-memory single-writer matching engine per symbol matches "
        "by price-time priority at microsecond latency, and a log-before-match "
        "design guarantees no loss and exact recovery. It trades raw throughput and "
        "cost for fairness, determinism and speed."
    ),
))
