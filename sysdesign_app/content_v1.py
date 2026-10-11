"""
Deep, interview-grade content for Volume 1 (Chapters 1–16).

Each Chapter follows the clarify-then-solve structure defined in schema.py.
Content is original, paraphrased study material written to interview depth
(ambiguity, trade-offs, cost, scalability, security, reliability, bottlenecks).
"""

from __future__ import annotations

from schema import (
    Chapter, ClarifyQ, Requirements, Estimation, EstimationRow,
    APIEndpoint, DataEntity, DeepDive, TradeoffTable, Component,
)

CHAPTERS: list[Chapter] = []

# ===========================================================================
# Chapter 1 — Scale From Zero To Millions Of Users
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v1_ch1", number=1, volume=1,
    title="Scale From Zero to Millions of Users",
    tagline="Evolve a single-server app into a resilient, horizontally scaled system.",
    diagram_id="v1_ch1",
    overview=(
        "This chapter is the backbone of every other design: how a system grows "
        "from one box serving a handful of users into a distributed architecture "
        "serving millions. The skill tested is **incremental evolution** — you "
        "never jump to the final architecture. Start simple, find the bottleneck, "
        "add exactly the component that removes it, and name the trade-off it "
        "introduces. The recurring theme: **statelessness + horizontal scaling** "
        "lets a system grow without a rewrite, and **caching + async work** are "
        "the biggest levers for latency and cost."
    ),
    clarifying=[
        ClarifyQ("Functional scope",
                 "Is the workload read-heavy, write-heavy, or mixed?",
                 "The read/write ratio decides whether you invest in replicas/caches (reads) or sharding/queues (writes).",
                 "Read-heavy web app, ~100:1 reads:writes, like most consumer products."),
        ClarifyQ("Scale / traffic",
                 "How many daily active users and what is the growth curve?",
                 "Separates 'one server is fine' from 'we need multi-region', and sets the estimation baseline.",
                 "Growing from thousands to ~10M DAU, so we plan the path, not just the endpoint."),
        ClarifyQ("Non-functional",
                 "What are the availability and latency targets?",
                 "99.9% vs 99.99% changes the redundancy budget; p99 latency changes caching/CDN decisions.",
                 "99.99% availability, p99 read latency under ~200 ms."),
        ClarifyQ("Constraints",
                 "Single region or global? Any data-residency rules?",
                 "Global users force CDN, geo-DNS and cross-region replication, which add consistency complexity.",
                 "Start single-region; design so multi-region is additive, not a rewrite."),
        ClarifyQ("Consistency",
                 "Is eventual consistency acceptable for reads?",
                 "Replicas and caches introduce staleness; if strong consistency is required everywhere the design differs.",
                 "Eventual consistency is fine for most reads; a few flows need read-your-writes."),
    ],
    requirements=Requirements(
        functional=[
            "Serve web/API requests for the product's core features",
            "Persist and retrieve user data reliably",
            "Serve static assets (images, JS, CSS) quickly worldwide",
        ],
        non_functional=[
            "Scale horizontally with traffic — no single bottleneck",
            "99.99% availability (no single point of failure)",
            "Low-latency reads via caching and CDN",
            "Cost grows sub-linearly with traffic where possible",
            "Operational simplicity: stateless tiers, easy to add capacity",
        ],
        out_of_scope=[
            "The specific product features (this is an infrastructure pattern)",
            "Detailed billing / payments",
        ],
    ),
    estimation=Estimation(
        assumptions=[
            "10M DAU, each making ~20 requests/day",
            "Read:write ratio ~ 100:1",
            "Average response payload ~ 2 KB",
        ],
        rows=[
            EstimationRow("Average QPS", "10M x 20 / 86,400", "~ 2,300 QPS"),
            EstimationRow("Peak QPS", "2,300 x 3", "~ 7,000 QPS"),
            EstimationRow("Read QPS", "~99% of peak", "~ 6,900 QPS"),
            EstimationRow("Write QPS", "~1% of peak", "~ 70 QPS"),
            EstimationRow("Egress bandwidth", "7,000 x 2 KB", "~ 14 MB/s"),
        ],
        notes=[
            "One modern server handles thousands of QPS, but not with redundancy — "
            "we need at least two of everything for availability.",
            "Reads dominate, so caching and replicas are the highest-leverage investments.",
        ],
    ),
    apis=[
        APIEndpoint("GET /v1/resource/{id}", "Read path — served from cache when hot, replica on miss."),
        APIEndpoint("POST /v1/resource", "Write path — goes to the primary database and invalidates cache."),
    ],
    data_model=[
        DataEntity("Core entities",
                   ["id (PK)", "attributes...", "created_at, updated_at"],
                   store="Relational primary for writes; read replicas for scale-out reads."),
    ],
    high_level=(
        "**Evolution, step by step:**\n\n"
        "1. **Single server** — web, app and DB together. Simple, but a single point of failure.\n"
        "2. **Separate the database** so web and DB scale independently.\n"
        "3. **Load balancer + stateless web servers** — any server handles any request; losing one is invisible.\n"
        "4. **Database replication** — primary takes writes, replicas serve reads and enable failover.\n"
        "5. **Cache (cache-aside)** — check cache, on miss read DB then populate. Cuts DB load and latency.\n"
        "6. **CDN** — serve static assets from the edge.\n"
        "7. **Shared session store** — keep web servers stateless so autoscaling is trivial.\n"
        "8. **Message queue + workers** — move slow work off the request path.\n"
        "9. **Database sharding** — when one primary can't take the write load.\n"
        "10. **Multiple data centers** — geo-route and replicate for latency and DR."
    ),
    request_flows=[
        "User -> DNS resolves to the nearest region.",
        "Static assets served from the CDN edge.",
        "Dynamic request -> load balancer -> a stateless web server.",
        "Web server checks cache; on miss reads a replica and populates cache.",
        "Writes go to the primary; replicas catch up asynchronously.",
        "Slow tasks are enqueued and handled by workers.",
    ],
    deep_dives=[
        DeepDive("Scalability",
                 "Horizontal scaling beats vertical scaling at scale: you cannot buy an "
                 "infinitely large machine, and one big box is still a single point of "
                 "failure. The enabler is a **stateless web tier** — no request depends "
                 "on which server served the previous one, so you add/remove servers "
                 "freely behind the load balancer. Reads scale with replicas and caches; "
                 "writes eventually scale with sharding.",
                 ["Vertical scaling is simpler but capped and fragile.",
                  "Horizontal scaling needs statelessness and a load balancer."]),
        DeepDive("Cost efficiency",
                 "Caching and the CDN are the cheapest performance you can buy: a cache "
                 "hit avoids a DB query; a CDN hit avoids origin traffic. Autoscaling the "
                 "stateless tier means paying for peak only when it happens. The costly "
                 "resources are the write-side database and cross-region replication, so "
                 "defer them until estimation shows you need them.",
                 ["Over-provisioning wastes money; autoscaling adds cold starts.",
                  "Aggressive caching risks staleness — bound with TTLs and invalidation."]),
        DeepDive("Reliability & availability",
                 "The rule is 'no single point of failure': at least two of every tier, "
                 "health checks on the load balancer, multi-AZ deployment. The database "
                 "is the hardest SPOF to remove — you need automated primary failover and "
                 "must choose synchronous vs asynchronous replication.",
                 ["Synchronous replication: stronger durability, higher write latency.",
                  "Asynchronous replication: fast writes, small data-loss window on failover."]),
        DeepDive("Security",
                 "Terminate TLS at the load balancer/CDN, keep databases in private "
                 "subnets never exposed to the internet, and put a WAF at the edge. "
                 "Secrets live in a managed secret store, not in code. Rate limiting at "
                 "the gateway protects every downstream tier.",
                 ["A WAF adds latency and false positives but blocks common attacks."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Scaling the database",
            ["Technique", "Helps with", "Cost / downside"],
            [["Read replicas", "Read scale + failover", "Replication lag, eventual consistency"],
             ["Caching", "Read latency + DB load", "Staleness, invalidation complexity"],
             ["Vertical scale", "Quick short-term relief", "Hard ceiling, still an SPOF"],
             ["Sharding", "Write scale", "Cross-shard queries, rebalancing pain"]],
        ),
    ],
    bottlenecks=[
        "The write-side primary database becomes the ceiling — resolve with sharding or a write-optimized store.",
        "A single region limits latency for distant users — add regions and geo-routing.",
        "Cache stampede on popular keys — use request coalescing and staggered TTLs.",
        "Load balancer capacity — use DNS-level distribution across multiple LBs.",
    ],
    security=[
        "TLS everywhere; terminate at edge, re-encrypt to origin where required.",
        "Databases in private subnets; least-privilege IAM for service-to-service access.",
        "WAF + rate limiting at the gateway to blunt DDoS and abuse.",
        "Secrets in a managed vault with rotation; never in source control.",
    ],
    wrap_up=(
        "You scaled from one server to a distributed, multi-tier system by removing "
        "one bottleneck at a time. The transferable ideas — **stateless tiers, "
        "read replicas, cache-aside, CDN, queues, and sharding** — reappear in every "
        "other design in this book. To scale further: multi-region active-active, "
        "cell-based architecture to limit blast radius, and CQRS to separate read "
        "and write models."
    ),
))

# ===========================================================================
# Chapter 2 — Back-of-the-Envelope Estimation
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v1_ch2", number=2, volume=1,
    title="Back-of-the-Envelope Estimation",
    tagline="Size a system fast so your design decisions are grounded in numbers.",
    diagram_id="v1_ch2",
    overview=(
        "Estimation is how you turn a vague prompt into concrete constraints. "
        "Interviewers use it to see whether you can reason about **scale** — will "
        "this fit in memory? do we need sharding? one region or many? The goal is "
        "the right **order of magnitude**, not precision. You state assumptions "
        "out loud, do simple arithmetic, and let the numbers point at the "
        "bottleneck before you design anything."
    ),
    clarifying=[
        ClarifyQ("Scope",
                 "Which metric actually drives the design — QPS, storage, or bandwidth?",
                 "Different systems are bound by different resources; estimating the wrong one wastes time.",
                 "Identify the dominant constraint first (e.g. storage for a photo service, QPS for an API)."),
        ClarifyQ("Traffic shape",
                 "What's the peak-to-average ratio?",
                 "You must provision for peak, not average; the multiplier changes capacity by 2-5x.",
                 "Assume peak ~ 2-3x average unless told otherwise."),
        ClarifyQ("Data lifetime",
                 "How long is data retained?",
                 "Retention multiplied by write rate determines total storage and cost.",
                 "Retain 5 years for cold data, with tiering to cheaper storage over time."),
    ],
    requirements=Requirements(
        functional=["Produce QPS, storage, bandwidth and memory estimates on demand"],
        non_functional=["Fast to compute mentally", "Order-of-magnitude accuracy", "Explicit assumptions"],
        out_of_scope=["Exact capacity planning / benchmarking"],
    ),
    estimation=Estimation(
        assumptions=[
            "Example service: 100M DAU, 1 write + 10 reads per user per day",
            "Each record ~ 1 KB; retained 5 years",
        ],
        rows=[
            EstimationRow("Write QPS", "100M x 1 / 86,400", "~ 1,160 QPS"),
            EstimationRow("Peak write QPS", "1,160 x 3", "~ 3,500 QPS"),
            EstimationRow("Read QPS", "100M x 10 / 86,400", "~ 11,600 QPS"),
            EstimationRow("Storage / year", "100M x 1 KB x 365", "~ 36.5 TB/yr"),
            EstimationRow("Storage / 5 yr", "36.5 TB x 5", "~ 180 TB"),
            EstimationRow("Cache memory", "hot 20% of daily reads x 1 KB", "~ 20 GB"),
        ],
        notes=[
            "Powers of two: KB=2^10, MB=2^20, GB=2^30, TB=2^40, PB=2^50.",
            "Latency intuition: memory ~100 ns, SSD read ~100 us, cross-region round trip ~100 ms.",
            "Availability: 99.9% ~ 8.7 h/yr down; 99.99% ~ 52 min/yr; 99.999% ~ 5 min/yr.",
        ],
    ),
    apis=[],
    data_model=[],
    high_level=(
        "**The estimation recipe:**\n\n"
        "1. **State assumptions** — DAU, actions per user, payload size, retention. "
        "Say them out loud so the interviewer can correct you.\n"
        "2. **Derive QPS** — total daily actions / 86,400, then multiply for peak.\n"
        "3. **Derive storage** — record size x record count x retention; add replication factor.\n"
        "4. **Derive bandwidth** — QPS x payload size, both ingress and egress.\n"
        "5. **Derive memory** — the hot working set you'd cache (often ~20% of reads).\n"
        "6. **Interpret** — compare to hardware limits to spot the bottleneck."
    ),
    request_flows=[
        "Prompt -> list assumptions.",
        "Assumptions -> QPS, storage, bandwidth, memory.",
        "Numbers -> identify the binding constraint -> shape the design.",
    ],
    deep_dives=[
        DeepDive("From numbers to architecture",
                 "Estimation is only useful if it changes a decision. If storage is 180 "
                 "TB, a single node won't hold it — you need sharding or object storage. "
                 "If read QPS is 12k and each hits the DB, you need caching and replicas. "
                 "If bandwidth is high, the CDN and compression matter. Always close the "
                 "loop: 'because the number is X, the design must do Y.'",
                 ["Rounding aggressively speeds the math but can hide a 2-3x factor — keep the peak multiplier explicit."]),
        DeepDive("Cost efficiency",
                 "Numbers reveal cost. 180 TB on hot SSD-backed databases is far more "
                 "expensive than the same data tiered to object storage with a cache in "
                 "front. Estimation lets you argue for tiering, compression, and TTL-based "
                 "eviction with real figures rather than hand-waving.",
                 ["Cheaper cold tiers add retrieval latency — acceptable for archival, not for hot reads."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Which resource binds the system?",
            ["If the big number is...", "You likely need...", "Watch out for..."],
            [["Read QPS", "Caching + read replicas", "Cache staleness"],
             ["Write QPS", "Sharding + queues", "Hot shards, rebalancing"],
             ["Storage", "Object storage + tiering", "Retrieval latency"],
             ["Bandwidth", "CDN + compression", "Cache invalidation"]],
        ),
    ],
    bottlenecks=[
        "Under-estimating peak leads to outages under real load — always size for peak.",
        "Ignoring replication factor undercounts storage by 2-3x.",
    ],
    security=[
        "Estimation itself is safe, but capacity headroom is a DDoS defense: provision and rate-limit for well above expected peak.",
    ],
    wrap_up=(
        "Good estimation is fast, explicit, and decision-oriented. Memorize the "
        "powers of two, a few latency numbers, and the availability nines, and "
        "always translate each number into a concrete design consequence."
    ),
))


