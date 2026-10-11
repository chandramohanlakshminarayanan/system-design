"""
Hand-authored Mermaid sequence diagrams, one per design chapter.

Each shows how a representative request moves through the system over time —
the behavioral counterpart to the static architecture diagram. Rendered by
app.render_sequence(). Chapters without a sequence (the meta chapters in
Vol 1) simply return None from get_sequence().
"""

from __future__ import annotations

SEQUENCES: dict[str, str] = {}


def get_sequence(chapter_id: str) -> str | None:
    return SEQUENCES.get(chapter_id)


# ===========================================================================
# VOLUME 1
# ===========================================================================

SEQUENCES["v1_ch1"] = """
sequenceDiagram
    autonumber
    actor U as User
    participant DNS
    participant CDN
    participant LB as Load Balancer
    participant W as Web Server
    participant C as Cache
    participant P as DB Primary
    participant R as DB Replica
    U->>DNS: Resolve domain
    DNS-->>U: Nearest region IP
    U->>CDN: GET static assets
    CDN-->>U: Cached JS/CSS/images
    U->>LB: HTTPS request
    LB->>W: Route to a stateless server
    W->>C: Read (cache-aside)
    alt cache hit
        C-->>W: Value
    else cache miss
        W->>R: Read from replica
        R-->>W: Row
        W->>C: Populate cache
    end
    Note over W,P: Writes go to the primary only
    W->>P: Write
    P-->>R: Async replicate
    W-->>U: Response
"""

SEQUENCES["v1_ch4"] = """
sequenceDiagram
    autonumber
    actor C as Client
    participant G as API Gateway (limiter)
    participant R as Redis (counters)
    participant S as API Service
    C->>G: Request (API key)
    G->>R: Atomic INCR + check (Lua)
    alt under limit
        R-->>G: count <= limit
        G->>S: Forward request
        S-->>G: Response
        G-->>C: 200 OK + X-RateLimit-* headers
    else over limit
        R-->>G: count > limit
        G-->>C: 429 Too Many Requests + Retry-After
    end
    Note over G,R: On Redis outage: fail-open (general) or fail-closed (sensitive)
"""

SEQUENCES["v1_ch5"] = """
sequenceDiagram
    autonumber
    actor Cl as Client
    participant Ring as Hash Ring
    participant N as Owner Node
    Cl->>Ring: hash(key)
    Ring->>Ring: Walk clockwise to next virtual node
    Ring-->>Cl: Physical node for key
    Cl->>N: get / put (key)
    N-->>Cl: Value / ack
    Note over Ring,N: Add/remove a node -> only the neighbouring arc's keys move
"""

SEQUENCES["v1_ch6"] = """
sequenceDiagram
    autonumber
    actor Cl as Client
    participant Co as Coordinator
    participant A as Replica A
    participant B as Replica B
    participant C as Replica C
    Cl->>Co: put(key, value)
    par Replicate to N nodes
        Co->>A: write
        Co->>B: write
        Co->>C: write
    end
    A-->>Co: ack
    B-->>Co: ack
    Note over Co: W acks received (W + R > N) -> success
    Co-->>Cl: OK
    Cl->>Co: get(key)
    Co->>A: read
    Co->>B: read
    A-->>Co: v2 (vector clock)
    B-->>Co: v2
    Co-->>Cl: Reconciled value
"""

SEQUENCES["v1_ch7"] = """
sequenceDiagram
    autonumber
    actor App
    participant Node as ID Generator Node
    App->>Node: next_id()
    Node->>Node: read timestamp (41 bits)
    Node->>Node: add datacenter + machine bits (10)
    Node->>Node: increment sequence (12 bits)
    alt sequence overflow in same ms
        Node->>Node: wait for next millisecond
    end
    Node-->>App: 64-bit unique, time-sortable ID
    Note over Node: Clock regression detected -> pause until clock catches up
"""

SEQUENCES["v1_ch8"] = """
sequenceDiagram
    autonumber
    actor U as User
    participant G as API Gateway
    participant WS as Write Service
    participant ID as ID Generator
    participant DB as URL Store
    participant Ca as Cache
    U->>G: POST /urls (long_url)
    G->>WS: create short URL
    WS->>ID: next unique id
    ID-->>WS: id
    WS->>WS: base62(id) -> short code
    WS->>DB: store code -> long_url
    WS-->>U: short URL
    Note over U,Ca: --- later: someone visits the short link ---
    U->>G: GET /{code}
    G->>Ca: lookup code
    alt cache hit
        Ca-->>G: long_url
    else miss
        G->>DB: lookup code
        DB-->>G: long_url
        G->>Ca: populate
    end
    G-->>U: 302 redirect -> long_url
"""

