"""
Central registry that assembles all chapters from the per-volume content
modules and exposes lookup helpers used by the UI.
"""

from __future__ import annotations

from typing import Dict, List

from schema import Chapter
from content_v1 import CHAPTERS as V1
from content_v2 import CHAPTERS as V2
from deep_design import COMPONENTS

VOLUME_TITLES = {
    1: "Volume 1 · Foundations & Classic Designs",
    2: "Volume 2 · Advanced Systems & Trade-offs",
}

_ALL: List[Chapter] = V1 + V2

# Attach book-style component walkthroughs where provided.
for _c in _ALL:
    if not _c.components and _c.id in COMPONENTS:
        _c.components = COMPONENTS[_c.id]

_BY_ID: Dict[str, Chapter] = {c.id: c for c in _ALL}


def all_chapters() -> List[Chapter]:
    return _ALL


def by_volume(vol: int) -> List[Chapter]:
    return [c for c in _ALL if c.volume == vol]


def get(cid: str) -> Chapter | None:
    return _BY_ID.get(cid)


def index_of(cid: str) -> int:
    for i, c in enumerate(_ALL):
        if c.id == cid:
            return i
    return -1


def neighbours(cid: str):
    i = index_of(cid)
    prev = _ALL[i - 1] if i > 0 else None
    nxt = _ALL[i + 1] if 0 <= i < len(_ALL) - 1 else None
    return prev, nxt