# ===========================================================================
# Chapter 3 — A Framework for System Design Interviews
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v1_ch3", number=3, volume=1,
    title="A Framework for System Design Interviews",
    tagline="A repeatable method: clarify, design, deep-dive, wrap up.",
    diagram_id="v1_ch3",
    overview=(
        "A system design interview is open-ended by design. The framework keeps "
        "you from rambling: understand the problem, propose a high-level design and "
        "get buy-in, deep-dive where it matters, then wrap up with trade-offs. This "
        "is the exact flow this trainer enforces — clarify first, then solve."
    ),
    clarifying=[
        ClarifyQ("Process",
                 "How much time do we have, and what does the interviewer want to emphasize?",
                 "Time-boxing decides how deep you can go; some interviewers want breadth, others one deep component.",
                 "~45 minutes: ~10 clarify, ~10 high-level, ~20 deep dive, ~5 wrap-up."),
        ClarifyQ("Scope",
                 "Which features are in scope for this session?",
                 "You cannot design everything; agreeing scope prevents wasted effort.",
                 "Pick 2-3 core features and design those end to end."),
    ],
    requirements=Requirements(
        functional=["Cover requirements, design, deep dive and trade-offs in order"],
        non_functional=["Structured", "Communicative", "Time-boxed"],
        out_of_scope=["Any single specific system (this is the meta-process)"],
    ),
    estimation=Estimation(
        assumptions=["A typical 45-minute interview"],
        rows=[
            EstimationRow("Clarify", "~20% of time", "~10 min"),
            EstimationRow("High-level design", "~20%", "~10 min"),
            EstimationRow("Deep dive", "~45%", "~20 min"),
            EstimationRow("Wrap-up", "~10%", "~5 min"),
        ],
        notes=["Budgets are guidance, not rules — read the interviewer and adjust."],
    ),
    apis=[],
    data_model=[],
    high_level=(
        "**Step 1 - Understand the problem and establish scope.** Ask about "
        "features, users, scale, and constraints. Write down functional and "
        "non-functional requirements. Do back-of-the-envelope estimates.\n\n"
        "**Step 2 - Propose a high-level design and get buy-in.** Draw boxes and "
        "arrows: clients, APIs, services, storage. Walk one or two request flows. "
        "Confirm the interviewer agrees before going deeper.\n\n"
        "**Step 3 - Design deep dive.** Zoom into the components that matter most "
        "(often data model, a hot path, or a tricky consistency problem). Discuss "
        "alternatives and justify choices with the numbers from Step 1.\n\n"
        "**Step 4 - Wrap up.** Summarize, call out bottlenecks, discuss how you'd "
        "scale further, and acknowledge trade-offs and failure modes."
    ),
    request_flows=[
        "Clarify -> lock requirements.",
        "High-level -> agree the architecture.",
        "Deep dive -> justify the hard parts.",
        "Wrap up -> trade-offs and next steps.",
    ],
    deep_dives=[
        DeepDive("Communication is the real test",
                 "Interviewers evaluate how you think, not whether you recite a known "
                 "answer. Narrate your reasoning, state assumptions, and explicitly "
                 "surface trade-offs. Silence and a perfect diagram score worse than a "
                 "slightly rougher design explained clearly.",
                 ["Going deep on one thing beats shallow coverage of everything."]),
        DeepDive("Managing ambiguity",
                 "Ambiguity is deliberate. Resolve it with targeted questions, then "
                 "restate the assumptions you'll design against. This is exactly the "
                 "clarify phase — it prevents building the wrong system.",
                 ["Too many questions wastes time; ask the ones that change the design."]),
    ],
    tradeoff_tables=[],
    bottlenecks=[
        "Skipping clarification -> designing the wrong problem.",
        "Spreading too thin -> no depth to demonstrate skill.",
    ],
    security=["Remember to raise security/privacy in the deep dive; strong candidates volunteer it unprompted."],
    wrap_up=(
        "The framework is a habit: clarify, design, deep-dive, wrap up. Practice it "
        "until it's automatic, and every subsequent chapter becomes an application "
        "of the same four steps."
    ),
))

# ===========================================================================
# Chapter 4 — Design a Rate Limiter
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v1_ch4", number=4, volume=1,
    title="Design a Rate Limiter",
    tagline="Throttle requests fairly and accurately to protect services from overload and abuse.",
    diagram_id="v1_ch4",
    overview=(
        "A rate limiter caps how many requests a client may make in a time window, "
        "returning HTTP 429 when the limit is exceeded. It protects backends from "
        "abuse, accidental request storms, and cascading failure, and it enforces "
        "fair usage and billing tiers. The design tension is **accuracy vs cost**: "
        "the most precise algorithms use the most memory, and in a distributed "
        "fleet the counters must be shared without becoming a bottleneck."
    ),
    clarifying=[
        ClarifyQ("Functional scope",
                 "Do we limit per user, per IP, per API key, or a combination?",
                 "The identity dimension defines the counter key and affects fairness and abuse resistance.",
                 "Per API key primarily, with per-IP as a coarse anti-abuse fallback."),
        ClarifyQ("Placement",
                 "Client-side, a standalone middleware, or the API gateway?",
                 "Server-side is authoritative; the gateway centralizes it for all services.",
                 "Enforce at the API gateway so every service is protected uniformly."),
        ClarifyQ("Accuracy",
                 "Is occasional slight over-admission acceptable, or must limits be exact?",
                 "Exactness drives algorithm and memory choice (sliding window log vs counter).",
                 "Small bursts at window edges are acceptable; use sliding-window counter."),
        ClarifyQ("Scale",
                 "How many rules and how much request volume?",
                 "High volume across many nodes needs shared, atomic counters in a fast store.",
                 "Millions of clients, tens of thousands of QPS, distributed fleet."),
        ClarifyQ("Behavior on limit",
                 "Reject, queue, or throttle? What headers do we return?",
                 "Clients need to back off correctly; standard headers make integration predictable.",
                 "Reject with 429 + Retry-After and X-RateLimit-* headers."),
    ],
    requirements=Requirements(
        functional=[
            "Limit requests per client per window",
            "Return 429 with clear rate-limit headers when exceeded",
            "Support configurable rules per API/tier",
        ],
        non_functional=[
            "Low added latency (single-digit ms)",
            "Accurate across a distributed cluster",
            "Highly available — must not take down traffic if it fails",
            "Memory-efficient at millions of keys",
        ],
        out_of_scope=["Billing integration", "Per-endpoint quota analytics dashboards"],
    ),
    estimation=Estimation(
        assumptions=["10M active clients", "Peak 50,000 QPS through the gateway"],
        rows=[
            EstimationRow("Counter ops/sec", "~ peak QPS", "~ 50,000 ops/s"),
            EstimationRow("Keys in memory", "10M clients x small counter", "~ hundreds of MB"),
            EstimationRow("Redis latency budget", "per request", "< 1 ms"),
        ],
        notes=["Counters are tiny; the cost is op throughput and round-trip latency, not storage."],
    ),
    apis=[
        APIEndpoint("(implicit) every request", "The limiter runs in the gateway before routing; no public API of its own."),
        APIEndpoint("HTTP 429 Too Many Requests",
                    "Returned with Retry-After and X-RateLimit-Limit/Remaining/Reset headers.",
                    "Clients must honor Retry-After to back off."),
    ],
    data_model=[
        DataEntity("Counter",
                   ["key = client_id + window", "count", "window_start / TTL"],
                   store="Redis — in-memory, atomic increments via Lua, TTL for auto-cleanup."),
        DataEntity("Rule",
                   ["scope (api/tier)", "limit", "window size", "algorithm"],
                   store="Config store / cache, hot-reloaded."),
    ],
    high_level=(
        "Requests hit the **API gateway**, where the rate-limiter middleware "
        "extracts the client identity and looks up the applicable rule. It runs an "
        "**atomic counter operation in Redis** (a Lua script so check-and-increment "
        "is race-free) and either forwards the request to the service or short-"
        "circuits with a 429. Redis is shared across all gateway nodes so the limit "
        "is enforced cluster-wide, not per node.\n\n"
        "If Redis is briefly unavailable, the limiter **fails open** (allow) or "
        "degrades to a local approximate limit — you never want the safety "
        "mechanism to become the outage."
    ),
    request_flows=[
        "Request -> gateway extracts client id and matches a rule.",
        "Gateway runs atomic INCR/Lua against Redis for the client's window.",
        "Under limit -> forward to service and return X-RateLimit-* headers.",
        "Over limit -> return 429 with Retry-After.",
    ],
    deep_dives=[
        DeepDive("Algorithms and their trade-offs",
                 "**Token bucket** refills tokens at a fixed rate and lets each request "
                 "spend one; it allows controlled bursts and is the common default. "
                 "**Leaking bucket** enforces a smooth outflow like a queue. **Fixed "
                 "window counter** is trivial but allows a 2x burst at the window "
                 "boundary. **Sliding window log** keeps a timestamp per request — exact "
                 "but memory-heavy. **Sliding window counter** blends the previous and "
                 "current fixed windows for near-exact accuracy at low cost.",
                 ["Token bucket: bursts allowed, simple, memory-cheap.",
                  "Sliding window log: exact, but O(requests) memory per key.",
                  "Sliding window counter: best accuracy/cost balance for most systems."]),
        DeepDive("Distributed accuracy",
                 "With many gateway nodes, per-node counters drift and clients can exceed "
                 "limits N-fold. Centralizing counters in Redis with atomic Lua scripts "
                 "keeps a single source of truth. To cut Redis round trips at extreme "
                 "scale, nodes can maintain a small local budget and reconcile "
                 "periodically, trading a little accuracy for latency.",
                 ["Centralized counters: accurate, but Redis is a hot dependency.",
                  "Local + sync: lower latency, slightly looser limits."]),
        DeepDive("Reliability",
                 "The limiter sits on the hot path of every request, so it must be fast "
                 "and must degrade gracefully. Decide fail-open vs fail-closed per "
                 "endpoint: fail-open for general traffic (availability first), fail-"
                 "closed for sensitive/expensive endpoints (protection first).",
                 ["Fail-open protects availability but weakens protection during Redis outages.",
                  "Fail-closed protects the backend but can cause a self-inflicted outage."]),
        DeepDive("Cost & security",
                 "Rate limiting is itself a security control — it blunts credential-"
                 "stuffing, scraping and volumetric abuse, and it caps the cost of "
                 "expensive endpoints. Layer it with per-IP limits at the edge (CDN/WAF) "
                 "so attackers are filtered before reaching your origin.",
                 ["Edge limits are cheap and broad; app limits are precise but closer to your cost center."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Rate-limiting algorithms",
            ["Algorithm", "Bursts", "Memory", "Accuracy"],
            [["Token bucket", "Allowed (bounded)", "Low", "Good"],
             ["Leaking bucket", "Smoothed out", "Low", "Good"],
             ["Fixed window", "2x at edges", "Very low", "Rough"],
             ["Sliding window log", "None", "High", "Exact"],
             ["Sliding window counter", "Minimal", "Low", "Very good"]],
        ),
    ],
    bottlenecks=[
        "Redis becomes a hot dependency — cluster it and shard counters by key.",
        "Network round trip per request — use local budgets + async sync at extreme QPS.",
        "Hot single key (one abusive client) — shard the key or apply a stricter local cap.",
    ],
    security=[
        "Layer edge (per-IP, WAF) and application (per-key) limits.",
        "Return generic 429s; don't leak internal limits that help attackers tune.",
        "Combine with anomaly detection to catch distributed low-and-slow abuse.",
    ],
    wrap_up=(
        "A production rate limiter lives at the gateway, uses a sliding-window "
        "counter over atomic Redis operations for cluster-wide accuracy, returns "
        "standard 429 headers, and fails gracefully. It's both a reliability and a "
        "security control. Scale further with counter sharding and edge pre-filtering."
    ),
))