SEQUENCES["v1_ch9"] = """
sequenceDiagram
    autonumber
    participant F as URL Frontier
    participant D as Downloader
    participant P as Parser
    participant Dp as Dedup (Bloom)
    participant S as Content Store
    F->>D: next polite URL
    D->>D: check robots.txt, fetch page
    D->>P: raw HTML
    P->>P: extract + normalize links
    P->>Dp: seen before?
    alt new content
        Dp-->>P: no
        P->>S: store parsed content
        P->>F: enqueue new links
    else duplicate / trap
        Dp-->>P: yes -> skip
    end
    Note over F: Per-host politeness limits concurrency
"""

SEQUENCES["v1_ch10"] = """
sequenceDiagram
    autonumber
    participant Svc as Service
    participant API as Notification API
    participant Pref as Preference Store
    participant Q as Message Queue
    participant Wk as Channel Worker
    participant Pr as Provider (APNs/SMS/Email)
    Svc->>API: send(notification)
    API->>Pref: opted-in? quiet hours?
    alt allowed
        Pref-->>API: yes
        API->>Q: enqueue per-channel message
        Q->>Wk: deliver
        Wk->>Pr: push / SMS / email
        alt success
            Pr-->>Wk: delivered
        else failure
            Wk->>Q: retry (backoff) / dead-letter
        end
    else opted out
        Pref-->>API: no -> drop
    end
    Note over Wk: Idempotency key prevents duplicate sends
"""

SEQUENCES["v1_ch11"] = """
sequenceDiagram
    autonumber
    actor A as Author
    participant PS as Post Service
    participant DB as Post DB
    participant FO as Fanout (async)
    participant FC as Feed Cache
    actor V as Viewer
    A->>PS: publish(post)
    PS->>DB: store post
    PS->>FO: enqueue fan-out
    alt normal user
        FO->>FC: push post_id to each follower feed
    else celebrity
        Note over FO,FC: Skip push - pulled at read time
    end
    V->>FC: GET feed
    FC-->>V: recent post_ids
    V->>DB: hydrate posts (+ merge celebrity pulls)
    DB-->>V: feed content
"""

SEQUENCES["v1_ch12"] = """
sequenceDiagram
    autonumber
    actor A as User A
    participant WA as Conn Server (A)
    participant Ch as Chat Service
    participant KV as Message Store
    participant Dir as Presence/Directory
    participant WB as Conn Server (B)
    actor B as User B
    A->>WA: send(msg) over WebSocket
    WA->>Ch: deliver
    Ch->>KV: persist (time-sortable id)
    Ch->>Dir: where is B connected?
    alt B online
        Dir-->>Ch: Conn Server B
        Ch->>WB: push msg
        WB-->>B: message (WebSocket)
    else B offline
        Note over Ch,KV: Stored; delivered on B's reconnect
    end
    B->>WB: read receipt
"""

SEQUENCES["v1_ch13"] = """
sequenceDiagram
    autonumber
    actor U as User
    participant QS as Query Service
    participant T as Trie Cache (top-K)
    participant Agg as Offline Aggregator
    participant L as Query Logs
    U->>QS: keystroke prefix "sys"
    QS->>T: lookup prefix node
    T-->>QS: cached top-K completions
    QS-->>U: suggestions (< 10 ms)
    Note over Agg,T: --- offline, periodically ---
    L->>Agg: query frequencies
    Agg->>T: rebuild trie + hot-swap
"""

SEQUENCES["v1_ch14"] = """
sequenceDiagram
    autonumber
    actor Cr as Creator
    participant API as API Server
    participant B as Blob Storage
    participant T as Transcoding (DAG)
    participant CDN
    actor V as Viewer
    Cr->>API: initiate upload
    API-->>Cr: pre-signed URL
    Cr->>B: upload original (direct)
    B->>T: trigger transcoding
    T->>T: segment -> parallel transcode -> renditions + manifest
    T->>CDN: distribute renditions
    Note over V,CDN: --- playback ---
    V->>API: get manifest
    API-->>V: HLS/DASH manifest
    V->>CDN: stream adaptive chunks
    CDN-->>V: video (nearest edge)
"""

SEQUENCES["v1_ch15"] = """
sequenceDiagram
    autonumber
    actor D1 as Device 1
    participant API as API Server
    participant Blk as Block Servers
    participant Store as Cloud Storage
    participant Meta as Metadata DB
    participant N as Notification Svc
    actor D2 as Device 2
    D1->>API: file edited
    API->>Blk: upload changed blocks only
    Blk->>Store: store new blocks (dedup by hash)
    API->>Meta: update version + block list
    API->>N: change event
    N->>D2: notify
    D2->>API: pull new metadata
    D2->>Store: fetch missing blocks
    Store-->>D2: blocks -> file converged
"""


