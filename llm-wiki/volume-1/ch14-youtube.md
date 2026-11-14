# Design YouTube

**Summary**: Upload, transcode (DAG pipeline), store, and stream video globally with adaptive bitrate and CDN delivery.
**Tags**: #system-design #video #youtube #transcoding #cdn #blob-storage #dag #volume-1
**Source**: System Design Volume 1.pdf — Chapter 14 (pp. 220–243)
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

**Scope & estimation** — support upload and smooth playback across devices, at
global scale; billions of views; DAU × videos/day drives storage/bandwidth.
Build on top of **CDN** and **blob storage** rather than reinventing them.

**Video uploading flow** — client uploads the **original video to blob storage**;
metadata is recorded (metadata DB/cache); a **transcoding** step produces
multiple formats/resolutions; transcoded videos go to blob storage and are
distributed to the CDN; a completion event updates metadata.

**Video streaming flow** — the client streams from the **nearest CDN edge** using
a streaming protocol with **adaptive bitrate** (quality adapts to bandwidth).

**Deep dive**
- **Video transcoding** — needed for compatibility and multiple resolutions.
- **Directed acyclic graph (DAG) model** — express transcoding as a DAG of tasks
  (inspection, video/audio/thumbnail branches, merge) for parallelism and
  flexibility.
- **Transcoding architecture** — preprocessor (splits into segments / GOPs),
  DAG scheduler, resource manager, task workers, encoded-video queues, and a
  completion handler.
- **System optimizations** — speed (parallel upload of segments, place upload
  centers near users), safety (pre-signed upload URLs, DRM), cost (serve
  popular videos from CDN, others from origin; tiered storage).
- **Error handling** — recoverable (retry) vs non-recoverable (fail fast) errors
  across the pipeline.

## Related Notes

- [[Design Google Drive]]
- [[Scale From Zero to Millions of Users]]