# ===========================================================================
# Chapter 5 — Design Consistent Hashing
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v1_ch5", number=5, volume=1,
    title="Design Consistent Hashing",
    tagline="Distribute keys across nodes so adding or removing a node moves almost nothing.",
    diagram_id="v1_ch5",
    overview=(
        "When you spread data or load across N servers, the naive approach is "
        "`hash(key) % N`. It works until N changes — then almost every key remaps, "
        "causing a storm of cache misses or data movement. **Consistent hashing** "
        "places nodes and keys on a ring so that adding or removing a node only "
        "affects keys in its immediate neighborhood. It's the foundation of "
        "distributed caches, Dynamo-style databases, and CDN routing."
    ),
    clarifying=[
        ClarifyQ("Use case",
                 "Are we partitioning a cache, a database, or routing requests?",
                 "The cost of remapping differs: cache misses are cheap-ish, data movement is expensive.",
                 "A distributed cache/data store where minimizing key movement is critical."),
        ClarifyQ("Node heterogeneity",
                 "Do nodes have equal capacity?",
                 "Unequal nodes need weighting via a different number of virtual nodes.",
                 "Mostly homogeneous, but support weighting for future mixed fleets."),
        ClarifyQ("Scale",
                 "How many physical nodes and how often do they change?",
                 "Frequent membership changes make minimal remapping and even distribution essential.",
                 "Tens to hundreds of nodes with routine scaling and failures."),
    ],
    requirements=Requirements(
        functional=[
            "Map any key deterministically to a node",
            "Add/remove nodes with minimal key remapping",
            "Support weighting for heterogeneous nodes",
        ],
        non_functional=[
            "Even key distribution (avoid hot nodes)",
            "O(log n) lookup",
            "Minimal metadata overhead",
        ],
        out_of_scope=["Replication strategy (covered in the KV store chapter)"],
    ),
    estimation=Estimation(
        assumptions=["100 physical nodes", "~150 virtual nodes each for even spread"],
        rows=[
            EstimationRow("Ring positions", "100 x 150", "~ 15,000 virtual nodes"),
            EstimationRow("Keys moved on 1 node change", "~ 1/N of keys", "~ 1%"),
            EstimationRow("Lookup cost", "binary search on ring", "O(log n)"),
        ],
        notes=["Naive modulo hashing moves ~ (N-1)/N of keys on a change — near 100%."],
    ),
    apis=[
        APIEndpoint("add_node(node)", "Insert a node's virtual points onto the ring; remap only neighboring key ranges."),
        APIEndpoint("remove_node(node)", "Remove its virtual points; its keys move to the next clockwise nodes."),
        APIEndpoint("get_node(key)", "Hash the key, walk clockwise to the first virtual node, return its physical node."),
    ],
    data_model=[
        DataEntity("Hash ring",
                   ["sorted map: position -> virtual node", "virtual node -> physical node"],
                   store="In-memory sorted structure (e.g. TreeMap / skip list) on each client or router."),
    ],
    high_level=(
        "Map the output of a hash function onto a **ring** (0 to 2^m). Each physical "
        "node is hashed to several positions on the ring — its **virtual nodes**. To "
        "locate a key, hash it and walk clockwise to the first virtual node; that "
        "node's physical server owns the key.\n\n"
        "When a node joins, only the keys between it and its predecessor move to it. "
        "When a node leaves, its keys move to the next node clockwise. Everything "
        "else stays put — that's the whole point."
    ),
    request_flows=[
        "Hash the key onto the ring.",
        "Binary-search clockwise for the next virtual node.",
        "Resolve virtual node -> physical node and route the request.",
        "On membership change, only the affected arc's keys move.",
    ],
    deep_dives=[
        DeepDive("Why virtual nodes matter",
                 "With one ring position per node, distribution is lumpy — some nodes "
                 "own huge arcs, others tiny ones, and removing a node dumps its entire "
                 "load onto a single neighbor. Giving each node ~100-200 virtual nodes "
                 "smooths the distribution and spreads a departing node's keys across "
                 "many survivors. More virtual nodes = smoother balance but more "
                 "metadata to store and search.",
                 ["Few vnodes: less memory, lumpy load.",
                  "Many vnodes: even load, more metadata and lookup overhead."]),
        DeepDive("Scalability & rebalancing",
                 "Consistent hashing turns scaling into a local operation: adding "
                 "capacity moves ~1/N of keys instead of nearly all of them. For a data "
                 "store this means the rebalance transfers a bounded slice; for a cache "
                 "it means only a small fraction of keys briefly miss. Weighted vnodes "
                 "let you add bigger machines and give them proportionally more of the ring.",
                 ["Uniform vnode counts assume equal nodes; weight them for mixed hardware."]),
        DeepDive("Reliability & hot spots",
                 "Even with vnodes, a single very popular key still lands on one node — "
                 "consistent hashing balances key *ranges*, not per-key popularity. Pair "
                 "it with replication (store each key on the next R nodes clockwise) for "
                 "availability, and with a small local cache for hot keys.",
                 ["Consistent hashing solves distribution, not per-key hotness."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Modulo vs consistent hashing",
            ["Approach", "Keys moved on node change", "Distribution", "Complexity"],
            [["hash(key) % N", "~ all keys", "Even", "Trivial"],
             ["Consistent hashing", "~ 1/N of keys", "Even (with vnodes)", "Moderate"]],
        ),
    ],
    bottlenecks=[
        "Uneven distribution without enough virtual nodes — increase vnode count.",
        "Hot keys concentrate on one node — add replication and local caching.",
        "Ring metadata sync across clients — distribute via a coordination service.",
    ],
    security=[
        "Use a well-distributed hash (e.g. MD5/murmur) to prevent adversarial key clustering.",
        "Protect the membership/coordination channel so a bad actor can't remap traffic.",
    ],
    wrap_up=(
        "Consistent hashing makes membership changes cheap by localizing key "
        "movement, and virtual nodes keep the distribution even. It's used by "
        "Dynamo, Cassandra, memcached clients and CDNs. Combine it with replication "
        "for availability and local caching for hot keys."
    ),
))

# ===========================================================================
# Chapter 6 — Design a Key-Value Store
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v1_ch6", number=6, volume=1,
    title="Design a Key-Value Store",
    tagline="A distributed, highly available store with tunable consistency (Dynamo-style).",
    diagram_id="v1_ch6",
    overview=(
        "A key-value store exposes just `get(key)` and `put(key, value)` but the "
        "interview is about the distributed systems underneath: partitioning, "
        "replication, consistency, conflict resolution and failure handling. The "
        "canonical answer is a **Dynamo-style, leaderless** design that favors "
        "availability and partition tolerance with **tunable consistency** via "
        "quorums. It's the clearest place to demonstrate you understand CAP."
    ),
    clarifying=[
        ClarifyQ("Consistency model",
                 "Do we need strong consistency, or is eventual consistency acceptable?",
                 "This is the core CAP decision and dictates the whole architecture.",
                 "Highly available with tunable consistency; default to eventual, allow strong via quorum."),
        ClarifyQ("Value size",
                 "Small values or large blobs?",
                 "Large values change storage engine and network assumptions.",
                 "Small values (< ~10 KB); large blobs belong in object storage."),
        ClarifyQ("Scale",
                 "How much data and throughput?",
                 "Determines partition count and replication factor.",
                 "Petabyte scale, hundreds of thousands of ops/sec, must scale horizontally."),
        ClarifyQ("Availability",
                 "Must writes succeed during network partitions?",
                 "If yes, we accept temporary inconsistency (AP); if no, we choose CP.",
                 "Writes must remain available (AP), reconciling conflicts later."),
    ],
    requirements=Requirements(
        functional=["get(key) / put(key, value)", "Tunable consistency per operation"],
        non_functional=[
            "High availability and partition tolerance",
            "Horizontal scalability",
            "Low latency reads/writes",
            "Durability via replication",
        ],
        out_of_scope=["Rich queries, secondary indexes, transactions across keys"],
    ),
    estimation=Estimation(
        assumptions=["1 PB data", "Replication factor N = 3", "200k ops/sec"],
        rows=[
            EstimationRow("Raw storage", "1 PB x 3 replicas", "~ 3 PB"),
            EstimationRow("Nodes (at ~20 TB each)", "3 PB / 20 TB", "~ 150 nodes"),
            EstimationRow("Per-node ops", "200k / 150", "~ 1,300 ops/s"),
        ],
        notes=["Replication multiplies storage by N; plan capacity accordingly."],
    ),
    apis=[
        APIEndpoint("get(key) -> value", "Reads from R replicas; returns the newest version (or resolves conflicts)."),
        APIEndpoint("put(key, value)", "Writes to W replicas; succeeds when W acknowledge."),
    ],
    data_model=[
        DataEntity("Key-value pair",
                   ["key", "value", "version (vector clock)", "timestamp"],
                   store="Local storage engine per node (LSM-tree/SSTables) for high write throughput."),
    ],
    high_level=(
        "Data is partitioned across nodes with **consistent hashing** and each key "
        "is replicated to the next **N** nodes clockwise. There is **no leader** — "
        "any node can coordinate a request (a coordinator). Consistency is tuned "
        "per operation with quorum parameters **(N, W, R)**: a write waits for W "
        "acknowledgments, a read gathers R responses, and **W + R > N** guarantees "
        "a read sees the latest write.\n\n"
        "Nodes track membership and failures with a **gossip protocol**. Divergent "
        "replicas are detected and repaired using **Merkle trees** (anti-entropy). "
        "Conflicting concurrent writes are versioned with **vector clocks** and "
        "reconciled at read time."
    ),
    request_flows=[
        "put: coordinator hashes key -> N replicas; write returns when W ack.",
        "get: coordinator reads from R replicas; if versions differ, reconcile.",
        "Gossip continuously spreads membership and failure info.",
        "Anti-entropy (Merkle trees) repairs replicas in the background.",
    ],
    deep_dives=[
        DeepDive("CAP and tunable consistency",
                 "Under a network partition you can keep the system Consistent or "
                 "Available, not both. This design chooses **availability** and reaches "
                 "consistency through quorums. Setting W+R>N gives strong read-after-"
                 "write; lowering W or R trades consistency for latency and availability. "
                 "You expose these knobs so callers pick per-operation guarantees.",
                 ["W=N,R=1: fast reads, slow/less-available writes.",
                  "W=1,R=N: fast writes, slower reads.",
                  "W+R>N: strong consistency at the cost of latency."]),
        DeepDive("Conflict resolution",
                 "With concurrent writes to different replicas, versions diverge. **Vector "
                 "clocks** capture causality so the system can tell a newer version from a "
                 "true conflict. Real conflicts are resolved by last-write-wins (simple, "
                 "can lose data) or by returning both versions for the application to merge "
                 "(e.g. shopping-cart union).",
                 ["LWW is simple but silently drops concurrent updates.",
                  "Application merge preserves data but pushes complexity to clients."]),
        DeepDive("Failure handling & reliability",
                 "Temporary node failures use **hinted handoff**: a healthy node "
                 "temporarily stores writes for the down node and forwards them on "
                 "recovery. Permanent failures trigger replica repair via Merkle-tree "
                 "comparison, which finds divergent ranges without scanning all data. "
                 "Gossip avoids a central membership bottleneck.",
                 ["Hinted handoff keeps writes available but can briefly violate quorum durability."]),
        DeepDive("Cost & scalability",
                 "Replication factor N directly multiplies storage cost — N=3 is the "
                 "common durability/cost sweet spot. LSM-tree engines give cheap, high-"
                 "throughput writes at the cost of read/compaction overhead. Scaling is "
                 "linear: add nodes, the ring rebalances a bounded slice of keys.",
                 ["Higher N: more durability, more cost.",
                  "LSM writes: fast, but compaction consumes IO and CPU."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Quorum settings (N=3)",
            ["W", "R", "Guarantee", "Best for"],
            [["3", "1", "Fast, consistent reads", "Read-heavy, tolerant of slow writes"],
             ["1", "3", "Fast writes", "Write-heavy, tolerant of slow reads"],
             ["2", "2", "Balanced strong consistency", "General purpose"]],
        ),
    ],
    bottlenecks=[
        "Hot keys overload their replica set — add caching or key splitting.",
        "Compaction IO on LSM engines — schedule and throttle it.",
        "Wide quorums increase tail latency — tune W/R to the workload.",
    ],
    security=[
        "Encrypt data at rest and in transit between nodes.",
        "Authenticate inter-node gossip to prevent rogue nodes joining the ring.",
        "Per-namespace access control for multi-tenant clusters.",
    ],
    wrap_up=(
        "A Dynamo-style KV store combines consistent hashing (partitioning), "
        "replication (durability), quorums (tunable consistency), vector clocks "
        "(conflict detection), gossip (membership) and Merkle trees (repair). It's "
        "the reference design for AP systems and a showcase of CAP trade-offs."
    ),
))


