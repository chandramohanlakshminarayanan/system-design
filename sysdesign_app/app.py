"""
System Design Interview Trainer — Microsoft Learn-style UI.

An interview-realistic study app: for each system it first walks the
candidate through the RIGHT clarifying questions (ambiguity, scope, scale,
constraints), and only after requirements are locked does it present a deep,
end-to-end solution covering estimation, API, data model, architecture and
deep dives on trade-offs, scalability, cost, security, reliability and
bottlenecks.

Run:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

import registry
from schema import Chapter
from diagrams import get_diagram
from sequences import get_sequence
from qa_assistant import render_chat_assistant
from quiz_generator import render_quiz

st.set_page_config(
    page_title="System Design Interview Trainer",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Google Cloud Console-inspired styling
# ---------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto:wght@400;500;700&display=swap');

:root {
  --gc-blue:#1a73e8;        /* GCC primary blue */
  --gc-blue-lt:#e8f0fe;     /* selected / hover tint */
  --gc-blue-mid:#8ab4f8;    /* accent / link */
  --gc-dark:#202124;        /* top-bar background */
  --gc-sidebar:#f8f9fa;     /* sidebar background */
  --gc-border:#dadce0;      /* all dividers */
  --gc-text:#202124;        /* primary text */
  --gc-text-2:#5f6368;      /* secondary text */
  --gc-white:#ffffff;
  --gc-surface:#ffffff;     /* card surfaces */
  --gc-hover:#f1f3f4;       /* hover background */
  --banner-h:64px;
}

html, body, [class*="css"] {
  font-family: 'Google Sans','Roboto',-apple-system,system-ui,sans-serif;
  color: var(--gc-text);
}

/* ================================================================
   TOP BANNER / HEADER
   ================================================================ */
#chandra-banner {
  position:fixed; top:0; left:0; right:0; height:var(--banner-h);
  z-index:1000001;
  background:transparent;
  display:flex; align-items:center; justify-content:center;
  padding:0 200px 0 60px;
  pointer-events:none;
}
#chandra-banner > * { pointer-events:auto; }
#chandra-banner .cb-title {
  color:#323130; font-weight:700; font-size:1.32rem; letter-spacing:.2px;
  font-family:'Google Sans','Roboto',sans-serif; line-height:1.1;
}
#chandra-banner .cb-title .accent {
  background:linear-gradient(90deg,#4a6fa5,#6b5b95);
  -webkit-background-clip:text; background-clip:text; color:transparent;
}
@media (max-width:900px){ #chandra-banner .cb-title .accent { display:none; } }

header[data-testid="stHeader"] {
  background:#e8e4f3 !important;
  position:fixed !important; top:0 !important; left:0 !important; right:0 !important;
  width:100% !important; height:var(--banner-h) !important;
  min-height:var(--banner-h) !important;
  z-index:1000000;
  border-bottom:none !important;
}
[data-testid="stAppViewContainer"] {
  border-top:none !important;
}
header[data-testid="stHeader"] button,
header[data-testid="stHeader"] a,
header[data-testid="stHeader"] span,
header[data-testid="stHeader"] p { color:#323130 !important; }
header[data-testid="stHeader"] button svg,
header[data-testid="stHeader"] svg { color:#323130 !important; fill:#323130 !important; }

/* Deploy button: blue outlined pill on light banner */
header[data-testid="stHeader"] [data-testid="stAppDeployButton"] button {
  background:#4a6fa5 !important;
  border:none !important;
  color:#ffffff !important; border-radius:4px !important;
  font-weight:500 !important; font-size:0.85rem !important;
  padding:5px 12px !important;
}
header[data-testid="stHeader"] [data-testid="stAppDeployButton"] button * {
  color:#ffffff !important; fill:#ffffff !important;
}
/* 3-dots: dark on light banner */
header[data-testid="stHeader"] [data-testid="stMainMenu"] button svg,
header[data-testid="stHeader"] [data-testid="stMainMenuButton"] button svg {
  color:#323130 !important; fill:#323130 !important;
}
/* Expand sidebar >> button */
[data-testid="stExpandSidebarButton"] { position:relative; z-index:1000002 !important; }
[data-testid="stExpandSidebarButton"] button,
[data-testid="stExpandSidebarButton"] svg,
[data-testid="stExpandSidebarButton"] svg * {
  color:#323130 !important; fill:#323130 !important; stroke:#323130 !important;
}

/* ================================================================
   MAIN CONTENT AREA
   ================================================================ */
[data-testid="stAppViewContainer"] { margin-top:var(--banner-h); background:#e8e4f3; }
[data-testid="stAppViewContainer"] .main,
section.main, .stApp { background:#e8e4f3; }

/* Main content rendered as a rounded, floating white surface */
.block-container {
  padding:2rem 2.4rem 2.6rem 2.4rem;
  margin:1.1rem auto 1.6rem auto;
  max-width:1500px;
  background:var(--gc-white);
  border:1px solid var(--gc-border);
  border-radius:20px;
  box-shadow:0 2px 10px rgba(60,64,67,.08);
}

/* ================================================================
   SIDEBAR
   ================================================================ */
section[data-testid="stSidebar"] {
  background:#e8e4f3 !important;
  border-right:none !important;
  box-shadow:none !important;
}
/* sidebar text: dark for readability */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] .stMarkdown {
  color:#201f1e !important;
}
section[data-testid="stSidebar"] [role="heading"],
section[data-testid="stSidebar"] .stMarkdown h2 {
  color:#000000 !important;
  font-size:0.72rem !important; font-weight:700 !important;
  letter-spacing:.08em; text-transform:uppercase; margin:12px 0 4px 10px;
}
section[data-testid="stSidebar"] > div:first-child,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
  padding-top:0.75rem !important;
}
/* Sidebar nav buttons: GCC left-rail style */
section[data-testid="stSidebar"] .stButton>button {
  text-align:left; justify-content:flex-start; width:100%;
  background:transparent; border:none; color:var(--gc-text);
  padding:8px 16px 8px 16px; font-size:0.875rem;
  border-radius:0 24px 24px 0; font-weight:400;
  border-left:3px solid transparent;
  transition:background .15s;
}
section[data-testid="stSidebar"] .stButton>button p,
section[data-testid="stSidebar"] .stButton>button div,
section[data-testid="stSidebar"] .stButton>button span {
  text-align:left !important; width:100%;
  justify-content:flex-start !important;
  color:var(--gc-text) !important;
}
section[data-testid="stSidebar"] .stButton>button:hover {
  background:#d5c9e8 !important; color:#4a6fa5 !important;
}
/* search box on sidebar */
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] input {
  background:var(--gc-white) !important; color:var(--gc-text) !important;
  border-color:var(--gc-border) !important; border-radius:4px !important;
}
/* progress bar: darker fill + border */
section[data-testid="stSidebar"] .stProgress > div > div > div {
  background:#c5bedd !important;
  border:1px solid #b0a8cc !important;
  border-radius:4px !important;
}
section[data-testid="stSidebar"] .stProgress > div > div > div > div {
  background:#7c6fa8 !important;
  border-radius:4px !important;
}
/* sidebar scrollbar: invisible */
section[data-testid="stSidebar"] ::-webkit-scrollbar,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"]::-webkit-scrollbar,
section[data-testid="stSidebar"] > div::-webkit-scrollbar { width:0px; }
section[data-testid="stSidebar"] * {
  scrollbar-width:none; scrollbar-color:transparent transparent;
}

/* ================================================================
   BREADCRUMB
   ================================================================ */
.crumb { color:var(--gc-text-2); font-size:0.82rem; margin-bottom:4px; }
.crumb a { color:var(--gc-blue); text-decoration:none; }
.crumb a:hover { text-decoration:underline; }

/* ================================================================
   PAGE TITLE
   ================================================================ */
h1.pt {
  font-size:1.75rem; font-weight:400; margin:0.2rem 0 0.4rem 0;
  color:var(--gc-text); font-family:'Google Sans','Roboto',sans-serif;
}
.subtitle { color:var(--gc-text-2); font-size:0.95rem; margin-bottom:0.75rem; }

/* ================================================================
   SECTION HEADINGS
   ================================================================ */
h2.unit {
  font-size:1.25rem; font-weight:500; margin:2rem 0 0.5rem 0;
  color:var(--gc-text); padding-bottom:8px;
  border-bottom:1px solid var(--gc-border); scroll-margin-top:72px;
  font-family:'Google Sans','Roboto',sans-serif;
}
h3.sub {
  font-size:1rem; font-weight:500; margin:1.25rem 0 0.3rem 0;
  color:var(--gc-text);
}

/* ================================================================
   CALLOUTS  (GCC-style info banners)
   ================================================================ */
.note, .tip, .warn, .imp {
  border-left:4px solid; border-radius:4px 12px 12px 4px;
  padding:12px 16px; margin:12px 0; font-size:0.9rem;
}
.note { background:#e8f0fe; border-color:var(--gc-blue); color:#174ea6; }
.tip  { background:#e6f4ea; border-color:#34a853; color:#137333; }
.warn { background:#fef7e0; border-color:#fbbc04; color:#7a4100; }
.imp  { background:#fce8e6; border-color:#ea4335; color:#c5221f; }
.callout-title { font-weight:700; display:block; margin-bottom:3px; }

/* ================================================================
   CARDS / MOD CARDS
   ================================================================ */
.modcard {
  border:1px solid var(--gc-border); border-radius:14px;
  padding:16px 18px; margin-bottom:12px;
  background:var(--gc-surface); box-shadow:0 1px 2px rgba(60,64,67,.06);
  transition:box-shadow .15s;
}
.modcard:hover { box-shadow:0 2px 6px rgba(60,64,67,0.18); }

/* ================================================================
   PILLS / CHIPS (GCC chip style)
   ================================================================ */
.pill {
  display:inline-block; background:var(--gc-blue-lt); color:var(--gc-blue);
  border:1px solid #c5d9f7; border-radius:16px;
  padding:2px 10px; font-size:0.72rem; font-weight:500;
}
.pill.v2 { background:#e6f4ea; color:#137333; border-color:#ceead6; }

/* ================================================================
   CLARIFY Q CATEGORIES
   ================================================================ */
.qcat {
  font-size:0.7rem; font-weight:700; letter-spacing:.05em;
  text-transform:uppercase; color:var(--gc-blue);
}
.qtext { font-weight:500; font-size:1.0rem; margin:2px 0 4px 0; }

/* ================================================================
   TABLES
   ================================================================ */
table.dt {
  border-collapse:separate; border-spacing:0; width:100%; font-size:0.875rem;
  margin:8px 0 14px 0; border:1px solid var(--gc-border);
  border-radius:12px; overflow:hidden;
}
table.dt th {
  background:#f1f3f4; text-align:left; padding:10px 12px;
  border-bottom:1px solid var(--gc-border);
  font-weight:500; color:var(--gc-text-2); font-size:0.82rem;
  text-transform:uppercase; letter-spacing:.04em;
}
table.dt td {
  padding:10px 12px; border-bottom:1px solid var(--gc-border);
  vertical-align:top;
}
table.dt tr:last-child td { border-bottom:none; }
table.dt tr:hover td { background:var(--gc-hover); }

/* ================================================================
   API ENDPOINT CHIPS
   ================================================================ */
.api {
  font-family:'Roboto Mono','Cascadia Code',Consolas,monospace;
  background:#f1f3f4; border:1px solid var(--gc-border);
  border-radius:12px; padding:3px 10px; font-size:0.85rem;
  color:#c5221f; font-weight:500;
}

/* ================================================================
   ROUND STREAMLIT NATIVE BLOCKS (code, dataframes, alerts, images, expanders)
   ================================================================ */
[data-testid="stAppViewContainer"] pre,
.stCodeBlock, [data-testid="stCodeBlock"],
[data-testid="stImage"] img,
[data-testid="stExpander"],
[data-testid="stExpander"] details,
.stDataFrame, [data-testid="stDataFrame"],
[data-testid="stTable"],
[data-testid="stAlert"],
[data-testid="stNotification"],
[data-testid="stMetric"] {
  border-radius:14px !important;
  overflow:hidden;
}
[data-testid="stAppViewContainer"] .stTabs [data-baseweb="tab-list"] {
  border-radius:12px;
}

/* ================================================================
   PROGRESS BAR (main content)
   ================================================================ */
.stProgress > div > div > div > div { background-color:var(--gc-blue); }

/* ================================================================
   ON THIS PAGE OUTLINE
   ================================================================ */
.otp-h {
  position:sticky; top:8px; font-weight:700; color:var(--gc-text-2);
  text-transform:uppercase; font-size:0.68rem; letter-spacing:.08em;
  margin-bottom:4px; padding-top:4px;
}
div[data-testid="stVerticalBlock"] .otp-h + div ul { margin:0; padding-left:1rem; }

/* ================================================================
   SCROLL ANCHORS
   ================================================================ */
[data-testid="stHeadingContainer"], .stHeading { scroll-margin-top:72px; }
h1, h2, h3 { scroll-margin-top:72px; }

hr.soft {
  border:none; border-top:1px solid var(--gc-border); margin:1.5rem 0;
}
html { scroll-behavior:smooth; }

/* remove sidebar top padding */
section[data-testid="stSidebar"] > div:first-child,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
  padding-top:0.75rem !important;
}

/* ================================================================
   FORM / INLINE INPUT (chat)
   ================================================================ */
[data-testid="stForm"] {
  border:1px solid var(--gc-border); border-radius:16px;
  padding:10px 12px; background:var(--gc-white);
}
[data-testid="stForm"] button {
  background:var(--gc-blue) !important;
  color:#ffffff !important; border:none !important;
  font-weight:500 !important; border-radius:20px !important;
}
[data-testid="stForm"] button p { color:#ffffff !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Full-width Kiro-style top banner (spans sidebar + main)
# ---------------------------------------------------------------------------
st.markdown(
    '<div id="chandra-banner">'
    '<div class="cb-title">Ace System Design · '
    '<span class="accent">Chandra\'s Arena</span></div>'
    '</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
ss = st.session_state
ss.setdefault("selected", None)      # chapter id or None -> home
ss.setdefault("done", set())
ss.setdefault("revealed", {})        # chapter_id -> bool (solution unlocked)
ss.setdefault("_last_pick", None)    # last handled search selection


def _revealed(cid: str) -> bool:
    return ss.revealed.get(cid, False)


# ---------------------------------------------------------------------------
# Small render helpers
# ---------------------------------------------------------------------------
def callout(kind: str, title: str, body: str):
    st.markdown(
        f'<div class="{kind}"><span class="callout-title">{title}</span>{body}</div>',
        unsafe_allow_html=True,
    )


def unit_h2(text: str, anchor: str):
    # Use Streamlit's native heading anchor so that markdown links of the form
    # [label](#anchor) scroll to it (sanitizer-safe, no custom JS needed).
    st.header(text, anchor=anchor, divider="gray")


def table(columns, rows, cls="dt"):
    head = "".join(f"<th>{c}</th>" for c in columns)
    body = "".join(
        "<tr>" + "".join(f"<td>{cell}</td>" for cell in r) + "</tr>"
        for r in rows
    )
    st.markdown(f'<table class="{cls}"><thead><tr>{head}</tr></thead>'
                f'<tbody>{body}</tbody></table>', unsafe_allow_html=True)


def render_diagram(chapter: Chapter, download: bool = True, key_suffix: str = ""):
    svg = get_diagram(chapter.diagram_id or chapter.id, chapter.title).to_svg()
    st.markdown(svg, unsafe_allow_html=True)
    if download:
        st.download_button("⬇️ Download diagram (SVG)", data=svg,
                           file_name=f"{chapter.id}.svg", mime="image/svg+xml",
                           key=f"dl_{chapter.id}{key_suffix}")


def render_sequence(mermaid_src: str, height: int = 640):
    """Render a Mermaid sequence diagram via mermaid.js (CDN), styled to match.

    The diagram scales to the full width of the content column and uses a
    larger font so it stays readable.
    """
    html = f"""
    <div style="background:#faf9f8;border:1px solid #edebe9;border-radius:8px;
                padding:14px;overflow:auto;width:100%;box-sizing:border-box;">
      <pre class="mermaid" style="margin:0;width:100%;text-align:center;">{mermaid_src}</pre>
    </div>
    <style>
      .mermaid svg {{ width:100% !important; height:auto !important; max-width:none !important; }}
    </style>
    <script type="module">
      import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
      mermaid.initialize({{
        startOnLoad:true, theme:'base',
        sequence:{{ useMaxWidth:false, actorMargin:70, width:170, messageFontSize:15, actorFontSize:15, noteFontSize:14 }},
        themeVariables:{{
          primaryColor:'#efe7ff', primaryBorderColor:'#6d28d9',
          primaryTextColor:'#201f1e', lineColor:'#8a8886',
          actorBkg:'#e6f2fb', actorBorder:'#106ebe', actorTextColor:'#0b4a6f',
          noteBkgColor:'#fff4ce', noteBorderColor:'#c19c00',
          fontFamily:"'Segoe UI','Inter',sans-serif", fontSize:'15px'
        }}
      }});
    </script>
    """
    components.html(html, height=height, scrolling=True)


# ---------------------------------------------------------------------------
# Sidebar — table of contents
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📘 System Design")

    total = len(registry.all_chapters())
    done_n = len(ss.done)

    # --- Autocomplete search: a type-to-filter selectbox over all chapters ---
    all_ch = registry.all_chapters()
    options = ["🔍  Jump to a chapter…"] + [
        f"V{c.volume} · {c.number}. {c.title}" for c in all_ch
    ]
    picked = st.selectbox(
        "Search", options, index=0, label_visibility="collapsed",
        key="chapter_search",
        help="Start typing a chapter name to filter, then select to jump.",
    )
    # Act only when the selection changes to a real chapter, so we don't fight
    # the widget's own state (avoids mutating the widget key after creation).
    if picked and not picked.startswith("🔍") and picked != ss.get("_last_pick"):
        ss["_last_pick"] = picked
        idx = options.index(picked) - 1
        ss.selected = all_ch[idx].id
        st.rerun()

    st.progress(done_n / total if total else 0.0,
                text=f"{done_n} / {total} completed")

    if st.button("🏠  Overview", use_container_width=True):
        ss.selected = None

    # --- Browsable table of contents ---
    for vol in (1, 2):
        chapters = registry.by_volume(vol)
        st.markdown(f"**{registry.VOLUME_TITLES[vol]}**")
        for c in chapters:
            mark = "✓ " if c.id in ss.done else ""
            active = "➤ " if ss.selected == c.id else ""
            if st.button(f"{active}{mark}{c.number}. {c.title}",
                         key=f"nav_{c.id}", use_container_width=True):
                ss.selected = c.id
                st.rerun()


# ---------------------------------------------------------------------------
# Home / overview
# ---------------------------------------------------------------------------
def render_home():
    st.markdown('<div class="crumb">Learn / System Design Interview Trainer</div>',
                unsafe_allow_html=True)
    st.markdown('<h1 class="pt">System Design Interview Trainer</h1>',
                unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Learn to solve system design questions the way '
        'strong candidates do — clarify first, then design deeply. Every '
        'chapter walks you through the right questions, then a complete '
        'solution covering estimation, APIs, data, architecture, and '
        'trade-offs across scalability, cost, security and reliability.</div>',
        unsafe_allow_html=True,
    )

    callout("tip", "How to use this trainer",
            "Open a chapter. First work through the <b>Clarifying questions</b> "
            "— try to answer each before revealing the recommended assumption. "
            "Then unlock the full solution and study the design and trade-offs.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Volumes", "2")
    c2.metric("Chapters", str(total))
    c3.metric("Completed", str(len(ss.done)))

    for vol in (1, 2):
        st.markdown(f"### {registry.VOLUME_TITLES[vol]}")
        cols = st.columns(2)
        for i, c in enumerate(registry.by_volume(vol)):
            with cols[i % 2]:
                pill = "pill v2" if vol == 2 else "pill"
                st.markdown(
                    f'<div class="modcard"><span class="{pill}">Chapter '
                    f'{c.number}</span><br><b style="font-size:1.02rem">'
                    f'{c.title}</b><br><span style="color:#605e5c;'
                    f'font-size:0.9rem">{c.tagline}</span></div>',
                    unsafe_allow_html=True,
                )
                if st.button(f"Start chapter {c.number}", key=f"home_{c.id}"):
                    ss.selected = c.id
                    st.rerun()


# ---------------------------------------------------------------------------
# Chapter page
# ---------------------------------------------------------------------------
def render_chapter(c: Chapter):
    prev, nxt = registry.neighbours(c.id)

    # breadcrumb + header
    st.markdown(
        f'<div class="crumb">Learn / {registry.VOLUME_TITLES[c.volume]} / '
        f'Chapter {c.number}</div>', unsafe_allow_html=True)
    st.markdown(f'<h1 class="pt">{c.title}</h1>', unsafe_allow_html=True)
    st.markdown(f'<div class="subtitle">{c.tagline}</div>',
                unsafe_allow_html=True)

    top = st.columns([1, 1, 2])
    with top[0]:
        done = c.id in ss.done
        if st.checkbox("Mark complete", value=done, key=f"done_{c.id}"):
            ss.done.add(c.id)
        else:
            ss.done.discard(c.id)

    # ----- On this page -----
    main, right = st.columns([5, 1])

    with right:
        links = [
            ("Overview", "overview"),
            ("Clarifying questions", "clarify"),
        ]
        if _revealed(c.id):
            links += [
                ("Requirements", "requirements"),
                ("Estimation", "estimation"),
                ("API design", "api"),
                ("Data model", "data"),
                ("High-level design", "hld"),
                ("Deep dives", "deep"),
                ("Bottlenecks", "bottlenecks"),
                ("Security", "security"),
                ("Wrap-up", "wrap"),
            ]
        st.markdown('<div class="otp-h">On this page</div>',
                    unsafe_allow_html=True)
        # Native markdown anchor links — Streamlit scrolls to the matching
        # st.header(anchor=...) target.
        st.markdown(
            "\n".join(f"- [{t}](#{a})" for t, a in links)
        )

    with main:
        # ----- Overview -----
        unit_h2("Overview", "overview")
        st.markdown(c.overview)
        # The architecture diagram is rendered once, in Step 6 (High-level
        # design), next to the solution walkthrough.

        # ----- Clarify -----
        unit_h2("Step 1 · Clarify the problem", "clarify")
        callout("note", "Why clarify first?",
                "Jumping to a design is the most common interview mistake. "
                "First remove ambiguity: pin down scope, scale, and "
                "constraints. Try answering each question yourself, then "
                "reveal the assumption we'll design against.")

        for i, cq in enumerate(c.clarifying):
            st.markdown(
                f'<div class="modcard"><span class="qcat">{cq.category}</span>'
                f'<div class="qtext">❓ {cq.question}</div>'
                f'<span style="color:#605e5c;font-size:0.9rem">{cq.why}</span>'
                f'</div>', unsafe_allow_html=True)
            with st.expander("Show recommended assumption"):
                st.markdown(f"**We'll assume:** {cq.recommended}")

        st.markdown('<hr class="soft">', unsafe_allow_html=True)
        if not _revealed(c.id):
            callout("imp", "Requirements locked?",
                    "Once you've thought through the questions above, unlock "
                    "the full end-to-end solution.")
            if st.button("🔓  Reveal the full solution", type="primary",
                         key=f"reveal_{c.id}"):
                ss.revealed[c.id] = True
                st.rerun()
        else:
            render_solution(c)

    # ----- prev / next -----
    st.markdown('<hr class="soft">', unsafe_allow_html=True)
    
    # ----- Chat Assistant -----
    render_chat_assistant(c)

    # ----- Quiz (active recall) -----
    render_quiz(c)
    
    st.markdown('<hr class="soft">', unsafe_allow_html=True)
    nav = st.columns([1, 1])
    with nav[0]:
        if prev and st.button(f"←  {prev.number}. {prev.title}",
                              use_container_width=True):
            ss.selected = prev.id
            st.rerun()
    with nav[1]:
        if nxt and st.button(f"{nxt.number}. {nxt.title}  →",
                             use_container_width=True):
            ss.selected = nxt.id
            st.rerun()


def render_solution(c: Chapter):
    # ----- Requirements -----
    if c.requirements:
        unit_h2("Step 2 · Requirements", "requirements")
        r = c.requirements
        cols = st.columns(2)
        with cols[0]:
            st.markdown('<h3 class="sub">Functional</h3>', unsafe_allow_html=True)
            st.markdown("\n".join(f"- {x}" for x in r.functional))
        with cols[1]:
            st.markdown('<h3 class="sub">Non-functional</h3>', unsafe_allow_html=True)
            st.markdown("\n".join(f"- {x}" for x in r.non_functional))
        if r.out_of_scope:
            st.markdown('<h3 class="sub">Out of scope</h3>', unsafe_allow_html=True)
            st.markdown("\n".join(f"- {x}" for x in r.out_of_scope))

    # ----- Estimation -----
    if c.estimation:
        unit_h2("Step 3 · Back-of-the-envelope estimation", "estimation")
        e = c.estimation
        if e.assumptions:
            st.markdown('<h3 class="sub">Assumptions</h3>', unsafe_allow_html=True)
            st.markdown("\n".join(f"- {x}" for x in e.assumptions))
        if e.rows:
            table(["Metric", "Calculation", "Result"],
                  [[r.metric, f'<code>{r.formula}</code>', f"<b>{r.result}</b>"]
                   for r in e.rows])
        for n in e.notes:
            callout("note", "Note", n)

    # ----- API -----
    if c.apis:
        unit_h2("Step 4 · API design", "api")
        for a in c.apis:
            st.markdown(f'<span class="api">{a.signature}</span>',
                        unsafe_allow_html=True)
            st.markdown(a.description)
            if a.notes:
                st.caption(a.notes)
            st.markdown("")

    # ----- Data model -----
    if c.data_model:
        unit_h2("Step 5 · Data model", "data")
        for d in c.data_model:
            st.markdown(f'<h3 class="sub">{d.name}</h3>', unsafe_allow_html=True)
            st.markdown("\n".join(f"- {f}" for f in d.fields))
            if d.store:
                callout("tip", "Storage choice", d.store)

    # ----- High-level design -----
    if c.high_level or c.components:
        unit_h2("Step 6 · High-level design", "hld")
        # Architecture diagram (structure) sits WITH the solution.
        st.markdown('<h3 class="sub">Architecture</h3>', unsafe_allow_html=True)
        render_diagram(c)
        # Sequence diagram (behaviour): how a request flows over time.
        seq = get_sequence(c.id)
        if seq:
            st.markdown('<h3 class="sub" id="sequence">Request lifecycle '
                        '(sequence diagram)</h3>', unsafe_allow_html=True)
            st.caption("How a representative request moves through the system, "
                       "step by step.")
            render_sequence(seq)
        if c.high_level:
            st.markdown('<h3 class="sub">How the design works</h3>',
                        unsafe_allow_html=True)
            st.markdown(c.high_level)
        # Component-by-component walkthrough (book-style depth)
        if c.components:
            st.markdown('<h3 class="sub">Component walkthrough</h3>',
                        unsafe_allow_html=True)
            for comp in c.components:
                with st.expander(f"🧩  {comp.name} — {comp.role}"):
                    st.markdown(comp.detail or comp.role)
        if c.request_flows:
            st.markdown('<h3 class="sub">Request flow (step by step)</h3>',
                        unsafe_allow_html=True)
            for i, f in enumerate(c.request_flows, 1):
                st.markdown(f"{i}. {f}")

    # ----- Deep dives -----
    if c.deep_dives:
        unit_h2("Step 7 · Deep dives & trade-offs", "deep")
        for d in c.deep_dives:
            st.markdown(f'<h3 class="sub">{d.heading}</h3>', unsafe_allow_html=True)
            st.markdown(d.body)
            if d.tradeoffs:
                callout("imp", "Trade-offs",
                        "".join(f"• {t}<br>" for t in d.tradeoffs))

    # ----- Trade-off tables -----
    for t in c.tradeoff_tables:
        st.markdown(f'<h3 class="sub">{t.title}</h3>', unsafe_allow_html=True)
        table(t.columns, t.rows)

    # ----- Bottlenecks -----
    if c.bottlenecks:
        unit_h2("Bottlenecks & how to scale further", "bottlenecks")
        for b in c.bottlenecks:
            st.markdown(f"- {b}")

    # ----- Security -----
    if c.security:
        unit_h2("Security & compliance", "security")
        for s in c.security:
            st.markdown(f"- {s}")

    # ----- Wrap up -----
    if c.wrap_up:
        unit_h2("Wrap-up", "wrap")
        st.markdown(c.wrap_up)


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
if ss.selected:
    ch = registry.get(ss.selected)
    if ch:
        render_chapter(ch)
    else:
        render_home()
else:
    render_home()