# ===========================================================================
# VOLUME 2
# ===========================================================================

SEQUENCES["v2_ch1"] = """
sequenceDiagram
    autonumber
    actor U as User
    participant LBS as Location Service
    participant Idx as Geo Index
    participant Ca as Geo Cache
    participant DB as Business DB
    U->>LBS: search(lat, lng, radius)
    LBS->>Idx: covering cells for radius
    Idx->>Ca: businesses in cells?
    alt cache hit
        Ca-->>Idx: candidate ids
    else miss
        Idx->>DB: fetch by cell
        DB-->>Idx: candidates
        Idx->>Ca: populate
    end
    Idx-->>LBS: candidate businesses
    LBS->>LBS: exact haversine filter + sort
    LBS-->>U: nearby businesses
"""

SEQUENCES["v2_ch2"] = """
sequenceDiagram
    autonumber
    actor U as User
    participant WS as WebSocket Server
    participant PS as Redis Pub/Sub
    participant LC as Location Cache (TTL)
    participant H as History DB
    participant WF as Friend's Session
    U->>WS: location update (every ~30s)
    WS->>LC: store position (short TTL)
    WS->>H: append history (async)
    WS->>PS: publish to user channel
    PS->>WF: deliver to subscribed friends
    WF->>WF: compute distance
    alt within radius
        WF-->>U: friend nearby push
    end
    Note over LC: Stop sharing -> TTL expiry removes you from maps
"""

SEQUENCES["v2_ch3"] = """
sequenceDiagram
    autonumber
    actor U as User
    participant Tile as Tile Service
    participant CDN
    participant Route as Routing Service
    participant G as Road Graph
    participant Tr as Traffic Pipeline
    U->>Tile: request tiles (z,x,y)
    Tile->>CDN: fetch tile
    CDN-->>U: pre-rendered tile
    U->>Route: route(from, to)
    Route->>G: shortest path (A* + contraction hierarchies)
    G-->>Route: path
    Route->>Tr: current edge speeds
    Tr-->>Route: live traffic
    Route-->>U: route geometry + ETA
"""

SEQUENCES["v2_ch4"] = """
sequenceDiagram
    autonumber
    participant P as Producer
    participant L as Partition Leader
    participant F1 as Follower (ISR)
    participant F2 as Follower (ISR)
    participant C as Consumer (group)
    P->>L: produce(topic, key, value)
    L->>L: append to log (offset++)
    par replicate
        L->>F1: replicate
        L->>F2: replicate
    end
    F1-->>L: ack
    F2-->>L: ack
    Note over L,F2: acks=all -> committed once ISR acknowledge
    L-->>P: ack (offset)
    C->>L: poll from committed offset
    L-->>C: batch of messages
    C->>L: commit offset
"""

SEQUENCES["v2_ch5"] = """
sequenceDiagram
    autonumber
    participant T as Target
    participant Col as Collector
    participant TSDB as Time-Series DB
    participant Q as Query Service
    participant AM as Alert Manager
    actor Ops as On-call
    loop every scrape interval
        Col->>T: pull /metrics
        T-->>Col: samples
        Col->>TSDB: append (compressed)
    end
    Q->>TSDB: range query (dashboards)
    Q->>Q: evaluate alert rules
    alt threshold breached
        Q->>AM: fire alert
        AM->>AM: dedupe + group + silence
        AM-->>Ops: notify (page/email)
    end
"""

SEQUENCES["v2_ch6"] = """
sequenceDiagram
    autonumber
    actor Ad as Ad Click
    participant Log as Event Log
    participant St as Stream Aggregator
    participant AggDB as Aggregated DB
    participant Raw as Raw Archive
    participant B as Batch Reconcile
    Ad->>Log: click event (event_id)
    par
        Log->>St: stream
        Log->>Raw: archive raw
    end
    St->>St: dedupe by event_id + watermark
    St->>AggDB: per-minute counts (fast)
    Note over B,Raw: --- periodically ---
    B->>Raw: recompute exact counts
    B->>AggDB: reconcile / correct (billing-grade)
"""

SEQUENCES["v2_ch7"] = """
sequenceDiagram
    autonumber
    actor U as User
    participant S as Search (cache/replica)
    participant Rv as Reservation Service
    participant DB as Reservation DB
    U->>S: search(location, dates)
    S-->>U: available rooms (may be stale)
    U->>Rv: reserve(room, dates, idempotency_key)
    Rv->>DB: BEGIN tx: check-and-decrement inventory
    alt room available
        DB-->>Rv: reserved < total -> decrement OK
        Rv->>DB: COMMIT (record reservation)
        Rv-->>U: confirmed
    else sold out / race lost
        DB-->>Rv: conditional update fails
        Rv-->>U: unavailable (no overselling)
    end
    Note over Rv: Same idempotency_key on retry -> returns original result
"""