# ===========================================================================
# Chapter 7 — Design a Unique ID Generator in Distributed Systems
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v1_ch7", number=7, volume=1,
    title="Design a Unique ID Generator in Distributed Systems",
    tagline="Generate unique, roughly time-sortable 64-bit IDs without a central bottleneck.",
    diagram_id="v1_ch7",
    overview=(
        "Many systems need unique IDs — for database primary keys, messages, "
        "orders. Auto-increment columns don't work across a distributed fleet, and "
        "UUIDs are unique but large and not sortable. The interview target is a "
        "**Snowflake-style** 64-bit ID that is unique, compact, and roughly "
        "**time-sortable** so it doubles as a rough ordering key."
    ),
    clarifying=[
        ClarifyQ("Properties",
                 "Must IDs be sortable by time, or just unique?",
                 "Sortability rules out random UUIDs and points to a timestamp-based layout.",
                 "Unique, numeric, and roughly increasing over time."),
        ClarifyQ("Scale",
                 "How many IDs per second, across how many machines?",
                 "Throughput sets the sequence-bit budget per millisecond per node.",
                 "Up to ~thousands of IDs/ms per node, thousands of nodes."),
        ClarifyQ("Constraints",
                 "Any tolerance for a central service, or must generation be local?",
                 "A central ticket server is simpler but a single point of failure.",
                 "Fully decentralized — each node generates IDs locally."),
    ],
    requirements=Requirements(
        functional=["Generate globally unique IDs", "Roughly time-ordered", "64-bit numeric"],
        non_functional=["High throughput", "No single point of failure", "Low latency (local)"],
        out_of_scope=["Human-readable / vanity IDs"],
    ),
    estimation=Estimation(
        assumptions=["12 sequence bits per ms", "41 timestamp bits"],
        rows=[
            EstimationRow("IDs per ms per node", "2^12", "4,096"),
            EstimationRow("IDs per sec per node", "4,096 x 1000", "~ 4.1M/s"),
            EstimationRow("Timestamp lifespan", "2^41 ms", "~ 69 years"),
            EstimationRow("Nodes addressable", "2^10 (5 dc + 5 machine)", "1,024"),
        ],
        notes=["Bit allocation is a tunable trade-off between lifespan, node count and throughput."],
    ),
    apis=[
        APIEndpoint("next_id() -> int64", "Returns a new unique, time-sortable 64-bit ID locally."),
    ],
    data_model=[
        DataEntity("ID (64 bits)",
                   ["1 bit sign (unused)", "41 bits timestamp (ms since epoch)",
                    "5 bits datacenter", "5 bits machine", "12 bits sequence"],
                   store="No storage — computed in memory from clock + machine id + counter."),
    ],
    high_level=(
        "Each node composes an ID from four parts: the current **timestamp** (ms "
        "since a custom epoch), its **datacenter id**, its **machine id**, and a "
        "per-millisecond **sequence** counter. Within a millisecond the sequence "
        "increments; when it overflows, the node waits for the next millisecond. "
        "Because the timestamp occupies the high bits, IDs sort roughly by "
        "creation time. No coordination is needed at generation time — only a "
        "one-time assignment of machine ids."
    ),
    request_flows=[
        "Read current time -> timestamp bits.",
        "Concatenate datacenter + machine bits (assigned at startup).",
        "Increment the per-ms sequence; wait if it overflows.",
        "Combine into a 64-bit integer and return.",
    ],
    deep_dives=[
        DeepDive("Clock issues",
                 "The design assumes a monotonic clock. If NTP moves the clock "
                 "**backwards**, a node could mint duplicate or out-of-order IDs. Handle "
                 "it by detecting regression and either waiting until the clock catches "
                 "up or refusing to generate until it does. Use a monotonic clock source "
                 "where available.",
                 ["Waiting on clock regression stalls generation briefly but preserves uniqueness."]),
        DeepDive("Bit budget trade-offs",
                 "The 64 bits are a fixed budget. More timestamp bits = longer lifespan "
                 "but fewer for nodes/sequence. More sequence bits = higher per-node "
                 "throughput but a shorter epoch or fewer nodes. Tune the split to your "
                 "actual scale rather than copying Twitter's exactly.",
                 ["Reallocating bits changes lifespan vs node count vs throughput."]),
        DeepDive("Alternatives & when to use them",
                 "A **central ticket server** (auto-increment) is dead simple but a SPOF "
                 "and a bottleneck. **UUIDv4** needs zero coordination and is collision-"
                 "safe but is 128-bit and unsortable, hurting index locality. **Segment/"
                 "range allocation** (each node grabs a block of ids from a central store) "
                 "reduces coordination while keeping compact integers.",
                 ["UUID: no coordination, but big and index-unfriendly.",
                  "Ticket server: simple, but a bottleneck and SPOF.",
                  "Snowflake: decentralized, compact, sortable — the usual winner."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "ID generation approaches",
            ["Approach", "Sortable", "Coordination", "Size"],
            [["Auto-increment", "Yes", "Central (SPOF)", "Compact"],
             ["UUIDv4", "No", "None", "128-bit"],
             ["Snowflake", "Roughly", "One-time machine id", "64-bit"],
             ["Range allocation", "Roughly", "Occasional central", "Compact"]],
        ),
    ],
    bottlenecks=[
        "Sequence overflow within a millisecond — add sequence bits or wait to next ms.",
        "Machine-id assignment at scale — automate via a coordination service (e.g. ZooKeeper).",
        "Clock skew across nodes — bound with NTP and regression handling.",
    ],
    security=[
        "Sequential IDs can leak volume/business metrics — add an opaque public alias if enumeration is a concern.",
        "Never encode secrets into IDs; they are shared freely.",
    ],
    wrap_up=(
        "Snowflake-style IDs give unique, compact, roughly-sortable identifiers with "
        "no runtime coordination. The craft is in allocating the 64 bits to your "
        "scale and handling clock regression safely."
    ),
))

# ===========================================================================
# Chapter 8 — Design a URL Shortener
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v1_ch8", number=8, volume=1,
    title="Design a URL Shortener",
    tagline="Map long URLs to short codes and redirect at massive, read-heavy scale.",
    diagram_id="v1_ch8",
    overview=(
        "A URL shortener (like bit.ly) creates a short alias for a long URL and "
        "redirects visitors. It looks trivial but exercises core skills: unique ID "
        "generation, an extremely **read-heavy** access pattern, caching, and the "
        "subtle choice of HTTP redirect type. The design lives or dies on the "
        "redirect hot path."
    ),
    clarifying=[
        ClarifyQ("Functional scope",
                 "Custom aliases? Expiration? Analytics on clicks?",
                 "Each feature changes the data model and write path.",
                 "Auto-generated short codes, optional expiry, basic click counting."),
        ClarifyQ("Scale",
                 "How many new URLs per day and what's the read:write ratio?",
                 "Redirects vastly outnumber creations, which makes this a caching problem.",
                 "~100M new URLs/day, read:write ~ 100:1."),
        ClarifyQ("Code length",
                 "How short must the code be, and over what lifetime?",
                 "Length bounds the keyspace: 7 base62 chars gives ~3.5 trillion codes.",
                 "7-character base62 codes."),
        ClarifyQ("Redirect type",
                 "Should redirects be cacheable by browsers (301) or trackable (302)?",
                 "301 offloads traffic but prevents click tracking; 302 keeps every hit.",
                 "302 by default so we can count clicks; allow 301 where tracking is unneeded."),
    ],
    requirements=Requirements(
        functional=["Shorten a long URL to a unique short code", "Redirect short -> long",
                    "Optional expiration and click counts"],
        non_functional=[
            "Very low redirect latency (read hot path)",
            "High availability (redirects must not fail)",
            "Scale to billions of stored URLs",
        ],
        out_of_scope=["Full analytics platform", "Spam/phishing content scanning (mention as security)"],
    ),
    estimation=Estimation(
        assumptions=["100M new URLs/day", "Read:write 100:1", "Each row ~ 500 bytes", "Retain 5 years"],
        rows=[
            EstimationRow("Write QPS", "100M / 86,400", "~ 1,160 QPS"),
            EstimationRow("Read (redirect) QPS", "1,160 x 100", "~ 116,000 QPS"),
            EstimationRow("URLs in 5 years", "100M x 365 x 5", "~ 182 billion"),
            EstimationRow("Storage", "182B x 500 B", "~ 91 TB"),
            EstimationRow("Keyspace (7 base62)", "62^7", "~ 3.5 trillion"),
        ],
        notes=["116k read QPS means redirects must be served largely from cache, not the DB."],
    ),
    apis=[
        APIEndpoint("POST /v1/urls {long_url}", "Creates a short code; returns the short URL.", "Idempotent per long_url if dedupe is enabled."),
        APIEndpoint("GET /{short_code}", "Looks up and issues a 301/302 redirect to the long URL."),
    ],
    data_model=[
        DataEntity("URL mapping",
                   ["short_code (PK)", "long_url", "created_at", "expires_at", "click_count"],
                   store="Sharded KV / NoSQL keyed by short_code for O(1) lookups; cache in front."),
    ],
    high_level=(
        "**Write path:** generate a unique 64-bit id (Snowflake or a counter), "
        "**base62-encode** it into a 7-char code, store the `code -> long_url` "
        "mapping, and return the short URL.\n\n"
        "**Read path (the hot one):** on `GET /{code}`, check the **cache** first; "
        "on a hit, redirect immediately. On a miss, read the KV store, populate the "
        "cache, then redirect. Because reads dominate 100:1 and the working set of "
        "popular links is small, cache hit rates are very high.\n\n"
        "Base62 encoding of a unique integer guarantees no collisions without a "
        "read-before-write check. If you hash the URL instead, you must handle "
        "collisions explicitly."
    ),
    request_flows=[
        "Create: id -> base62 -> store mapping -> return short URL.",
        "Redirect: cache hit -> 302 immediately.",
        "Redirect: cache miss -> read KV -> populate cache -> 302.",
        "Async: increment click_count off the hot path.",
    ],
    deep_dives=[
        DeepDive("Encoding vs hashing",
                 "Encoding a **unique counter/Snowflake id** in base62 is collision-free "
                 "by construction and yields short codes. **Hashing the long URL** (e.g. "
                 "MD5, then truncate) can produce the same code for different URLs, so you "
                 "need collision detection and retries — extra reads on the write path. "
                 "Encoding is generally cleaner.",
                 ["Encoding: no collisions, needs a unique id source.",
                  "Hashing: no id source, but must resolve collisions."]),
        DeepDive("301 vs 302 redirects",
                 "A **301 (permanent)** is cached by browsers, so subsequent visits skip "
                 "your servers entirely — great for load, but you lose click analytics. A "
                 "**302 (temporary)** routes every visit through you, enabling tracking at "
                 "the cost of more traffic. Choose per product need; many shorteners use "
                 "302 to keep analytics.",
                 ["301: less load, no per-click tracking.",
                  "302: full tracking, more traffic to serve."]),
        DeepDive("Scalability & cost",
                 "The redirect path is the scaling challenge. A CDN or edge cache in front "
                 "of hot codes plus a Redis layer absorbs the bulk of 116k QPS, leaving "
                 "the database for cold lookups and writes. Storage is cheap relative to "
                 "the read traffic; the KV store shards cleanly by short_code.",
                 ["Caching cuts DB load dramatically but adds an invalidation concern on expiry/edits."]),
        DeepDive("Reliability",
                 "Redirects should essentially never fail. Run the read tier and cache "
                 "multi-AZ, and treat writes as the less-critical path — if creation is "
                 "briefly degraded, existing links still resolve. Expired links return a "
                 "clean 404/410 rather than a broken redirect.",
                 ["Prioritizing the read path means write availability can be relaxed."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Key design choices",
            ["Decision", "Option A", "Option B"],
            [["Code generation", "Encode unique id (no collisions)", "Hash URL (needs collision handling)"],
             ["Redirect", "301 permanent (less load)", "302 temporary (trackable)"],
             ["Store", "NoSQL KV (scales, simple)", "SQL (rich queries, harder to shard)"]],
        ),
    ],
    bottlenecks=[
        "Redirect QPS on the database — front it with CDN + Redis cache.",
        "Hot-key cache stampede on viral links — request coalescing.",
        "Counter/id generation throughput — use Snowflake or ranged counters.",
    ],
    security=[
        "Scan or blocklist destinations to prevent phishing/malware shortening.",
        "Rate-limit creation per account to stop abuse.",
        "Avoid predictable sequential codes if enumeration of private links is a risk.",
    ],
    wrap_up=(
        "A URL shortener is fundamentally a read-optimized KV lookup: generate a "
        "unique id, base62-encode it, store the mapping, and serve redirects mostly "
        "from cache. The interesting decisions are encoding vs hashing and 301 vs "
        "302. Scale the read path with caching and a CDN."
    ),
))


