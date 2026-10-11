"""
Clean, professional architecture-diagram engine (Microsoft Learn / Azure
architecture-center aesthetic): crisp rounded rectangles, a system font,
subtle drop shadows, tidy orthogonal-ish connectors and clear labels.

Pure-Python inline SVG so it renders instantly in Streamlit and exports
cleanly, with no browser or binary dependency.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

FONT = "'Segoe UI', 'Inter', -apple-system, system-ui, sans-serif"

# Microsoft-Learn-ish palette: (fill, stroke, text)
STYLES = {
    "client":  ("#eff6fc", "#0078d4", "#0b4a6f"),
    "edge":    ("#f3f2f1", "#605e5c", "#323130"),   # gateways/LB/CDN
    "service": ("#e6f2fb", "#106ebe", "#0b4a6f"),
    "compute": ("#e8f5e9", "#107c10", "#0b4d1a"),
    "data":    ("#f3e9fb", "#8661c5", "#3b2a5a"),   # databases
    "cache":   ("#fde7e9", "#d13438", "#6e1216"),
    "queue":   ("#fff4ce", "#c19c00", "#5a4a00"),
    "external":("#f0f0f0", "#8a8886", "#323130"),
    "accent":  ("#dff6f0", "#038387", "#014b4e"),
}


def _id(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:8]


@dataclass
class Node:
    id: str
    label: str
    x: float
    y: float
    w: float = 150
    h: float = 62
    kind: str = "service"          # key into STYLES
    shape: str = "rect"            # rect | cylinder | hexagon | circle
    sub: str = ""                  # small secondary line under label


@dataclass
class Edge:
    src: str
    dst: str
    label: str = ""
    dashed: bool = False
    bidir: bool = False


@dataclass
class Group:
    label: str
    x: float
    y: float
    w: float
    h: float
    color: str = "#c8c6c4"


@dataclass
class Diagram:
    title: str = ""
    width: int = 900
    height: int = 500
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)
    groups: List[Group] = field(default_factory=list)

    def node(self, *a, **k) -> "Diagram":
        self.nodes.append(Node(*a, **k)); return self

    def edge(self, *a, **k) -> "Diagram":
        self.edges.append(Edge(*a, **k)); return self

    def group(self, *a, **k) -> "Diagram":
        self.groups.append(Group(*a, **k)); return self

    def _find(self, nid: str) -> Optional[Node]:
        return next((n for n in self.nodes if n.id == nid), None)

    # -- geometry ---------------------------------------------------------
    def _anchor(self, a: Node, b: Node) -> Tuple[float, float, float, float]:
        ax, ay = a.x + a.w / 2, a.y + a.h / 2
        bx, by = b.x + b.w / 2, b.y + b.h / 2
        dx, dy = bx - ax, by - ay
        if abs(dx) >= abs(dy):
            sx = a.x + a.w if dx > 0 else a.x
            sy = ay
            ex = b.x if dx > 0 else b.x + b.w
            ey = by
        else:
            sx = ax
            sy = a.y + a.h if dy > 0 else a.y
            ex = bx
            ey = b.y if dy > 0 else b.y + b.h
        return sx, sy, ex, ey

    # -- rendering --------------------------------------------------------
    def _shape(self, n: Node) -> str:
        fill, stroke, text = STYLES.get(n.kind, STYLES["service"])
        parts = [f'<g filter="url(#ds)">']
        if n.shape == "cylinder":
            e = n.h * 0.16
            parts.append(
                f'<path d="M {n.x} {n.y+e} '
                f'C {n.x} {n.y-e/2} {n.x+n.w} {n.y-e/2} {n.x+n.w} {n.y+e} '
                f'L {n.x+n.w} {n.y+n.h-e} '
                f'C {n.x+n.w} {n.y+n.h+e/2} {n.x} {n.y+n.h+e/2} {n.x} {n.y+n.h-e} Z" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
            )
            parts.append(
                f'<ellipse cx="{n.x+n.w/2}" cy="{n.y+e}" rx="{n.w/2}" ry="{e}" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
            )
        elif n.shape == "hexagon":
            k = n.h / 2
            parts.append(
                f'<path d="M {n.x+k} {n.y} L {n.x+n.w-k} {n.y} '
                f'L {n.x+n.w} {n.y+n.h/2} L {n.x+n.w-k} {n.y+n.h} '
                f'L {n.x+k} {n.y+n.h} L {n.x} {n.y+n.h/2} Z" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
            )
        elif n.shape == "circle":
            parts.append(
                f'<ellipse cx="{n.x+n.w/2}" cy="{n.y+n.h/2}" rx="{n.w/2}" '
                f'ry="{n.h/2}" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
            )
        else:
            parts.append(
                f'<rect x="{n.x}" y="{n.y}" width="{n.w}" height="{n.h}" '
                f'rx="8" ry="8" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
            )
        parts.append("</g>")
        # accent bar on the left for rects (Azure card style)
        if n.shape == "rect":
            parts.append(
                f'<rect x="{n.x}" y="{n.y}" width="4" height="{n.h}" '
                f'rx="2" fill="{stroke}"/>'
            )
        # label
        lines = n.label.split("\n")
        base = n.y + n.h / 2 - (len(lines) - 1) * 8 + (0 if not n.sub else -6)
        for i, ln in enumerate(lines):
            parts.append(
                f'<text x="{n.x+n.w/2}" y="{base + i*16 + 5}" '
                f'text-anchor="middle" font-family="{FONT}" font-size="13.5" '
                f'font-weight="600" fill="{text}">{_esc(ln)}</text>'
            )
        if n.sub:
            parts.append(
                f'<text x="{n.x+n.w/2}" y="{n.y+n.h-9}" text-anchor="middle" '
                f'font-family="{FONT}" font-size="10.5" fill="#605e5c">'
                f'{_esc(n.sub)}</text>'
            )
        return "".join(parts)

    def _edge(self, e: Edge) -> str:
        a, b = self._find(e.src), self._find(e.dst)
        if not a or not b:
            return ""
        sx, sy, ex, ey = self._anchor(a, b)
        dash = 'stroke-dasharray="6 5"' if e.dashed else ""
        parts = [
            f'<path d="M {sx} {sy} L {ex} {ey}" fill="none" stroke="#8a8886" '
            f'stroke-width="1.6" {dash} marker-end="url(#arr)"'
            + (' marker-start="url(#arrs)"' if e.bidir else "") + '/>'
        ]
        if e.label:
            mx, my = (sx + ex) / 2, (sy + ey) / 2
            w = len(e.label) * 6.4 + 10
            parts.append(
                f'<rect x="{mx-w/2}" y="{my-10}" width="{w}" height="18" '
                f'rx="4" fill="#ffffff" stroke="#e1dfdd" stroke-width="1"/>'
            )
            parts.append(
                f'<text x="{mx}" y="{my+3}" text-anchor="middle" '
                f'font-family="{FONT}" font-size="11" fill="#605e5c">'
                f'{_esc(e.label)}</text>'
            )
        return "".join(parts)

    def _group(self, g: Group) -> str:
        return (
            f'<rect x="{g.x}" y="{g.y}" width="{g.w}" height="{g.h}" rx="10" '
            f'fill="none" stroke="{g.color}" stroke-width="1.3" '
            f'stroke-dasharray="4 4"/>'
            f'<text x="{g.x+12}" y="{g.y+18}" font-family="{FONT}" '
            f'font-size="11.5" font-weight="600" fill="#605e5c">'
            f'{_esc(g.label)}</text>'
        )

    def to_svg(self) -> str:
        defs = (
            '<defs>'
            '<marker id="arr" markerWidth="10" markerHeight="10" refX="8" '
            'refY="3" orient="auto"><path d="M0,0 L8,3 L0,6 Z" fill="#8a8886"/>'
            '</marker>'
            '<marker id="arrs" markerWidth="10" markerHeight="10" refX="0" '
            'refY="3" orient="auto"><path d="M8,0 L0,3 L8,6 Z" fill="#8a8886"/>'
            '</marker>'
            '<filter id="ds" x="-20%" y="-20%" width="140%" height="150%">'
            '<feDropShadow dx="0" dy="1.5" stdDeviation="2.2" '
            'flood-color="#000000" flood-opacity="0.12"/></filter>'
            '</defs>'
        )
        body = [self._group(g) for g in self.groups]
        body += [self._edge(e) for e in self.edges]
        body += [self._shape(n) for n in self.nodes]
        title = ""
        top = 0
        if self.title:
            title = (
                f'<text x="24" y="30" font-family="{FONT}" font-size="16" '
                f'font-weight="700" fill="#201f1e">{_esc(self.title)}</text>'
            )
            top = 0
        _ = top
        return (
            f'<svg viewBox="0 0 {self.width} {self.height}" '
            f'xmlns="http://www.w3.org/2000/svg" '
            f'style="width:100%;height:auto;background:#faf9f8;'
            f'border:1px solid #edebe9;border-radius:8px;">'
            f'<rect width="{self.width}" height="{self.height}" fill="#faf9f8"/>'
            f'{defs}{title}{"".join(body)}</svg>'
        )


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
