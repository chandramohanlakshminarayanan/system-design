# Back-of-the-Envelope Estimation

**Summary**: Quick approximation techniques (powers of two, latency numbers, availability nines, QPS/storage) to size a system during an interview.
**Tags**: #system-design #estimation #capacity-planning #latency #availability #volume-1
**Source**: System Design Volume 1.pdf — Chapter 2 (pp. 34–41)
**Created**: 2026-09-26
**Last Updated**: 2026-09-26

---

## Content

Estimation turns a vague prompt into concrete constraints. Aim for the right
order of magnitude, not precision.

- **Power of two** — data volume units: 1 KB = 2^10 bytes, MB = 2^20,
  GB = 2^30, TB = 2^40, PB = 2^50.
- **Latency numbers every programmer should know** — memory reference ~100 ns;
  reading 1 MB from memory much faster than from SSD or disk; a round trip
  within a data center ~500 µs; cross-continent round trips ~100 ms. Takeaways:
  memory is fast, disk is slow, avoid disk seeks, compress before sending over
  the network, and cross-region calls are expensive.
- **Availability numbers** — "nines": 99.9% ≈ 8.76 h/yr down; 99.99% ≈
  52.6 min/yr; 99.999% ≈ 5.26 min/yr. Higher availability costs more redundancy.
- **Example: estimate Twitter QPS and storage** — assume DAU, tweets/user/day,
  and media percentage; derive average and peak QPS and 5-year media storage.
- **Tips** — state assumptions, round aggressively, label your numbers, and
  design for **peak** load, not average.

## Related Notes

- [[A Framework for System Design Interviews]]
- [[Scale From Zero to Millions of Users]]