# ===========================================================================
# Chapter 9 — Design a Web Crawler
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v1_ch9", number=9, volume=1,
    title="Design a Web Crawler",
    tagline="Fetch and process the web at scale — politely, without loops or duplicates.",
    diagram_id="v1_ch9",
    overview=(
        "A web crawler starts from seed URLs, downloads pages, extracts links, and "
        "repeats — feeding a search index or data pipeline. At web scale the hard "
        "parts are **politeness** (not hammering a host), **deduplication** (URLs "
        "and content), avoiding **traps**, and doing it all across a distributed "
        "fleet. The **URL frontier** is the component that ties it together."
    ),
    clarifying=[
        ClarifyQ("Scope",
                 "HTML only, or images/PDFs too? Whole web or a subset?",
                 "Content types and breadth change storage and parsing needs.",
                 "HTML primarily, targeting a large but bounded set of sites."),
        ClarifyQ("Scale",
                 "How many pages per month, and how fresh must they be?",
                 "Throughput and refresh cadence size the fleet and the frontier.",
                 "~1 billion pages/month, re-crawl important pages more often."),
        ClarifyQ("Politeness",
                 "Must we honor robots.txt and per-host rate limits?",
                 "Politeness prevents bans and legal issues; it constrains concurrency per host.",
                 "Yes — respect robots.txt and cap requests per host."),
        ClarifyQ("Constraints",
                 "How do we avoid crawling the same content or infinite URL spaces?",
                 "Dedup and trap detection prevent wasted work and loops.",
                 "Dedup URLs and content hashes; detect spider traps."),
    ],
    requirements=Requirements(
        functional=["Crawl from seeds", "Extract and follow links", "Store parsed content"],
        non_functional=[
            "Scalable and distributed",
            "Polite (robots.txt, per-host limits)",
            "Robust to traps, duplicates, malformed pages",
            "Extensible to new content types",
        ],
        out_of_scope=["Ranking/indexing algorithms (downstream of the crawler)"],
    ),
    estimation=Estimation(
        assumptions=["1B pages/month", "Average page ~ 500 KB", "Store compressed ~ 100 KB"],
        rows=[
            EstimationRow("Crawl QPS", "1B / (30 x 86,400)", "~ 386 pages/s"),
            EstimationRow("Ingress bandwidth", "386 x 500 KB", "~ 193 MB/s"),
            EstimationRow("Storage / month", "1B x 100 KB", "~ 100 TB/mo"),
        ],
        notes=["Bandwidth and storage dominate; compress aggressively and dedup content."],
    ),
    apis=[
        APIEndpoint("(internal) frontier.add(url)", "Enqueue a URL with priority and host for polite scheduling."),
        APIEndpoint("(internal) frontier.next()", "Return the next URL that respects per-host politeness."),
    ],
    data_model=[
        DataEntity("URL frontier entry",
                   ["url", "priority", "host", "next_fetch_time"],
                   store="Distributed queues: priority queues + per-host politeness queues."),
        DataEntity("Seen set",
                   ["url_hash / content_hash"],
                   store="Bloom filter + backing store for space-efficient dedup."),
        DataEntity("Content store",
                   ["url", "fetched_at", "compressed_html"],
                   store="Object storage / distributed FS."),
    ],
    high_level=(
        "The **URL frontier** holds URLs to crawl, balancing two goals: **priority** "
        "(crawl important/fresh pages first) and **politeness** (limit concurrent "
        "requests per host). Distributed **downloaders** fetch pages, respecting "
        "robots.txt and DNS caching. A **parser** extracts links and normalizes "
        "them. A **dedup** stage drops already-seen URLs (via a Bloom filter) and "
        "near-duplicate content (via content hashing). New links go back into the "
        "frontier; parsed content is stored for downstream indexing."
    ),
    request_flows=[
        "Seed URLs -> frontier.",
        "Downloader pulls next polite URL -> fetches HTML.",
        "Parser extracts + normalizes links.",
        "Dedup drops seen URLs/content; new links -> frontier.",
        "Content -> storage for indexing.",
    ],
    deep_dives=[
        DeepDive("The URL frontier",
                 "The frontier is the crawler's brain. It uses **priority queues** so "
                 "high-value pages are crawled sooner, and **per-host queues** with timing "
                 "so a single site isn't overwhelmed. A router maps each URL to the right "
                 "host queue. Getting this balance wrong either wastes capacity or gets "
                 "you rate-limited/banned.",
                 ["More per-host concurrency: faster, but risks bans.",
                  "Strict politeness: safe, but lower throughput."]),
        DeepDive("Deduplication & traps",
                 "URL dedup uses a **Bloom filter** for memory efficiency (accepting a "
                 "tiny false-positive rate that skips a few pages). Content dedup hashes "
                 "the page to skip mirror/near-duplicate pages. **Spider traps** — "
                 "infinite calendars, session-id URLs — are detected via depth/URL-length "
                 "limits and pattern rules.",
                 ["Bloom filters save memory but can rarely skip a new URL.",
                  "Aggressive trap rules may skip legitimate deep pages."]),
        DeepDive("Scalability & reliability",
                 "Downloaders scale horizontally and are stateless; the frontier and seen-"
                 "set are the shared state to partition. Checkpoint progress so a crashed "
                 "node's work resumes elsewhere. DNS resolution is cached to avoid it "
                 "becoming a bottleneck.",
                 ["Central frontier is a scaling limit — shard it by host hash."]),
        DeepDive("Cost & freshness",
                 "Re-crawling everything constantly is wasteful. Prioritize by change "
                 "frequency and importance so budget goes to pages that actually change. "
                 "Compression and content dedup cut storage/bandwidth cost significantly.",
                 ["Frequent re-crawl: fresher data, higher cost.",
                  "Change-based scheduling: efficient, needs good change estimation."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Crawler design tensions",
            ["Concern", "Aggressive", "Conservative"],
            [["Per-host rate", "Faster, risks bans", "Polite, slower"],
             ["Dedup memory", "Exact set (RAM heavy)", "Bloom filter (tiny error)"],
             ["Freshness", "Re-crawl often (costly)", "Change-based (efficient)"]],
        ),
    ],
    bottlenecks=[
        "Central frontier — shard by host to scale.",
        "DNS lookups — cache aggressively.",
        "Seen-set memory — Bloom filters + tiered storage.",
        "Slow hosts blocking workers — timeouts and per-host isolation.",
    ],
    security=[
        "Honor robots.txt and legal crawl boundaries.",
        "Sandbox parsing to guard against malicious pages.",
        "Rate-limit yourself to avoid being classified as an attacker.",
    ],
    wrap_up=(
        "A scalable crawler is really a well-designed URL frontier plus stateless "
        "downloaders, robust dedup, and polite scheduling. Prioritize by importance "
        "and change frequency to spend crawl budget wisely, and shard the shared "
        "state to scale out."
    ),
))

# ===========================================================================
# Chapter 10 — Design a Notification System
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v1_ch10", number=10, volume=1,
    title="Design a Notification System",
    tagline="Deliver push, SMS and email reliably across channels at scale.",
    diagram_id="v1_ch10",
    overview=(
        "A notification system lets many services send messages to users across "
        "push (APNs/FCM), SMS and email. The design centers on **decoupling** "
        "producers from delivery via queues, **reliable delivery** with retries and "
        "idempotency, respecting **user preferences**, and integrating flaky "
        "**third-party gateways** without letting them stall the system."
    ),
    clarifying=[
        ClarifyQ("Channels",
                 "Which channels — push, SMS, email, in-app?",
                 "Each channel has different providers, latency and reliability characteristics.",
                 "Push, SMS and email, extensible to more."),
        ClarifyQ("Delivery guarantee",
                 "At-least-once or exactly-once? Ordering required?",
                 "Exactly-once is hard; at-least-once + idempotency is the usual pragmatic choice.",
                 "At-least-once with dedup; ordering not guaranteed."),
        ClarifyQ("Volume",
                 "How many notifications per day, and are there spikes?",
                 "Spiky volume (e.g. a broadcast) is exactly why we need queues.",
                 "~100M/day with large broadcast spikes."),
        ClarifyQ("Preferences",
                 "Must we honor opt-outs and quiet hours?",
                 "Sending unwanted notifications harms trust and may break regulations.",
                 "Yes — enforce per-user, per-channel preferences and opt-outs."),
    ],
    requirements=Requirements(
        functional=["Send via push/SMS/email", "Respect user preferences/opt-outs",
                    "Retry failed sends", "Support templates"],
        non_functional=["Reliable at-least-once delivery", "Absorb spikes",
                        "Scale per channel independently", "Avoid duplicate sends"],
        out_of_scope=["Rich campaign analytics", "A/B testing engine"],
    ),
    estimation=Estimation(
        assumptions=["100M notifications/day", "Peak 10x average during broadcasts"],
        rows=[
            EstimationRow("Average send rate", "100M / 86,400", "~ 1,160/s"),
            EstimationRow("Peak send rate", "1,160 x 10", "~ 11,600/s"),
            EstimationRow("Queue buffer for 5-min spike", "11,600 x 300", "~ 3.5M messages"),
        ],
        notes=["Queues absorb the gap between spiky production and provider throughput limits."],
    ),
    apis=[
        APIEndpoint("POST /v1/notifications", "Services submit a notification (recipient, channel, template, data).",
                    "Include an idempotency key to prevent duplicates on retry."),
    ],
    data_model=[
        DataEntity("Notification",
                   ["id", "user_id", "channel", "template_id", "payload", "status", "idempotency_key"],
                   store="Durable store for status/audit; queue holds in-flight work."),
        DataEntity("User preference",
                   ["user_id", "channel", "opted_in", "quiet_hours", "device_tokens"],
                   store="Fast KV lookup on the send path."),
    ],
    high_level=(
        "Services call the **Notification API**, which validates the request, checks "
        "**user preferences**, and enqueues per-channel messages onto a **message "
        "queue**. Channel **workers** pull messages and call the appropriate "
        "provider (APNs/FCM for push, an SMS gateway, an email provider). The queue "
        "**decouples** producers from providers so spikes are buffered and each "
        "channel scales independently. Delivery status, retries and dead-lettering "
        "are tracked per message."
    ),
    request_flows=[
        "Service -> Notification API.",
        "API checks preferences/opt-outs; drops or proceeds.",
        "API enqueues per-channel messages.",
        "Workers pull and call providers; record status.",
        "Failures retry with backoff; poison messages -> dead-letter queue.",
    ],
    deep_dives=[
        DeepDive("Reliability & exactly-once",
                 "Providers and networks fail, so delivery is **at-least-once**: workers "
                 "retry with exponential backoff. To avoid users getting duplicates, each "
                 "notification carries an **idempotency key** and workers dedup on it. "
                 "True exactly-once end to end is impractical because the provider is "
                 "outside your control; at-least-once + dedup is the honest answer.",
                 ["At-least-once + dedup: practical and robust.",
                  "Chasing exactly-once across external providers: usually not worth the complexity."]),
        DeepDive("Handling spikes & backpressure",
                 "A broadcast can produce millions of messages instantly. The queue is the "
                 "shock absorber: producers enqueue quickly and workers drain at a rate "
                 "the providers allow. Rate limits per provider are enforced at the worker "
                 "layer so you don't get throttled or blocked upstream.",
                 ["Big buffers smooth spikes but add delivery latency during surges."]),
        DeepDive("Scalability & cost",
                 "Each channel scales separately — email workers and SMS workers are "
                 "independent pools. SMS is expensive per message, so preference checks "
                 "and deduplication directly control cost. Batching (e.g. digest emails) "
                 "reduces provider fees and user fatigue.",
                 ["Per-channel scaling isolates load but adds operational surface.",
                  "Digesting/batching cuts cost but delays individual messages."]),
        DeepDive("Security & compliance",
                 "Honor opt-outs and regional rules (e.g. anti-spam, quiet hours). Protect "
                 "device tokens and phone numbers as PII, encrypt them, and scope access. "
                 "Templates must be injection-safe so user data can't break out into "
                 "headers or markup.",
                 ["Strict compliance limits reach but protects trust and avoids legal risk."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Delivery guarantees",
            ["Guarantee", "Complexity", "User impact"],
            [["At-most-once", "Low", "May miss messages"],
             ["At-least-once + dedup", "Moderate", "Reliable, no dupes"],
             ["Exactly-once end-to-end", "High/impractical", "Ideal but rarely achievable"]],
        ),
    ],
    bottlenecks=[
        "Provider rate limits — throttle at workers and shard across provider accounts.",
        "Queue backlog during broadcasts — autoscale workers, prioritize transactional over marketing.",
        "Preference lookups on the hot path — cache them.",
    ],
    security=[
        "Treat device tokens/phone/email as PII: encrypt and access-control.",
        "Enforce opt-outs and quiet hours to meet regulations.",
        "Sanitize template inputs to prevent injection.",
    ],
    wrap_up=(
        "The notification system is a queue-centric, per-channel pipeline: validate "
        "and check preferences, enqueue, and let workers deliver with retries and "
        "idempotency. Queues absorb spikes; idempotency prevents duplicates; "
        "per-channel scaling and preference checks control cost and compliance."
    ),
))


