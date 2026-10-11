"""
Professional (Microsoft Learn / Azure-architecture style) diagrams, one per
chapter, built with diagram_engine.Diagram. get_diagram() falls back to a
generic three-tier sketch for any id without a bespoke diagram.
"""

from __future__ import annotations

from diagram_engine import Diagram


def _generic(title: str) -> Diagram:
    d = Diagram(title=title, width=900, height=260)
    d.node("client", "Clients", 40, 110, 140, 62, "client")
    d.node("lb", "Load Balancer", 240, 110, 150, 62, "edge")
    d.node("svc", "Service", 450, 110, 150, 62, "service")
    d.node("db", "Database", 660, 100, 150, 74, "data", shape="cylinder")
    d.edge("client", "lb", "HTTPS")
    d.edge("lb", "svc")
    d.edge("svc", "db", "read/write")
    return d


# ============================ VOLUME 1 =====================================

def v1_ch1():
    d = Diagram(title="From single server to distributed system", width=900, height=520)
    d.node("user", "Users", 40, 60, 130, 58, "client")
    d.node("dns", "DNS", 40, 220, 130, 58, "external")
    d.node("cdn", "CDN", 40, 360, 130, 58, "edge", sub="static assets")
    d.node("lb", "Load Balancer", 230, 130, 150, 60, "edge")
    d.node("w1", "Web Server 1", 430, 60, 150, 56, "service", shape="rect")
    d.node("w2", "Web Server 2", 430, 140, 150, 56, "service", shape="rect")
    d.node("cache", "Cache", 430, 250, 150, 56, "cache", sub="Redis")
    d.node("primary", "DB Primary", 650, 120, 150, 72, "data", shape="cylinder")
    d.node("replica", "DB Replica", 650, 280, 150, 72, "data", shape="cylinder")
    d.edge("user", "dns", "1 resolve")
    d.edge("user", "lb", "2 request")
    d.edge("user", "cdn", "static", dashed=True)
    d.edge("lb", "w1"); d.edge("lb", "w2")
    d.edge("w1", "cache", "read"); d.edge("w2", "cache")
    d.edge("w1", "primary", "write")
    d.edge("primary", "replica", "replicate", dashed=True)
    d.edge("w2", "replica", "read")
    return d


