# Design a Notification System

**Summary**: Send push, SMS, and email notifications reliably at scale using queues, workers, third-party gateways, retries, and dedup.
**Tags**: #system-design #notifications #message-queue #push #sms #email #reliability #volume-1
**Source**: System Design Volume 1.pdf — Chapter 10 (pp. 151–165)
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

**Types of notifications** — mobile push (iOS APNs, Android FCM), SMS
(Twilio/Nexmo), and email (SendGrid/Mailchimp). Each channel has a provider.

**Contact info gathering flow** — when users install the app / sign up, collect
device tokens, phone numbers, and emails, stored in the DB.

**Sending/receiving flow (high-level)** — Services (providers of events) →
**Notification servers** → **Message queues** (one per channel, for buffering)
→ **Workers** → third-party gateways → user devices. A cache and DB hold user
info, settings, and templates.

**Deep dive**
- **Reliability** — do not lose notifications: persist events in a
  **notification log**; deliver **at-least-once** with retries; use an
  **dedupe/idempotency** mechanism so users don't get duplicates (exactly-once
  is impractical across external providers).
- **Additional components** — **notification templates**, user **settings /
  opt-out**, **rate limiting** per user, retry with backoff, security
  (appKey/appSecret), monitoring queued counts, and event tracking/analytics.
- **Updated design** — reflects the above: queues absorb spikes and let each
  channel scale independently.

## Related Notes

- [[Scale From Zero to Millions of Users]]
- [[Design a News Feed System]]