SEQUENCES["v2_ch8"] = """
sequenceDiagram
    autonumber
    actor S as Sender
    participant SMTP as SMTP Service
    participant Q as Send Queue
    participant Ext as Recipient Server
    participant St as Mail Storage
    participant Idx as Search Index
    actor R as Recipient
    S->>SMTP: submit message
    SMTP->>Q: enqueue
    Q->>Ext: deliver (retry w/ backoff)
    Ext-->>Q: 250 OK / defer
    Note over Q,Ext: Bounce only after repeated failures
    Ext->>St: store to recipient mailbox
    St->>Idx: async index (metadata + body ref)
    R->>St: IMAP fetch / search
    St-->>R: messages
"""

SEQUENCES["v2_ch9"] = """
sequenceDiagram
    autonumber
    actor Cl as Client
    participant API as API Service
    participant Meta as Metadata Service
    participant Rt as Data Router
    participant D as Data Nodes
    Cl->>API: PUT /{bucket}/{key}
    API->>Rt: placement (erasure code fragments)
    Rt->>D: write fragments across failure domains
    D-->>Rt: acks
    API->>Meta: commit object location + version
    API-->>Cl: 200 (read-after-write consistent)
    Cl->>API: GET /{bucket}/{key}
    API->>Meta: lookup location
    Meta-->>API: fragment refs
    API->>D: read (reconstruct if needed)
    D-->>API: object bytes
    API-->>Cl: object
"""

SEQUENCES["v2_ch10"] = """
sequenceDiagram
    autonumber
    actor P as Player
    participant Sc as Score Service
    participant Z as Redis Sorted Set
    participant DB as Game DB
    actor V as Viewer
    P->>Sc: submit score
    Sc->>Sc: validate server-side (anti-cheat)
    Sc->>Z: ZADD member score
    Sc->>DB: persist (source of truth)
    V->>Sc: get top-N
    Sc->>Z: ZREVRANGE 0 N
    Z-->>Sc: top players
    V->>Sc: my rank
    Sc->>Z: ZREVRANK player
    Z-->>Sc: rank
    Sc-->>V: rank + neighbours
"""

SEQUENCES["v2_ch11"] = """
sequenceDiagram
    autonumber
    actor U as User
    participant Pay as Payment Service
    participant Led as Ledger (double-entry)
    participant PSP as Payment Provider
    participant Rec as Reconciliation
    U->>Pay: pay(amount, idempotency_key)
    Pay->>Pay: dedupe on idempotency_key
    Pay->>Led: record intent (debit/credit)
    Pay->>PSP: charge
    alt PSP responds
        PSP-->>Pay: succeeded
        Pay->>Led: mark succeeded
        Pay-->>U: success
    else timeout / no response
        Note over Pay,Rec: Status stays pending; reconcile later
    end
    Rec->>PSP: pull statements
    Rec->>Led: match + correct discrepancies
"""

SEQUENCES["v2_ch12"] = """
sequenceDiagram
    autonumber
    actor U as User
    participant Cmd as Command Side
    participant ES as Event Store
    participant Proj as Read Model
    participant Saga as Saga Orchestrator
    U->>Cmd: transfer(A -> B, key)
    Cmd->>Cmd: validate funds (per-wallet serialize)
    alt same partition
        Cmd->>ES: append debit A + credit B
        ES->>Proj: project balances
    else cross-partition
        Cmd->>Saga: start saga
        Saga->>ES: debit A (reserve)
        Saga->>ES: credit B
        alt credit fails
            Saga->>ES: compensate (refund A)
        end
    end
    Cmd-->>U: transfer result
"""

SEQUENCES["v2_ch13"] = """
sequenceDiagram
    autonumber
    actor Tr as Trader
    participant GW as Order Gateway
    participant Seq as Sequencer
    participant Log as Event Log
    participant ME as Matching Engine
    participant Book as Order Book
    participant MD as Market Data
    Tr->>GW: submit order
    GW->>Seq: assign global sequence (fairness)
    Seq->>Log: persist BEFORE matching (no loss)
    Seq->>ME: sequenced order
    ME->>Book: match by price-time priority
    alt match found
        Book-->>ME: trade(s)
        ME->>Log: persist trade
        ME->>MD: publish trade + book delta
        MD-->>Tr: fill notification
    else resting
        ME->>Book: add to book
    end
"""