# ===========================================================================
# Chapter 11 — Design a News Feed System
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v1_ch11", number=11, volume=1,
    title="Design a News Feed System",
    tagline="Publish posts and assemble personalized feeds with fast reads.",
    diagram_id="v1_ch11",
    overview=(
        "A news feed shows each user a personalized, time-ordered stream of posts "
        "from people they follow. The central decision is **fan-out on write vs "
        "fan-out on read** — precompute each user's feed when a post is created, or "
        "assemble it at read time. Neither is universally right; the celebrity "
        "problem forces a **hybrid**."
    ),
    clarifying=[
        ClarifyQ("Functional scope",
                 "Reverse-chronological or ranked feed? Media or text?",
                 "Ranking adds an ML scoring layer; media adds a CDN/storage path.",
                 "Reverse-chronological to start, with room to add ranking."),
        ClarifyQ("Scale",
                 "How many users, posts/day, and average following count?",
                 "Following distribution (celebrities) determines the fan-out strategy.",
                 "Hundreds of millions of users; some accounts have tens of millions of followers."),
        ClarifyQ("Latency",
                 "What feed-load latency is acceptable?",
                 "Tight read latency pushes toward precomputed feeds (fan-out on write).",
                 "Feed loads in well under a second (p99)."),
        ClarifyQ("Consistency",
                 "Is it OK if a new post takes a few seconds to appear?",
                 "Slight delay lets fan-out happen asynchronously, smoothing write spikes.",
                 "A few seconds of delay is acceptable."),
    ],
    requirements=Requirements(
        functional=["Publish a post", "Build and return a personalized feed", "Follow/unfollow"],
        non_functional=["Fast feed reads (p99 < ~1s)", "Handle celebrity fan-out",
                        "Scale to hundreds of millions of users"],
        out_of_scope=["Feed ranking ML models (mention as an extension)", "Ads insertion"],
    ),
    estimation=Estimation(
        assumptions=["300M DAU", "Each loads feed ~10x/day", "Average 200 followers"],
        rows=[
            EstimationRow("Feed read QPS", "300M x 10 / 86,400", "~ 35,000 QPS"),
            EstimationRow("Post write QPS", "assume 1 post/user/day", "~ 3,500 QPS"),
            EstimationRow("Fan-out writes (avg)", "3,500 x 200 followers", "~ 700,000/s"),
            EstimationRow("Celebrity fan-out", "1 post x 10M followers", "10M writes (must not do synchronously)"),
        ],
        notes=["Celebrity fan-out on write is catastrophic — this is why hybrid exists."],
    ),
    apis=[
        APIEndpoint("POST /v1/posts", "Create a post; triggers fan-out."),
        APIEndpoint("GET /v1/feed", "Return the caller's feed (list of post ids, then hydrate)."),
        APIEndpoint("POST /v1/follow/{user_id}", "Follow a user."),
    ],
    data_model=[
        DataEntity("Post", ["post_id", "author_id", "content_ref", "created_at"],
                   store="Post DB (sharded by post_id); media in blob storage + CDN."),
        DataEntity("Feed cache", ["user_id -> [post_id, ...]"],
                   store="Redis list per user (precomputed feed)."),
        DataEntity("Social graph", ["follower_id", "followee_id"],
                   store="Graph/edge store, sharded by user."),
    ],
    high_level=(
        "On **publish**, the post is written to the Post DB and a **fanout service** "
        "pushes the post id into the **feed cache** of each follower (fan-out on "
        "write). On **read**, the user's precomputed feed ids are fetched from cache "
        "and **hydrated** with post content — fast because the heavy work happened "
        "at write time.\n\n"
        "For **celebrities**, fan-out on write is infeasible (millions of writes per "
        "post), so their posts are **pulled** at read time and merged into the "
        "follower's cached feed. This **hybrid** keeps normal reads fast while "
        "avoiding write storms for hub accounts."
    ),
    request_flows=[
        "Publish -> write Post DB -> enqueue fan-out.",
        "Fan-out worker pushes post_id into followers' feed caches (non-celebrity).",
        "Read -> fetch feed_ids from cache -> merge celebrity posts (pull) -> hydrate content.",
    ],
    deep_dives=[
        DeepDive("Fan-out on write vs read",
                 "**Fan-out on write** precomputes feeds so reads are cheap — ideal for "
                 "the read-heavy pattern — but a post costs O(followers) writes and hub "
                 "accounts explode. **Fan-out on read** is cheap to write but expensive "
                 "and slow to read (gather from everyone you follow). The **hybrid** uses "
                 "write fan-out for normal users and read fan-out (pull) for celebrities.",
                 ["Write fan-out: fast reads, costly writes, bad for celebrities.",
                  "Read fan-out: cheap writes, slow reads.",
                  "Hybrid: fast reads + bounded write cost."]),
        DeepDive("Scalability",
                 "Fan-out is asynchronous via a queue so publish returns immediately and "
                 "write spikes are smoothed. Feed caches are sharded per user. The social "
                 "graph is sharded by user id; celebrity edges are flagged so the fan-out "
                 "worker knows to skip write fan-out for them.",
                 ["Async fan-out adds a few seconds of feed delay, which we accepted."]),
        DeepDive("Cost & storage",
                 "Precomputed feeds duplicate post ids across millions of caches — memory "
                 "cost that you bound by capping feed length (e.g. most recent 1,000 ids) "
                 "and evicting inactive users' feeds, regenerating on demand.",
                 ["Longer cached feeds: better UX, more memory.",
                  "Regenerating inactive feeds: saves memory, adds a cold-load cost."]),
        DeepDive("Reliability & ranking extension",
                 "If a fan-out worker lags, feeds are simply a little stale — degradation, "
                 "not failure. To evolve from chronological to **ranked**, insert a scoring "
                 "service that reorders candidate posts by an ML model at read time; the "
                 "candidate generation (who to show) still uses the same fan-out machinery.",
                 ["Ranking improves relevance but adds read-time latency and complexity."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Fan-out strategy",
            ["Strategy", "Write cost", "Read cost", "Best for"],
            [["On write (push)", "High", "Low", "Normal users"],
             ["On read (pull)", "Low", "High", "Celebrities / inactive users"],
             ["Hybrid", "Bounded", "Low", "Real systems"]],
        ),
    ],
    bottlenecks=[
        "Celebrity fan-out — pull at read time instead of push.",
        "Feed cache memory — cap feed length and evict inactive users.",
        "Hydration fan-out reads — batch and cache post content.",
    ],
    security=[
        "Enforce privacy/visibility rules when fanning out (blocked users, private accounts).",
        "Authorization on feed reads so users only see permitted posts.",
    ],
    wrap_up=(
        "The news feed is a fan-out problem. Precompute normal users' feeds for fast "
        "reads, pull celebrity posts at read time, and run fan-out asynchronously to "
        "smooth spikes. Cap and evict cached feeds to control cost, and layer ranking "
        "on top when relevance matters."
    ),
))

# ===========================================================================
# Chapter 12 — Design a Chat System
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v1_ch12", number=12, volume=1,
    title="Design a Chat System",
    tagline="Real-time 1:1 and group messaging with presence and history.",
    diagram_id="v1_ch12",
    overview=(
        "A chat system (WhatsApp/Messenger) delivers messages in near real time, "
        "shows who's online, and stores history so devices can sync. The defining "
        "challenge is maintaining **millions of persistent connections**, routing "
        "messages to whichever server holds a recipient's connection, and choosing "
        "a message store that supports fast sync and retrieval."
    ),
    clarifying=[
        ClarifyQ("Functional scope",
                 "1:1 only, or group chat? Read receipts, media?",
                 "Group chat changes fan-out; receipts/media add data paths.",
                 "1:1 and group chat with delivery/read receipts and media."),
        ClarifyQ("Scale",
                 "How many concurrent online users and messages/day?",
                 "Connection count drives the connection-server tier; message volume drives storage.",
                 "~50M concurrent connections, tens of billions of messages/day."),
        ClarifyQ("Delivery",
                 "Must messages be ordered and delivered exactly once per device?",
                 "Ordering and dedup affect the id scheme and client sync protocol.",
                 "Per-conversation ordering; at-least-once with client-side dedup."),
        ClarifyQ("Latency",
                 "How fast must messages arrive?",
                 "Real-time chat needs push, not polling — hence persistent connections.",
                 "Sub-second delivery for online users."),
    ],
    requirements=Requirements(
        functional=["1:1 and group messaging", "Online presence", "Message history & multi-device sync",
                    "Delivery/read receipts"],
        non_functional=["Sub-second delivery", "Millions of concurrent connections",
                        "Reliable, ordered per conversation", "Durable history"],
        out_of_scope=["End-to-end encryption details (mention in security)", "Voice/video calls"],
    ),
    estimation=Estimation(
        assumptions=["50M concurrent users", "40 messages/user/day", "Message ~ 200 bytes"],
        rows=[
            EstimationRow("Concurrent connections", "50M", "50M persistent sockets"),
            EstimationRow("Conn servers (~100k conns each)", "50M / 100k", "~ 500 servers"),
            EstimationRow("Message write QPS", "2B/day / 86,400", "~ 23,000 QPS"),
            EstimationRow("Storage / day", "2B x 200 B", "~ 400 GB/day"),
        ],
        notes=["The connection tier, not compute, is the scaling story — plan connection servers explicitly."],
    ),
    apis=[
        APIEndpoint("WS /connect", "Client opens a persistent WebSocket to a connection server."),
        APIEndpoint("send(conversation_id, content)", "Send a message over the socket."),
        APIEndpoint("GET /v1/conversations/{id}/messages?after=seq", "Fetch history / sync missed messages."),
    ],
    data_model=[
        DataEntity("Message",
                   ["message_id (time-sortable)", "conversation_id", "sender_id", "content_ref", "created_at"],
                   store="Wide-column/KV keyed by (conversation_id, message_id) for range reads."),
        DataEntity("Conversation membership", ["conversation_id", "user_id", "last_read_seq"],
                   store="KV for fast membership and receipt lookups."),
        DataEntity("Presence", ["user_id", "status", "last_active", "connection_server"],
                   store="In-memory store updated by heartbeats."),
    ],
    high_level=(
        "Each client holds a persistent **WebSocket** to a **connection server**. A "
        "**service discovery** layer records which server holds each user's "
        "connection. To deliver a message, the **chat service** persists it (getting "
        "a time-sortable id), looks up the recipient's connection server, and pushes "
        "it; if the recipient is offline, it's stored for retrieval on reconnect. A "
        "**presence service** tracks online status via heartbeats. Clients sync "
        "missed messages by requesting everything after their last-seen sequence."
    ),
    request_flows=[
        "Client connects -> connection server -> registered in service discovery.",
        "Send -> chat service persists message (time-sortable id).",
        "Chat service finds recipient's conn server -> pushes; offline -> store for later.",
        "Recipient reconnects -> pulls messages after last-seen seq.",
        "Presence heartbeats update online status.",
    ],
    deep_dives=[
        DeepDive("Connection management",
                 "Persistent connections make this different from request/response systems. "
                 "Each connection server holds ~100k sockets; a directory maps user -> "
                 "connection server so messages route correctly. When a server dies, its "
                 "clients reconnect elsewhere and re-register. WebSockets (or long-poll "
                 "fallback) enable server push for sub-second delivery.",
                 ["More sockets per server: cheaper, but a failure drops more users at once."]),
        DeepDive("Message ordering & sync",
                 "Per-conversation ordering comes from **time-sortable message ids** "
                 "(sequence or Snowflake) so clients can request 'everything after seq N' "
                 "to sync across devices and reconnections. Delivery is at-least-once; "
                 "clients dedup by id. This makes multi-device consistency tractable.",
                 ["Global ordering is unnecessary and expensive; per-conversation is enough."]),
        DeepDive("Group chat fan-out",
                 "For small groups, the server pushes to each member's connection. For "
                 "very large groups, that fan-out is heavier — you can cap group size, "
                 "batch deliveries, or treat huge groups more like a broadcast channel. "
                 "The message is stored once per conversation and read by all members.",
                 ["Push-to-all is simple for small groups; huge groups need batching/limits."]),
        DeepDive("Reliability, cost & security",
                 "Offline messages are queued durably and delivered on reconnect, so no "
                 "message is lost if a device is away. Storage is the main cost driver at "
                 "billions of messages/day — tier old messages to cheaper storage. For "
                 "privacy, support end-to-end encryption (server relays ciphertext) and "
                 "encrypt data at rest.",
                 ["E2E encryption maximizes privacy but blocks server-side search/features.",
                  "Tiering old messages cuts cost but slows access to old history."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Transport choice",
            ["Option", "Latency", "Overhead", "Notes"],
            [["WebSocket", "Low (push)", "Persistent conn", "Best for real-time"],
             ["Long polling", "Higher", "Reconnect churn", "Fallback where WS blocked"],
             ["Short polling", "High", "Wasteful", "Avoid for chat"]],
        ),
    ],
    bottlenecks=[
        "Connection-server capacity — shard users across many servers, plan for reconnect storms.",
        "Presence heartbeat volume — batch and coarsen update frequency.",
        "Message storage growth — tier and compress old history.",
        "Large-group fan-out — batch deliveries or cap group size.",
    ],
    security=[
        "Optional end-to-end encryption; server relays ciphertext only.",
        "Encrypt data at rest; authenticate every connection and message.",
        "Abuse/spam controls and per-user rate limits.",
    ],
    wrap_up=(
        "A chat system is a persistent-connection routing problem: keep millions of "
        "sockets, map users to connection servers, persist time-sortable messages "
        "for ordering and sync, and track presence via heartbeats. Scale the "
        "connection tier, tier old messages for cost, and add E2E encryption for privacy."
    ),
))


