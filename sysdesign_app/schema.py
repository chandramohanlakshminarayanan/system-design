"""
Rich, interview-grade content schema for each System Design chapter.

The structure deliberately mirrors how a strong candidate works a real
system-design interview:

    1. Clarify        -> ask the right questions, resolve ambiguity
    2. Requirements   -> functional + non-functional, locked after clarify
    3. Estimation     -> back-of-the-envelope traffic / storage / bandwidth
    4. API design     -> the external contract
    5. Data model     -> entities, storage choices
    6. High-level     -> the architecture and request flows
    7. Deep dives     -> trade-offs, scalability, cost, security, reliability,
                         bottlenecks
    8. Wrap up        -> summary + further-scaling notes

Everything here is plain data so the UI can render it consistently and the
"clarify-then-solve" flow can gate the solution behind the questions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Clarifying-question step (the "gather the right questions" phase)
# ---------------------------------------------------------------------------
@dataclass
class ClarifyQ:
    """A single clarifying question a candidate should ask."""
    category: str            # e.g. "Functional scope", "Scale", "Constraints"
    question: str            # the question to ask the interviewer
    why: str                 # why it matters / what ambiguity it removes
    recommended: str         # the assumption we proceed with (the "answer")


# ---------------------------------------------------------------------------
# Requirements
# ---------------------------------------------------------------------------
@dataclass
class Requirements:
    functional: List[str] = field(default_factory=list)
    non_functional: List[str] = field(default_factory=list)
    out_of_scope: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Estimation (back-of-the-envelope)
# ---------------------------------------------------------------------------
@dataclass
class EstimationRow:
    metric: str              # "Write QPS", "Storage / year", ...
    formula: str             # the arithmetic shown to the candidate
    result: str              # the rounded answer


@dataclass
class Estimation:
    assumptions: List[str] = field(default_factory=list)
    rows: List[EstimationRow] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# API design
# ---------------------------------------------------------------------------
@dataclass
class APIEndpoint:
    signature: str           # "POST /v1/urls"
    description: str
    notes: str = ""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class DataEntity:
    name: str
    fields: List[str] = field(default_factory=list)
    store: str = ""          # which storage engine and why


# ---------------------------------------------------------------------------
# Deep dive (trade-offs, scalability, cost, security, reliability, ...)
# ---------------------------------------------------------------------------
@dataclass
class DeepDive:
    heading: str             # "Scalability", "Cost efficiency", "Security" ...
    body: str                # multi-paragraph markdown
    tradeoffs: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# A component in the high-level design (book-style walkthrough)
# ---------------------------------------------------------------------------
@dataclass
class Component:
    name: str                # "Load balancer", "Feed cache", ...
    role: str                # one-line: what it is / does
    detail: str = ""         # multi-paragraph: why it exists, how it works,
                             # decisions, alternatives considered


# ---------------------------------------------------------------------------
# A trade-off comparison table (option A vs B vs C)
# ---------------------------------------------------------------------------
@dataclass
class TradeoffTable:
    title: str
    columns: List[str]                 # e.g. ["Option", "Pros", "Cons", "Use when"]
    rows: List[List[str]]              # each row aligns to columns


# ---------------------------------------------------------------------------
# The full chapter
# ---------------------------------------------------------------------------
@dataclass
class Chapter:
    id: str
    number: int
    volume: int
    title: str
    tagline: str
    overview: str                                   # markdown intro
    clarifying: List[ClarifyQ] = field(default_factory=list)
    requirements: Optional[Requirements] = None
    estimation: Optional[Estimation] = None
    apis: List[APIEndpoint] = field(default_factory=list)
    data_model: List[DataEntity] = field(default_factory=list)
    high_level: str = ""                            # markdown design narrative
    components: List["Component"] = field(default_factory=list)  # deep walkthrough
    request_flows: List[str] = field(default_factory=list)
    deep_dives: List[DeepDive] = field(default_factory=list)
    tradeoff_tables: List[TradeoffTable] = field(default_factory=list)
    bottlenecks: List[str] = field(default_factory=list)
    security: List[str] = field(default_factory=list)
    wrap_up: str = ""                               # markdown summary
    diagram_id: str = ""                            # key into diagrams.py
