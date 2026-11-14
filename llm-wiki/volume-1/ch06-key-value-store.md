# Design a Key-Value Store

**Summary**: A distributed, highly available key-value store (Dynamo-style) using consistent hashing, replication, quorum consistency, versioning, and failure handling.
**Tags**: #system-design #key-value-store #cap-theorem #quorum #vector-clocks #gossip #merkle-tree #volume-1
**Source**: System Design Volume 1.pdf — Chapter 6 (pp. 87–109)
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

**Scope** — support `get(key)` / `put(key, value)`; tunable trade-offs among
consistency, availability, low latency, and large data size.

**Single-server store** — a hash table in memory; add compression and
disk-spillover, but one server can't hold everything → distributed store.

**CAP theorem** — under a network partition you must choose Consistency or
Availability. Systems are classified CP, AP, or CA (CA is impractical in
distributed systems). A Dynamo-style store typically chooses **AP**.

**System components**
- **Data partition** — use **consistent hashing** to spread keys across nodes
  and add/remove nodes with minimal movement.
- **Data replication** — replicate each key to the next **N** nodes on the ring
  (skipping virtual duplicates), spanning failure domains.
- **Consistency** — quorum: **W** (write ack count), **R** (read ack count), **N**
  (replicas). `W + R > N` guarantees strong consistency; tune for latency.
- **Consistency models** — strong, weak, eventual (Dynamo-style uses eventual).
- **Inconsistency resolution: versioning** — **vector clocks** detect and
  reconcile conflicting concurrent writes.
- **Handling failures** — detect via **gossip protocol**; temporary failures use
  **sloppy quorum** + **hinted handoff**; permanent failures repair replicas via
  **anti-entropy with Merkle trees**.

**Architecture** — every node has the same responsibilities (partitioning,
replication, failure handling); write path (commit log → memtable → SSTable) and
read path (memtable/cache → bloom filter → SSTables).

## Related Notes

- [[Design Consistent Hashing]]
- [[Design a Unique ID Generator in Distributed Systems]]
- [[Scale From Zero to Millions of Users]]
