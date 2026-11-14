# Design Google Drive

**Summary**: Store, sync, and share files across devices using block-level delta sync, a metadata database, block servers, and change notifications.
**Tags**: #system-design #google-drive #file-sync #block-storage #delta-sync #metadata #volume-1
**Source**: System Design Volume 1.pdf — Chapter 15 (pp. 244–263)
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

**Scope & estimation** — upload/download, sync across devices, revision history,
sharing, notifications; strong consistency for file operations; huge storage
(users × GB). Design around read/write of files plus metadata.

**APIs** — upload (simple vs resumable with a pre-signed URL), download, and get
file revisions.

**Move away from a single server** — split into a **metadata DB** and object
storage (e.g. S3), replicated across regions; shard metadata as it grows.

**Sync conflicts** — when two clients edit concurrently, the **first version to
be processed wins**; the later one gets a **conflict** and both versions are
preserved so no data is lost.

**High-level design** — client (watcher, chunker, indexer), block servers,
cloud/object storage, metadata DB, and **notification service** for change
propagation; an offline backup queue.

**Deep dive**
- **Block servers** — split files into **blocks**, compress and encrypt them,
  and upload only **changed blocks** (**delta sync**), deduplicating identical
  blocks.
- **High consistency requirement** — metadata is strongly consistent (memory
  cache + relational DB with ACID) so all clients agree on the current version.
- **Metadata database** — tracks users, files, versions, block lists, and
  workspace/device info.
- **Upload/download flows** — coordinated through block servers, metadata DB,
  cloud storage, and the notification service so other devices converge.

## Related Notes

- [[Design YouTube]]
- [[Scale From Zero to Millions of Users]]