# ===========================================================================
# Chapter 13 — Design a Search Autocomplete System
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v1_ch13", number=13, volume=1,
    title="Design a Search Autocomplete System",
    tagline="Return the top suggestions for a prefix in a few milliseconds.",
    diagram_id="v1_ch13",
    overview=(
        "Autocomplete suggests the most popular completions as a user types. It is "
        "read-dominated and latency-critical — suggestions must appear within a few "
        "milliseconds of each keystroke. The core idea is to **precompute** the "
        "top-K completions per prefix offline and serve them from an in-memory "
        "structure (a **trie** with cached top-K), while aggregating query "
        "popularity in the background."
    ),
    clarifying=[
        ClarifyQ("Functional scope",
                 "Top-K by popularity? Personalized? Typo tolerance?",
                 "Personalization and fuzzy matching greatly increase complexity.",
                 "Global top-K by popularity, ~5 suggestions, exact-prefix to start."),
        ClarifyQ("Scale",
                 "How many queries/day and suggestion requests/keystroke?",
                 "Every keystroke can be a request, so read volume is huge.",
                 "~10B searches/day; each keystroke may trigger a lookup."),
        ClarifyQ("Latency",
                 "What's the latency budget per suggestion request?",
                 "Sub-10ms is needed to feel instant while typing.",
                 "Under ~10 ms at p99."),
        ClarifyQ("Freshness",
                 "How fresh must suggestions be — real-time trends or daily?",
                 "Real-time trending needs a streaming update path; daily allows batch rebuilds.",
                 "Daily/near-real-time rebuilds are acceptable for most terms."),
    ],
    requirements=Requirements(
        functional=["Return top-K completions for a prefix", "Reflect query popularity"],
        non_functional=["p99 < ~10 ms", "Very high read QPS", "Efficient memory use"],
        out_of_scope=["Full search ranking", "Deep personalization (mention as extension)"],
    ),
    estimation=Estimation(
        assumptions=["10B searches/day", "~4 keystroke lookups per search", "Top-5 suggestions"],
        rows=[
            EstimationRow("Search QPS", "10B / 86,400", "~ 116,000 QPS"),
            EstimationRow("Suggestion QPS", "116k x ~4 keystrokes", "~ 460,000 QPS"),
            EstimationRow("Latency budget", "per keystroke", "< 10 ms"),
        ],
        notes=["~half a million QPS forces in-memory serving; the DB is only for offline aggregation."],
    ),
    apis=[
        APIEndpoint("GET /v1/suggest?prefix=abc", "Returns the top-K completions for the prefix."),
    ],
    data_model=[
        DataEntity("Trie node",
                   ["character edges", "cached top-K completions for the subtree"],
                   store="In-memory trie, sharded by prefix; served from suggestion nodes."),
        DataEntity("Query frequency",
                   ["query", "count (windowed)"],
                   store="Aggregated offline from logs (batch/stream) in an analytics store."),
    ],
    high_level=(
        "A background pipeline **aggregates query frequencies** from logs (batch or "
        "streaming). It builds a **trie** where each node caches the **top-K "
        "completions** for its subtree, so a lookup is O(length of prefix) — walk to "
        "the prefix node and return its cached list. The trie is held in memory and "
        "**sharded by prefix** to fit and to spread load. It's **rebuilt "
        "periodically** so suggestions reflect recent popularity. The write/logging "
        "path and the read/serving path are fully separated."
    ),
    request_flows=[
        "Keystroke -> GET /suggest?prefix.",
        "Query service walks the in-memory trie to the prefix node.",
        "Return the node's cached top-K completions.",
        "Offline: logs -> frequency aggregation -> rebuild trie -> hot-swap.",
    ],
    deep_dives=[
        DeepDive("Trie with cached top-K",
                 "A plain trie finds a prefix quickly but still needs to search its subtree "
                 "for the most popular completions. **Caching top-K at each node** turns "
                 "the lookup into a direct read, meeting the millisecond budget. The cost "
                 "is build time and memory — every node stores a small list — but reads "
                 "become trivial, which is the right trade for a read-dominated system.",
                 ["Caching top-K: fast reads, higher memory and build cost.",
                  "Computing top-K at query time: less memory, too slow at 460k QPS."]),
        DeepDive("Offline aggregation & freshness",
                 "Query popularity is computed offline from logs so the serving path never "
                 "does heavy work. Batch rebuilds (e.g. daily) are simplest; a streaming "
                 "layer can nudge counts for trending terms. Sampling logs at extreme scale "
                 "keeps aggregation affordable with negligible accuracy loss.",
                 ["Batch rebuilds: simple, slightly stale.",
                  "Streaming updates: fresher trends, more moving parts."]),
        DeepDive("Scalability & sharding",
                 "One trie won't fit or serve half a million QPS from a single node, so it "
                 "is sharded by prefix (e.g. by first characters) across many suggestion "
                 "servers, with a router directing each request. Replicas per shard add "
                 "read capacity and availability. Rebuilt tries are hot-swapped to avoid "
                 "downtime.",
                 ["Prefix sharding spreads load but can create hot shards for popular letters."]),
        DeepDive("Cost & security",
                 "Serving from memory is fast but RAM is the cost driver — bound it by "
                 "limiting suggestions per node and pruning rare terms. Filter the "
                 "suggestion corpus to remove offensive or unsafe completions, since "
                 "suggestions are user-facing and reputationally sensitive.",
                 ["Pruning rare terms saves memory but may drop long-tail suggestions."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Serving structure",
            ["Approach", "Read latency", "Memory", "Freshness"],
            [["Trie + cached top-K", "Very low", "High", "Rebuild cadence"],
             ["DB query per keystroke", "Too high", "Low", "Real-time"],
             ["Prefix -> precomputed list in KV", "Low", "Moderate", "Rebuild cadence"]],
        ),
    ],
    bottlenecks=[
        "Hot prefix shards (common first letters) — add replicas / finer sharding.",
        "Trie memory footprint — prune rare terms, cap K.",
        "Rebuild cost/latency — incremental updates for trending terms.",
    ],
    security=[
        "Filter offensive/unsafe suggestions before they reach users.",
        "Don't surface private or personally identifying queries in a global corpus.",
    ],
    wrap_up=(
        "Autocomplete is a precompute-and-serve problem: aggregate popularity "
        "offline, cache top-K at each trie node, serve from a sharded in-memory "
        "structure, and rebuild periodically. Reads are trivial by construction; "
        "the engineering is in aggregation, sharding and memory control."
    ),
))

# ===========================================================================
# Chapter 14 — Design YouTube
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v1_ch14", number=14, volume=1,
    title="Design YouTube",
    tagline="Upload, transcode, store and stream video smoothly to a global audience.",
    diagram_id="v1_ch14",
    overview=(
        "A video platform ingests uploads, **transcodes** them into multiple "
        "resolutions and codecs, stores originals and renditions durably, and "
        "streams them worldwide with **adaptive bitrate**. The system splits "
        "cleanly into three concerns — **upload**, **processing (transcoding)**, "
        "and **delivery** — each scaled independently, with the CDN doing the heavy "
        "lifting on the read side."
    ),
    clarifying=[
        ClarifyQ("Functional scope",
                 "Upload + playback only, or also comments, recommendations, live?",
                 "Live streaming and recommendations are large separate systems.",
                 "Focus on upload, transcoding, storage and adaptive playback."),
        ClarifyQ("Scale",
                 "How many uploads/day and views/day?",
                 "Views dwarf uploads; delivery is the dominant load, handled by CDN.",
                 "Hundreds of hours uploaded/min; billions of views/day."),
        ClarifyQ("Quality/latency",
                 "How fast must a video be watchable after upload? Which resolutions?",
                 "Transcoding time affects publish latency; resolutions affect storage.",
                 "Watchable within minutes; multiple resolutions from 240p to 4K."),
        ClarifyQ("Devices/networks",
                 "Must playback adapt to varying bandwidth and devices?",
                 "Adaptive bitrate (HLS/DASH) is required for smooth global playback.",
                 "Yes — adaptive streaming across mobile and desktop."),
    ],
    requirements=Requirements(
        functional=["Upload large videos", "Transcode to multiple renditions", "Adaptive streaming playback"],
        non_functional=["Smooth global playback (CDN)", "Durable storage",
                        "Scalable transcoding pipeline", "Reasonable publish latency"],
        out_of_scope=["Recommendations", "Live streaming", "Monetization"],
    ),
    estimation=Estimation(
        assumptions=["500 hours uploaded/min", "Avg video 300 MB original", "5 renditions ~1.5x original", "Views 5B/day"],
        rows=[
            EstimationRow("Uploads/day", "500 x 60 x 24 hours", "~ 720k hours/day"),
            EstimationRow("Original storage/day", "~ millions of videos x 300 MB", "hundreds of TB/day"),
            EstimationRow("With renditions", "x ~2.5 total", "~ PB/month scale"),
            EstimationRow("View delivery", "5B views x tens of MB", "served ~99% via CDN"),
        ],
        notes=["Delivery bandwidth is enormous; the CDN, not origin, must absorb it."],
    ),
    apis=[
        APIEndpoint("POST /v1/videos (initiate)", "Get a pre-signed URL for direct-to-storage upload.", "Client uploads directly to blob storage."),
        APIEndpoint("POST /v1/videos/{id}/complete", "Mark upload complete; enqueue transcoding."),
        APIEndpoint("GET /v1/videos/{id}/manifest", "Return the HLS/DASH manifest for adaptive playback."),
    ],
    data_model=[
        DataEntity("Video metadata", ["video_id", "owner", "title", "status", "rendition_refs", "created_at"],
                   store="Metadata DB (sharded)."),
        DataEntity("Media files", ["original", "renditions (240p..4K)", "manifest"],
                   store="Blob/object storage; renditions distributed to CDN."),
    ],
    high_level=(
        "**Upload:** the client gets a **pre-signed URL** and uploads the original "
        "directly to **blob storage** (bypassing app servers). On completion, a "
        "**transcoding pipeline** — modeled as a DAG of tasks — produces multiple "
        "**renditions** (resolutions/codecs) and a streaming **manifest**. "
        "Renditions are pushed to the **CDN**.\n\n"
        "**Playback:** the client fetches the manifest and streams **adaptive "
        "bitrate** chunks (HLS/DASH) from the nearest CDN edge, switching quality to "
        "match bandwidth. The origin is rarely touched; the CDN serves the vast "
        "majority of bytes."
    ),
    request_flows=[
        "Client -> initiate upload -> pre-signed URL -> upload original to storage.",
        "Complete -> enqueue transcoding pipeline.",
        "Pipeline produces renditions + manifest -> push to CDN.",
        "Viewer -> fetch manifest -> stream adaptive chunks from CDN edge.",
    ],
    deep_dives=[
        DeepDive("Transcoding pipeline",
                 "Transcoding is CPU-heavy and parallelizable. Model it as a **DAG**: "
                 "split the video into segments, transcode segments in parallel across a "
                 "worker fleet, then assemble renditions and the manifest. Parallelism "
                 "cuts publish latency; using spot/preemptible compute cuts cost. Failures "
                 "retry at the segment level.",
                 ["More parallelism: faster publish, higher peak compute cost.",
                  "Spot instances: cheaper, but tasks must tolerate preemption."]),
        DeepDive("Adaptive streaming & delivery",
                 "Videos are stored as short **chunks** at several bitrates with a manifest "
                 "(HLS/DASH). The player picks the bitrate that fits current bandwidth, "
                 "avoiding rebuffering. The **CDN** caches popular chunks at the edge, so "
                 "delivery scales without hammering origin — essential given billions of "
                 "views.",
                 ["More renditions: smoother adaptation, more storage/transcode cost."]),
        DeepDive("Storage cost & tiering",
                 "Storing originals plus renditions is petabyte-scale. Most views hit a "
                 "small set of popular videos, so keep hot content on fast storage/CDN and "
                 "**tier cold videos** to cheaper archival storage. Delete or re-derive "
                 "rarely-watched renditions to save space.",
                 ["Keeping all renditions hot: best UX, high cost.",
                  "Tiering cold content: big savings, slower first play for old videos."]),
        DeepDive("Reliability & security",
                 "Direct-to-storage upload with pre-signed URLs keeps app servers out of "
                 "the byte path and is resumable for large files. Content is served over "
                 "HTTPS; signed URLs and token auth protect premium/private videos. "
                 "Copyright/abuse scanning runs in the pipeline.",
                 ["Signed URLs protect content but add key-management overhead."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Delivery & storage choices",
            ["Decision", "Option A", "Option B"],
            [["Upload path", "Direct-to-storage (pre-signed)", "Through app servers (simpler, bottleneck)"],
             ["Compute", "Spot/preemptible (cheap)", "On-demand (reliable)"],
             ["Cold content", "Tier to archival (cheap)", "Keep hot (fast)"]],
        ),
    ],
    bottlenecks=[
        "Transcoding compute during upload spikes — autoscale, queue, use spot.",
        "Origin bandwidth — maximize CDN cache hit ratio.",
        "Storage growth — tier cold content and prune unused renditions.",
    ],
    security=[
        "HTTPS + signed URLs/token auth for private or premium content.",
        "Copyright and abuse scanning in the transcoding pipeline.",
        "Resumable, validated uploads to prevent corrupt/malicious files.",
    ],
    wrap_up=(
        "A video platform separates upload, transcoding and delivery. Upload "
        "directly to storage, transcode in a parallel DAG into adaptive renditions, "
        "and serve almost everything from the CDN. Control cost with spot compute "
        "and storage tiering; protect content with signed URLs."
    ),
))