def v1_ch2():
    d = Diagram(title="Estimation building blocks", width=900, height=320)
    for i, (lbl, sub) in enumerate([
        ("QPS", "daily / 86,400"), ("Peak QPS", "2–3× average"),
        ("Storage", "size × count × years"), ("Bandwidth", "QPS × payload"),
        ("Cache memory", "hot set ~20%"), ("Availability", "the nines")]):
        x = 40 + (i % 3) * 290
        y = 70 + (i // 3) * 120
        kind = ["service", "service", "data", "edge", "cache", "accent"][i]
        d.node(f"n{i}", lbl, x, y, 250, 80, kind, sub=sub)
    return d


def v1_ch3():
    d = Diagram(title="The 4-step framework", width=900, height=220)
    steps = [("1 · Clarify", "client"), ("2 · High-level", "service"),
             ("3 · Deep dive", "compute"), ("4 · Wrap up", "accent")]
    for i, (lbl, k) in enumerate(steps):
        d.node(f"s{i}", lbl, 40 + i * 215, 90, 180, 64, k)
        if i:
            d.edge(f"s{i-1}", f"s{i}")
    return d


def v1_ch4():
    d = Diagram(title="Rate limiter placement", width=900, height=360)
    d.node("client", "Clients", 40, 150, 130, 60, "client")
    d.node("gw", "API Gateway", 230, 150, 150, 60, "edge", sub="rate limiter")
    d.node("redis", "Redis", 230, 270, 150, 60, "cache", sub="counters + Lua")
    d.node("svc", "API Servers", 470, 70, 150, 60, "service")
    d.node("drop", "429 Too Many\nRequests", 470, 240, 160, 64, "external")
    d.edge("client", "gw", "request")
    d.edge("gw", "redis", "atomic check")
    d.edge("gw", "svc", "allow")
    d.edge("gw", "drop", "reject")
    return d


def v1_ch5():
    d = Diagram(title="Consistent hashing ring", width=820, height=440)
    d.node("ring", "Hash ring\n0 … 2^160", 310, 170, 180, 90, "accent", shape="circle")
    d.node("s0", "Node A", 330, 40, 130, 52, "compute")
    d.node("s1", "Node B", 600, 190, 130, 52, "compute")
    d.node("s2", "Node C", 330, 350, 130, 52, "compute")
    d.node("s3", "Node D", 70, 190, 130, 52, "compute")
    for s in ("s0", "s1", "s2", "s3"):
        d.edge(s, "ring", dashed=True)
    return d


def v1_ch6():
    d = Diagram(title="Distributed key-value store (Dynamo-style)", width=900, height=400)
    d.node("client", "Client", 40, 160, 120, 60, "client")
    d.node("coord", "Coordinator", 210, 150, 150, 70, "service", sub="any node")
    d.node("n1", "Node A", 440, 60, 130, 56, "data", shape="cylinder")
    d.node("n2", "Node B", 440, 160, 130, 56, "data", shape="cylinder")
    d.node("n3", "Node C", 440, 260, 130, 56, "data", shape="cylinder")
    d.node("quorum", "Quorum\nW + R > N", 650, 150, 160, 70, "accent")
    d.edge("client", "coord", "get/put")
    d.edge("coord", "n1", "replicate N")
    d.edge("coord", "n2"); d.edge("coord", "n3")
    d.edge("coord", "quorum", dashed=True)
    return d


def v1_ch7():
    d = Diagram(title="Snowflake 64-bit ID layout", width=900, height=230)
    segs = [("1 bit", "sign", "external"), ("41 bits", "timestamp", "service"),
            ("5 bits", "datacenter", "compute"), ("5 bits", "machine", "edge"),
            ("12 bits", "sequence", "accent")]
    widths = [90, 250, 150, 150, 190]
    x = 30
    for i, ((top, sub, k), w) in enumerate(zip(segs, widths)):
        d.node(f"s{i}", top, x, 90, w, 70, k, sub=sub)
        x += w + 8
    return d


def v1_ch8():
    d = Diagram(title="URL shortener", width=900, height=360)
    d.node("client", "Clients", 40, 150, 130, 60, "client")
    d.node("gw", "API Gateway", 220, 150, 140, 60, "edge")
    d.node("write", "Write Service", 420, 60, 150, 56, "service", sub="create short")
    d.node("read", "Read Service", 420, 160, 150, 56, "service", sub="redirect")
    d.node("idgen", "ID Generator", 420, 260, 150, 56, "compute", sub="base62")
    d.node("cache", "Cache", 640, 90, 140, 56, "cache")
    d.node("db", "URL Store", 640, 220, 150, 70, "data", shape="cylinder")
    d.edge("client", "gw")
    d.edge("gw", "write"); d.edge("gw", "read")
    d.edge("write", "idgen"); d.edge("write", "db")
    d.edge("read", "cache", "hot"); d.edge("read", "db", "miss")
    return d


def v1_ch9():
    d = Diagram(title="Web crawler", width=920, height=380)
    d.node("seed", "Seed URLs", 40, 160, 120, 56, "client")
    d.node("frontier", "URL Frontier", 210, 150, 150, 68, "queue", sub="priority+polite")
    d.node("fetch", "HTML Downloader", 420, 60, 160, 56, "service")
    d.node("parse", "Parser", 420, 160, 160, 56, "service")
    d.node("dedupe", "Dedupe", 420, 260, 160, 56, "compute", sub="bloom filter")
    d.node("store", "Content Store", 660, 150, 150, 70, "data", shape="cylinder")
    d.edge("seed", "frontier")
    d.edge("frontier", "fetch", "next")
    d.edge("fetch", "parse"); d.edge("parse", "dedupe")
    d.edge("parse", "frontier", "new links", dashed=True)
    d.edge("dedupe", "store")
    return d


def v1_ch10():
    d = Diagram(title="Notification system", width=920, height=380)
    d.node("svc", "Services", 40, 160, 120, 56, "client")
    d.node("api", "Notification API", 200, 150, 160, 68, "service")
    d.node("q", "Message Queue", 400, 150, 150, 68, "queue")
    d.node("workers", "Workers", 590, 150, 130, 68, "compute")
    for i, (lbl, y) in enumerate([("APNs / FCM", 60), ("SMS", 150), ("Email", 240)]):
        d.node(f"ch{i}", lbl, 760, y, 130, 52, "external")
        d.edge("workers", f"ch{i}")
    d.edge("svc", "api"); d.edge("api", "q"); d.edge("q", "workers")
    return d


def v1_ch11():
    d = Diagram(title="News feed (hybrid fan-out)", width=920, height=400)
    d.node("user", "User", 40, 170, 110, 56, "client")
    d.node("web", "Web Servers", 190, 160, 140, 68, "service")
    d.node("post", "Post Service", 380, 60, 140, 56, "service")
    d.node("fanout", "Fanout Service", 380, 170, 150, 56, "compute")
    d.node("feedcache", "Feed Cache", 380, 280, 150, 56, "cache", sub="per user")
    d.node("postdb", "Post DB", 620, 90, 140, 70, "data", shape="cylinder")
    d.edge("user", "web", "read/post")
    d.edge("web", "post", "publish")
    d.edge("post", "fanout"); d.edge("post", "postdb")
    d.edge("fanout", "feedcache", "push")
    d.edge("web", "feedcache", "read feed")
    return d


def v1_ch12():
    d = Diagram(title="Chat system", width=920, height=400)
    d.node("a", "User A", 40, 70, 110, 52, "client")
    d.node("b", "User B", 40, 250, 110, 52, "client")
    d.node("ws", "WebSocket Servers", 210, 160, 170, 68, "service", sub="stateful conn")
    d.node("chat", "Chat Service", 430, 70, 150, 56, "service")
    d.node("presence", "Presence Service", 430, 250, 160, 56, "compute")
    d.node("kv", "Message Store", 650, 150, 160, 70, "data", shape="cylinder")
    d.edge("a", "ws", "send", bidir=True)
    d.edge("ws", "b", "push", bidir=True)
    d.edge("ws", "chat"); d.edge("ws", "presence")
    d.edge("chat", "kv")
    return d


def v1_ch13():
    d = Diagram(title="Search autocomplete", width=900, height=380)
    d.node("client", "Client", 40, 150, 120, 60, "client")
    d.node("gw", "Query Service", 220, 150, 150, 60, "service")
    d.node("trie", "Trie Cache", 430, 60, 160, 60, "cache", sub="prefix→top-K")
    d.node("agg", "Aggregator", 430, 220, 160, 60, "compute", sub="offline")
    d.node("logs", "Analytics Logs", 660, 220, 160, 70, "data", shape="cylinder")
    d.edge("client", "gw", "prefix")
    d.edge("gw", "trie", "top-K")
    d.edge("logs", "agg")
    d.edge("agg", "trie", "rebuild", dashed=True)
    return d


def v1_ch14():
    d = Diagram(title="Video platform (YouTube)", width=940, height=420)
    d.node("user", "Users", 40, 170, 120, 58, "client")
    d.node("lb", "Load Balancer", 190, 170, 150, 58, "edge")
    d.node("api", "API Servers", 370, 70, 140, 56, "service")
    d.node("upload", "Upload Service", 370, 180, 150, 56, "service")
    d.node("transcode", "Transcoding", 560, 70, 150, 56, "compute", sub="DAG pipeline")
    d.node("blob", "Blob Storage", 560, 180, 150, 70, "data", shape="cylinder")
    d.node("cdn", "CDN", 760, 170, 130, 58, "edge")
    d.edge("user", "lb")
    d.edge("lb", "api", "watch"); d.edge("lb", "upload", "upload")
    d.edge("upload", "blob"); d.edge("blob", "transcode")
    d.edge("transcode", "cdn"); d.edge("user", "cdn", "stream", dashed=True)
    return d


def v1_ch15():
    d = Diagram(title="Cloud drive (Google Drive)", width=940, height=420)
    d.node("client", "Client\n(sync)", 40, 170, 130, 66, "client")
    d.node("lb", "Load Balancer", 200, 175, 140, 58, "edge")
    d.node("api", "API Servers", 370, 70, 140, 56, "service")
    d.node("meta", "Metadata DB", 370, 190, 140, 70, "data", shape="cylinder")
    d.node("block", "Block Servers", 560, 70, 150, 56, "compute", sub="dedupe/diff")
    d.node("store", "Cloud Storage", 560, 190, 150, 70, "data", shape="cylinder")
    d.node("notif", "Notification Svc", 760, 120, 150, 60, "accent")
    d.edge("client", "lb"); d.edge("lb", "api")
    d.edge("api", "meta"); d.edge("api", "block", "chunks")
    d.edge("block", "store")
    d.edge("notif", "client", "changes", dashed=True)
    return d


def v1_ch16():
    d = Diagram(title="Recurring building blocks", width=900, height=320)
    items = [("Scalability", "service"), ("Availability", "compute"),
             ("Consistency", "data"), ("Caching", "cache"),
             ("Sharding", "edge"), ("Async / Queues", "queue")]
    for i, (lbl, k) in enumerate(items):
        x = 40 + (i % 3) * 290
        y = 70 + (i // 3) * 120
        d.node(f"n{i}", lbl, x, y, 250, 80, k)
    return d


# ============================ VOLUME 2 =====================================

def v2_ch1():
    d = Diagram(title="Proximity service", width=920, height=380)
    d.node("user", "User", 40, 160, 110, 58, "client")
    d.node("lb", "Load Balancer", 190, 160, 150, 58, "edge")
    d.node("lbs", "Location Service", 380, 70, 170, 56, "service", sub="read path")
    d.node("geo", "Geo Index", 380, 200, 170, 60, "compute", sub="geohash/quadtree")
    d.node("cache", "Geo Cache", 600, 70, 150, 56, "cache")
    d.node("db", "Business DB", 600, 190, 160, 70, "data", shape="cylinder")
    d.edge("user", "lb", "search")
    d.edge("lb", "lbs"); d.edge("lbs", "geo")
    d.edge("geo", "cache"); d.edge("lbs", "db")
    return d


def v2_ch2():
    d = Diagram(title="Nearby friends (real-time)", width=920, height=380)
    d.node("user", "User (mobile)", 40, 160, 130, 62, "client")
    d.node("lb", "WebSocket LB", 210, 160, 140, 62, "edge")
    d.node("ws", "WebSocket Servers", 380, 70, 180, 56, "service")
    d.node("pub", "Redis Pub/Sub", 380, 200, 170, 56, "cache")
    d.node("loc", "Location Cache", 610, 70, 160, 56, "cache", sub="TTL")
    d.node("hist", "History DB", 610, 190, 160, 70, "data", shape="cylinder")
    d.edge("user", "lb", "location", dashed=True)
    d.edge("lb", "ws"); d.edge("ws", "pub", bidir=True)
    d.edge("ws", "loc"); d.edge("ws", "hist", "async")
    return d


def v2_ch3():
    d = Diagram(title="Maps: location, routing, tiles", width=940, height=400)
    d.node("user", "User", 40, 170, 110, 58, "client")
    d.node("lb", "Load Balancer", 190, 170, 150, 58, "edge")
    d.node("loc", "Location Svc", 370, 60, 150, 52, "service")
    d.node("route", "Routing Svc", 370, 170, 150, 52, "service")
    d.node("tile", "Tile Svc", 370, 280, 150, 52, "service")
    d.node("graph", "Road Graph", 560, 110, 160, 70, "data", shape="cylinder")
    d.node("cdn", "Tile CDN", 560, 270, 150, 58, "edge")
    d.edge("user", "lb")
    d.edge("lb", "loc"); d.edge("lb", "route"); d.edge("lb", "tile")
    d.edge("route", "graph", "A* / CH"); d.edge("tile", "cdn")
    return d


def v2_ch4():
    d = Diagram(title="Distributed message queue", width=940, height=380)
    d.node("prod", "Producers", 40, 160, 130, 58, "client")
    d.node("broker", "Broker Cluster", 220, 150, 150, 70, "service")
    d.node("p0", "Partition 0", 430, 50, 150, 50, "queue", shape="cylinder")
    d.node("p1", "Partition 1", 430, 150, 150, 50, "queue", shape="cylinder")
    d.node("p2", "Partition 2", 430, 250, 150, 50, "queue", shape="cylinder")
    d.node("cons", "Consumer Group", 650, 150, 160, 70, "compute", sub="offsets")
    d.edge("prod", "broker", "publish")
    d.edge("broker", "p0", "append"); d.edge("broker", "p1"); d.edge("broker", "p2")
    d.edge("p0", "cons", "pull"); d.edge("p1", "cons")
    return d


def v2_ch5():
    d = Diagram(title="Metrics monitoring & alerting", width=940, height=400)
    d.node("src", "Metric Sources", 40, 170, 140, 58, "client")
    d.node("collect", "Collector", 220, 170, 140, 58, "service", sub="pull/push")
    d.node("tsdb", "Time-Series DB", 420, 60, 170, 70, "data", shape="cylinder")
    d.node("query", "Query Service", 420, 210, 170, 56, "service")
    d.node("alert", "Alert Manager", 640, 60, 150, 56, "cache")
    d.node("dash", "Dashboards", 640, 210, 150, 56, "accent")
    d.edge("src", "collect"); d.edge("collect", "tsdb")
    d.edge("tsdb", "query"); d.edge("query", "alert", "rules"); d.edge("query", "dash")
    return d


def v2_ch6():
    d = Diagram(title="Ad click aggregation", width=940, height=400)
    d.node("click", "Click Events", 40, 170, 130, 58, "client")
    d.node("log", "Event Log", 200, 170, 130, 58, "queue", sub="Kafka")
    d.node("agg", "Stream Aggregator", 360, 60, 170, 56, "compute")
    d.node("recon", "Batch Reconcile", 360, 210, 170, 56, "compute")
    d.node("raw", "Raw Events", 580, 60, 150, 70, "data", shape="cylinder")
    d.node("aggdb", "Aggregated DB", 580, 200, 160, 70, "data", shape="cylinder")
    d.edge("click", "log"); d.edge("log", "agg", "stream"); d.edge("log", "raw", "archive")
    d.edge("agg", "aggdb", "per-minute")
    d.edge("recon", "aggdb", "correct", dashed=True)
    return d


def v2_ch7():
    d = Diagram(title="Hotel reservation", width=940, height=380)
    d.node("user", "User", 40, 160, 110, 58, "client")
    d.node("lb", "Load Balancer", 190, 160, 150, 58, "edge")
    d.node("hotel", "Hotel Svc", 370, 55, 150, 50, "service")
    d.node("rate", "Rate Svc", 370, 160, 150, 50, "service")
    d.node("resv", "Reservation Svc", 370, 265, 160, 50, "service")
    d.node("cache", "Inventory Cache", 590, 70, 160, 56, "cache")
    d.node("db", "Reservation DB", 590, 200, 170, 70, "data", shape="cylinder")
    d.edge("user", "lb")
    d.edge("lb", "hotel"); d.edge("lb", "rate"); d.edge("lb", "resv")
    d.edge("resv", "cache"); d.edge("resv", "db", "atomic")
    return d


def v2_ch8():
    d = Diagram(title="Distributed email service", width=940, height=400)
    d.node("client", "Mail Client", 40, 170, 130, 60, "client")
    d.node("lb", "Load Balancer", 200, 170, 140, 60, "edge")
    d.node("smtp", "SMTP (out)", 370, 60, 150, 52, "service")
    d.node("imap", "IMAP/POP (read)", 370, 165, 160, 52, "service")
    d.node("q", "Send Queue", 370, 270, 150, 52, "queue")
    d.node("store", "Mail Storage", 600, 100, 160, 70, "data", shape="cylinder")
    d.node("search", "Search Index", 600, 240, 160, 56, "compute")
    d.edge("client", "lb"); d.edge("lb", "smtp"); d.edge("lb", "imap")
    d.edge("smtp", "q"); d.edge("q", "store"); d.edge("imap", "store")
    d.edge("store", "search", "async", dashed=True)
    return d


def v2_ch9():
    d = Diagram(title="S3-like object storage", width=940, height=380)
    d.node("client", "Client", 40, 160, 120, 60, "client")
    d.node("api", "API Service", 200, 160, 140, 60, "service", sub="auth+route")
    d.node("meta", "Metadata Svc", 380, 60, 160, 56, "service")
    d.node("place", "Data Router", 380, 200, 160, 56, "compute")
    d.node("mdb", "Metadata DB", 600, 60, 150, 70, "data", shape="cylinder")
    d.node("data", "Data Nodes", 600, 200, 160, 70, "data", shape="cylinder", sub="replica/EC")
    d.edge("client", "api", "PUT/GET")
    d.edge("api", "meta"); d.edge("api", "place")
    d.edge("meta", "mdb"); d.edge("place", "data")
    return d


def v2_ch10():
    d = Diagram(title="Real-time gaming leaderboard", width=920, height=360)
    d.node("game", "Game Clients", 40, 150, 140, 60, "client")
    d.node("api", "Score Service", 220, 150, 150, 60, "service")
    d.node("zset", "Redis Sorted Set", 420, 60, 180, 60, "cache", shape="cylinder")
    d.node("db", "Game DB", 420, 210, 170, 70, "data", shape="cylinder", sub="source of truth")
    d.node("rank", "Rank / Top-N", 660, 130, 160, 60, "compute")
    d.edge("game", "api", "submit")
    d.edge("api", "zset", "ZADD"); d.edge("api", "db", "persist")
    d.edge("zset", "rank", "ZREVRANGE")
    return d


def v2_ch11():
    d = Diagram(title="Payment system", width=940, height=400)
    d.node("user", "User", 40, 170, 110, 58, "client")
    d.node("pay", "Payment Service", 190, 165, 160, 66, "service")
    d.node("ledger", "Ledger", 390, 60, 160, 56, "data", sub="double-entry")
    d.node("wallet", "Wallet Service", 390, 210, 160, 56, "service")
    d.node("psp", "PSP", 600, 60, 150, 56, "external", sub="Stripe/…")
    d.node("db", "Payment DB", 600, 200, 160, 70, "data", shape="cylinder")
    d.edge("user", "pay", "pay")
    d.edge("pay", "ledger"); d.edge("pay", "wallet")
    d.edge("pay", "psp", "charge"); d.edge("ledger", "db")
    return d


def v2_ch12():
    d = Diagram(title="Digital wallet", width=940, height=380)
    d.node("user", "User", 40, 160, 110, 58, "client")
    d.node("api", "Wallet Service", 190, 155, 150, 66, "service")
    d.node("cmd", "Command Side", 380, 60, 160, 56, "compute", sub="CQRS")
    d.node("es", "Event Store", 380, 205, 160, 56, "queue", sub="event sourcing")
    d.node("saga", "Saga Orchestrator", 600, 60, 170, 56, "compute")
    d.node("bal", "Balance Store", 600, 200, 160, 70, "data", shape="cylinder")
    d.edge("user", "api", "transfer")
    d.edge("api", "cmd"); d.edge("cmd", "es", "append")
    d.edge("cmd", "saga"); d.edge("es", "bal", "project")
    return d


def v2_ch13():
    d = Diagram(title="Stock exchange", width=960, height=400)
    d.node("trader", "Trader", 40, 165, 110, 58, "client")
    d.node("gw", "Order Gateway", 190, 160, 140, 66, "edge")
    d.node("seq", "Sequencer", 360, 55, 150, 52, "compute", sub="total order")
    d.node("match", "Matching Engine", 360, 165, 160, 60, "service", sub="in-memory")
    d.node("book", "Order Book", 580, 60, 160, 70, "cache", sub="bids/asks")
    d.node("market", "Market Data Pub", 580, 210, 170, 56, "accent")
    d.node("log", "Trade Log", 800, 130, 130, 70, "data", shape="cylinder")
    d.edge("trader", "gw", "order")
    d.edge("gw", "seq"); d.edge("seq", "match")
    d.edge("match", "book"); d.edge("match", "market", "ticks")
    d.edge("match", "log", "persist")
    return d


DIAGRAMS = {
    "v1_ch1": v1_ch1, "v1_ch2": v1_ch2, "v1_ch3": v1_ch3, "v1_ch4": v1_ch4,
    "v1_ch5": v1_ch5, "v1_ch6": v1_ch6, "v1_ch7": v1_ch7, "v1_ch8": v1_ch8,
    "v1_ch9": v1_ch9, "v1_ch10": v1_ch10, "v1_ch11": v1_ch11, "v1_ch12": v1_ch12,
    "v1_ch13": v1_ch13, "v1_ch14": v1_ch14, "v1_ch15": v1_ch15, "v1_ch16": v1_ch16,
    "v2_ch1": v2_ch1, "v2_ch2": v2_ch2, "v2_ch3": v2_ch3, "v2_ch4": v2_ch4,
    "v2_ch5": v2_ch5, "v2_ch6": v2_ch6, "v2_ch7": v2_ch7, "v2_ch8": v2_ch8,
    "v2_ch9": v2_ch9, "v2_ch10": v2_ch10, "v2_ch11": v2_ch11, "v2_ch12": v2_ch12,
    "v2_ch13": v2_ch13,
}


def get_diagram(diagram_id: str, title: str = "") -> Diagram:
    fn = DIAGRAMS.get(diagram_id)
    return fn() if fn else _generic(title or "System overview")