# ===========================================================================
# Chapter 15 — Design Google Drive
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v1_ch15", number=15, volume=1,
    title="Design Google Drive",
    tagline="Store, sync and share files across devices efficiently.",
    diagram_id="v1_ch15",
    overview=(
        "A cloud drive stores users' files, keeps them **in sync** across devices, "
        "supports **sharing** and **revision history**, and does it without "
        "re-uploading whole files on every change. The key techniques are "
        "**block-level (delta) sync** and a clean separation between **file "
        "metadata** and the **block/blob storage** that holds the bytes."
    ),
    clarifying=[
        ClarifyQ("Functional scope",
                 "Sync + share + versions? Real-time collaborative editing?",
                 "Collaborative editing (like Docs) is a separate, harder problem.",
                 "File storage, multi-device sync, sharing and version history; not live co-editing."),
        ClarifyQ("Scale",
                 "How many users and how much data each?",
                 "Total storage and sync traffic size the storage and notification tiers.",
                 "Hundreds of millions of users, GBs each, frequent small edits."),
        ClarifyQ("Efficiency",
                 "Must edits avoid re-uploading the whole file?",
                 "Delta sync is essential for bandwidth and speed on large files.",
                 "Yes — sync only changed blocks."),
        ClarifyQ("Consistency",
                 "How are concurrent edits from two devices resolved?",
                 "Offline edits create conflicts that need a resolution policy.",
                 "Last-writer-wins with conflict copies when needed."),
    ],
    requirements=Requirements(
        functional=["Upload/download files", "Sync across devices", "Share files", "Revision history"],
        non_functional=["Bandwidth-efficient (delta sync)", "Durable and available",
                        "Scale to hundreds of millions of users", "Fast change propagation"],
        out_of_scope=["Real-time collaborative editing", "Rich document rendering"],
    ),
    estimation=Estimation(
        assumptions=["200M users", "Avg 10 GB stored each", "Frequent small edits"],
        rows=[
            EstimationRow("Total stored", "200M x 10 GB", "~ 2 EB (exabytes)"),
            EstimationRow("With dedup + tiering", "minus duplicate blocks", "significantly less"),
            EstimationRow("Sync events", "many small block updates/sec", "high metadata QPS"),
        ],
        notes=["Delta sync + block dedup dramatically cut both bandwidth and storage."],
    ),
    apis=[
        APIEndpoint("POST /v1/files (upload blocks)", "Upload only changed blocks (by hash)."),
        APIEndpoint("GET /v1/files/{id}", "Fetch file metadata + block references."),
        APIEndpoint("GET /v1/changes?cursor=...", "Long-poll/stream changes for sync."),
        APIEndpoint("POST /v1/files/{id}/share", "Grant access to another user."),
    ],
    data_model=[
        DataEntity("File metadata",
                   ["file_id", "owner", "name", "version", "block_hashes[]", "permissions"],
                   store="Metadata DB (strongly consistent, sharded by user)."),
        DataEntity("Block",
                   ["block_hash (content-addressed)", "bytes"],
                   store="Object storage; deduplicated by content hash."),
        DataEntity("Revision",
                   ["file_id", "version", "block_hashes[]", "created_at"],
                   store="Metadata DB — versions reference blocks, so history is cheap."),
    ],
    high_level=(
        "Files are split into **blocks**; each block is hashed and stored in "
        "**content-addressed object storage**, so identical blocks (across versions "
        "or users) are stored once (**dedup**). The **metadata service** tracks "
        "files, versions, block lists and permissions, and is the source of truth "
        "for sync. On an edit, the client uploads only **changed blocks** and "
        "updates metadata. A **notification service** tells other devices that "
        "changes exist so they pull the new metadata and any missing blocks."
    ),
    request_flows=[
        "Edit -> client diffs file into blocks -> uploads only changed blocks.",
        "Metadata updated with new version and block list.",
        "Notification service signals other devices.",
        "Other devices pull new metadata + missing blocks to converge.",
    ],
    deep_dives=[
        DeepDive("Block-level delta sync",
                 "Splitting files into blocks and syncing only the changed ones is the "
                 "core efficiency win: a one-line edit in a large document transfers a few "
                 "KB, not the whole file. Content-addressing (hash as key) also gives "
                 "**deduplication** for free — repeated blocks and identical files across "
                 "users cost storage only once.",
                 ["Smaller blocks: finer dedup/diff, more metadata overhead.",
                  "Larger blocks: less metadata, coarser diffs."]),
        DeepDive("Metadata vs data separation",
                 "Metadata (small, needs strong consistency and rich queries) lives in a "
                 "database; block bytes (large, immutable) live in object storage. This "
                 "lets each scale on its own terms and keeps the consistency-critical part "
                 "small. Versions are just different block lists in metadata, making "
                 "history cheap.",
                 ["Immutable blocks simplify caching and dedup but require GC for orphaned blocks."]),
        DeepDive("Conflicts & consistency",
                 "Two devices editing offline produce divergent versions. A pragmatic "
                 "policy is **last-writer-wins** with a **conflict copy** preserved so no "
                 "data is silently lost. Metadata operations are strongly consistent so "
                 "all devices agree on the current version pointer.",
                 ["LWW is simple but needs conflict copies to avoid data loss."]),
        DeepDive("Reliability, cost & security",
                 "Object storage provides high durability via replication/erasure coding. "
                 "Dedup and tiering (move cold files to cheaper storage) control cost at "
                 "exabyte scale. Files are encrypted at rest and in transit; sharing is "
                 "governed by per-file ACLs, and orphaned blocks are garbage-collected.",
                 ["Aggressive tiering cuts cost but slows access to old files.",
                  "Dedup across users needs care to avoid cross-tenant data leaks."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "Sync & storage choices",
            ["Decision", "Option A", "Option B"],
            [["Sync granularity", "Block/delta (efficient)", "Whole file (simple)"],
             ["Conflict policy", "LWW + conflict copy", "Manual merge (complex)"],
             ["Cold data", "Tier to archival", "Keep hot"]],
        ),
    ],
    bottlenecks=[
        "Metadata QPS from frequent small edits — shard by user, cache.",
        "Notification fan-out to many devices — efficient long-poll/streaming.",
        "Storage cost at scale — dedup + tiering + block GC.",
    ],
    security=[
        "Encrypt files at rest and in transit.",
        "Per-file ACLs and signed URLs for sharing.",
        "Careful cross-user dedup to prevent data leakage; audit access.",
    ],
    wrap_up=(
        "A cloud drive is a metadata database over deduplicated, content-addressed "
        "block storage, with delta sync for efficiency and a notification service "
        "for convergence. Versions are cheap (block lists), conflicts use LWW with "
        "safety copies, and cost is controlled with dedup and tiering."
    ),
))


# ===========================================================================
# Chapter 16 — The Learning Continues
# ===========================================================================
CHAPTERS.append(Chapter(
    id="v1_ch16", number=16, volume=1,
    title="The Learning Continues",
    tagline="The building blocks and habits that recur across every design.",
    diagram_id="v1_ch16",
    overview=(
        "The final chapter steps back from individual systems to the patterns that "
        "recur everywhere. Strong system design is not memorizing 20 architectures; "
        "it's fluently recombining a small set of building blocks and reasoning "
        "about their trade-offs for the problem in front of you."
    ),
    clarifying=[
        ClarifyQ("Direction",
                 "Which area do you want to deepen — data, reliability, or scale?",
                 "Focusing your study beats trying to learn everything shallowly.",
                 "Rotate through data modeling, consistency, and failure handling with real systems."),
        ClarifyQ("Practice method",
                 "How will you practice — reading or re-deriving designs?",
                 "Re-deriving from first principles builds far more durable skill than reading.",
                 "Re-derive each design from requirements, then compare to references."),
    ],
    requirements=Requirements(
        functional=["Consolidate recurring patterns", "Point to further study"],
        non_functional=["Transferable understanding over memorization"],
        out_of_scope=["Any single system"],
    ),
    estimation=Estimation(
        assumptions=["Interview prep over several weeks"],
        rows=[
            EstimationRow("Core patterns to master", "count", "~ 8-10"),
            EstimationRow("Designs to re-derive", "practice set", "~ 15-20"),
        ],
        notes=["Depth on the fundamentals transfers to unseen problems."],
    ),
    apis=[],
    data_model=[],
    high_level=(
        "**The recurring building blocks:**\n\n"
        "- **Horizontal scaling + stateless tiers** behind load balancers.\n"
        "- **Replication** for read scale and availability; **sharding** for write scale.\n"
        "- **Caching** (cache-aside, CDN) as the cheapest latency win.\n"
        "- **Asynchronous processing** via queues to decouple and absorb spikes.\n"
        "- **Consistent hashing** for partitioning and minimal rebalancing.\n"
        "- **Quorums / CAP reasoning** for tunable consistency.\n"
        "- **Idempotency + retries** for reliable delivery.\n"
        "- **Metadata/data separation** and content-addressing for storage systems.\n\n"
        "**The habits:** clarify first, estimate to find the bottleneck, design the "
        "happy path, then attack failure modes, cost and security explicitly."
    ),
    request_flows=[
        "Clarify -> estimate -> high-level -> deep dive -> trade-offs.",
        "Identify the binding constraint before choosing components.",
    ],
    deep_dives=[
        DeepDive("Reason about trade-offs, don't memorize",
                 "Every choice — replicate or shard, cache or not, strong or eventual "
                 "consistency, sync or async — is a trade-off. The interview measures "
                 "whether you can name the trade-off and justify a choice for the given "
                 "requirements, not whether you recall a canonical diagram.",
                 ["The 'right' answer depends on requirements you clarified earlier."]),
        DeepDive("Where to go next",
                 "Study engineering blogs from large companies, read about real incidents "
                 "(they teach failure modes), and re-derive each classic design from its "
                 "requirements. Volume 2 applies these blocks to harder, more specialized "
                 "systems where trade-offs dominate.",
                 ["Reading references is useful; re-deriving is what builds intuition."]),
    ],
    tradeoff_tables=[
        TradeoffTable(
            "The core levers",
            ["Lever", "Buys you", "At the cost of"],
            [["Replication", "Read scale, availability", "Staleness"],
             ["Sharding", "Write scale", "Cross-shard complexity"],
             ["Caching", "Latency, cost", "Invalidation"],
             ["Async/queues", "Spike absorption", "Delay, complexity"]],
        ),
    ],
    bottlenecks=[
        "The database is usually the first ceiling — know replicate vs shard cold.",
        "Single-region latency — know when to go multi-region.",
    ],
    security=[
        "Make security and privacy a default section in every design, not an afterthought.",
    ],
    wrap_up=(
        "System design mastery is a small toolkit used with good judgment: scale "
        "horizontally, cache aggressively, decouple with queues, reason about CAP, "
        "and always tie decisions back to the requirements you clarified. Keep "
        "re-deriving designs and studying real systems."
    ),
))
