"""
Quiz Generator using Apple Foundation Model.

Generates multiple-choice quizzes from a chapter's content on-device, presents
them interactively, scores the user, and tracks quiz completion per chapter.
Reinforces learning through active recall.
"""

import asyncio
import json
import re
import streamlit as st
import apple_fm_sdk as fm
from schema import Chapter


# ---------------------------------------------------------------------------
# LLM-backed quiz question generation
# ---------------------------------------------------------------------------
class QuizGenerator:
    """Generates multiple-choice quiz questions from chapter content."""

    def __init__(self):
        self.model = fm.SystemLanguageModel()
        self.session = None

    async def _get_session(self):
        if self.session is None:
            is_available, reason = self.model.is_available()
            if not is_available:
                raise RuntimeError(f"Apple Foundation Model not available: {reason}")
            self.session = fm.LanguageModelSession(model=self.model)
        return self.session

    def _build_context(self, chapter: Chapter) -> str:
        """
        Assemble a COMPACT context string from the chapter.

        Kept deliberately small: the on-device model has a limited input
        window, and large chapters (e.g. URL Shortener) otherwise overflow it
        with a "Context window size exceeded" error. We favour headings and
        short snippets over full narrative text.
        """
        parts = [
            f"Chapter {chapter.number}: {chapter.title}",
            f"Tagline: {chapter.tagline}",
            f"Overview: {chapter.overview[:400]}",
        ]
        if chapter.requirements:
            fns = "; ".join(chapter.requirements.functional[:4])
            if fns:
                parts.append(f"Functional requirements: {fns}")
        if chapter.deep_dives:
            dd = "; ".join(d.heading for d in chapter.deep_dives[:6])
            parts.append(f"Key topics: {dd}")
        if chapter.tradeoff_tables:
            tt = "; ".join(t.title for t in chapter.tradeoff_tables[:4])
            parts.append(f"Trade-off topics: {tt}")

        context = "\n".join(parts)
        # Hard cap the total context so the prompt always fits the input window.
        return context[:1200]

    async def generate_quiz(self, chapter: Chapter, num_questions: int = 5) -> list:
        """
        Generate a list of multiple-choice questions from the chapter.

        Returns a list of dicts:
            {"question": str, "options": [str, str, str, str],
             "correct_index": int, "explanation": str}
        """
        context = self._build_context(chapter)
        prompt = (
            "You are a system design instructor. Based ONLY on the chapter "
            "content below, write "
            f"{num_questions} multiple-choice quiz questions that test "
            "understanding of the key concepts and trade-offs.\n\n"
            f"CHAPTER CONTENT:\n{context}\n\n"
            "Rules:\n"
            "- Each question has exactly 4 options.\n"
            "- Exactly one option is correct.\n"
            "- Keep each option under 12 words and each explanation to one short sentence.\n"
            "- Vary difficulty; focus on concepts, not trivia.\n\n"
            "Respond with ONLY valid JSON (no markdown, no prose) in this exact shape:\n"
            '{"questions": [{"question": "...", "options": ["A","B","C","D"], '
            '"correct_index": 0, "explanation": "..."}]}'
        )

        # The on-device model occasionally truncates long outputs. Try a couple
        # of times and keep the attempt that yields the most valid questions.
        # A FRESH session is used each attempt so accumulated context can't
        # overflow the input window ("Context window size exceeded").
        best: list = []
        last_err: Exception | None = None
        for _ in range(2):
            is_available, reason = self.model.is_available()
            if not is_available:
                raise RuntimeError(f"Apple Foundation Model not available: {reason}")
            session = fm.LanguageModelSession(model=self.model)
            try:
                raw = await session.respond(prompt=prompt)
                parsed = self._parse_quiz(raw, num_questions)
            except ValueError as e:
                last_err = e
                continue
            except Exception as e:  # e.g. context window exceeded
                last_err = e
                continue
            if len(parsed) > len(best):
                best = parsed
            if len(best) >= num_questions:
                break

        if not best:
            raise last_err or ValueError("No valid questions could be parsed. Try again.")
        return best

    @classmethod
    def _parse_quiz(cls, raw: str, num_questions: int) -> list:
        """
        Robustly parse the model's response into quiz questions.

        The on-device model sometimes truncates its output mid-JSON when it
        hits the token limit. So we (1) try strict JSON first, and if that
        fails (2) fall back to extracting each complete question object with a
        regex, salvaging every well-formed question even when the tail is cut
        off.
        """
        text = cls._strip_fences(raw)

        # ---- Strategy 1: strict JSON parse of the whole object ----------
        questions = cls._try_strict_json(text)

        # ---- Strategy 2: salvage complete question objects by regex -----
        if not questions:
            questions = cls._salvage_questions(text)

        cleaned = cls._validate(questions, num_questions)
        if not cleaned:
            raise ValueError("No valid questions could be parsed. Try again.")
        return cleaned

    # -- parsing helpers ---------------------------------------------------
    @staticmethod
    def _strip_fences(raw: str) -> str:
        text = raw.strip()
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
        return text

    @staticmethod
    def _try_strict_json(text: str):
        """Try to parse the outermost {...} as JSON. Return [] on failure."""
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return []
        candidate = text[start:end + 1]
        try:
            data = json.loads(candidate)
            return data.get("questions", []) if isinstance(data, dict) else []
        except json.JSONDecodeError:
            return []

    @staticmethod
    def _salvage_questions(text: str):
        """
        Extract each complete {...} question object individually. This works
        even when the overall JSON is truncated, because we only keep the
        objects that are themselves complete and parseable.
        """
        salvaged = []
        # Find balanced {...} blocks that look like question objects.
        depth = 0
        buf_start = None
        for i, ch in enumerate(text):
            if ch == "{":
                if depth == 0:
                    buf_start = i
                depth += 1
            elif ch == "}":
                if depth > 0:
                    depth -= 1
                    if depth == 0 and buf_start is not None:
                        block = text[buf_start:i + 1]
                        if '"question"' in block and '"options"' in block:
                            try:
                                salvaged.append(json.loads(block))
                            except json.JSONDecodeError:
                                pass  # skip incomplete/garbled block
                        buf_start = None
        return salvaged

    @staticmethod
    def _validate(questions, num_questions: int):
        cleaned = []
        for q in questions[:num_questions]:
            if not isinstance(q, dict):
                continue
            opts = q.get("options", [])
            ci = q.get("correct_index", 0)
            if (isinstance(q.get("question"), str)
                    and isinstance(opts, list) and len(opts) == 4
                    and isinstance(ci, int) and 0 <= ci < 4):
                cleaned.append({
                    "question": q["question"].strip(),
                    "options": [str(o).strip() for o in opts],
                    "correct_index": ci,
                    "explanation": str(q.get("explanation", "")).strip(),
                })
        return cleaned


@st.cache_resource
def get_quiz_generator():
    """Get or create a cached quiz generator instance."""
    return QuizGenerator()


# ---------------------------------------------------------------------------
# Session-state helpers
# ---------------------------------------------------------------------------
def _quiz_key(chapter_id: str) -> str:
    return f"quiz_{chapter_id}"


def _init_quiz_state(chapter_id: str):
    key = _quiz_key(chapter_id)
    if key not in st.session_state:
        st.session_state[key] = {
            "questions": [],       # generated questions
            "answers": {},         # {q_index: selected_option_index}
            "submitted": False,    # whether the user has submitted
            "score": None,         # last score
        }


def is_quiz_passed(chapter_id: str, pass_ratio: float = 0.6) -> bool:
    """Return True if the user has passed this chapter's quiz."""
    state = st.session_state.get(_quiz_key(chapter_id))
    if not state or state.get("score") is None:
        return False
    total = len(state["questions"]) or 1
    return (state["score"] / total) >= pass_ratio


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
_QUIZ_CSS = """
<style>
.quiz-head {
  display:flex; align-items:center; gap:10px; margin:6px 0 4px 0;
}
.quiz-head .quiz-avatar {
  width:34px; height:34px; border-radius:10px; flex:none;
  background:linear-gradient(135deg,#0e9f6e,#057a55);
  display:flex; align-items:center; justify-content:center; font-size:18px;
  box-shadow:0 2px 8px rgba(14,159,110,0.25);
}
.quiz-head .quiz-title { font-weight:700; font-size:1.15rem; color:#201f1e; line-height:1.1; }
.quiz-head .quiz-sub   { font-size:0.8rem; color:#605e5c; }

.quiz-q {
  background:#f9f8fc; border:1px solid #e1dfdd; border-radius:12px;
  padding:14px 16px; margin:10px 0;
}
.quiz-q .qnum { font-weight:700; color:#7c3aed; font-size:0.85rem; }
.quiz-q .qtext { font-weight:600; color:#201f1e; margin:2px 0 6px 0; }

.quiz-correct { color:#057a55; font-weight:600; }
.quiz-wrong   { color:#c81e1e; font-weight:600; }
.quiz-explain { color:#605e5c; font-size:0.9rem; margin-top:4px; }

.quiz-score-card {
  background:linear-gradient(135deg,#ecfdf5,#d1fae5);
  border:1px solid #a7f3d0; border-radius:12px; padding:16px;
  text-align:center; margin:12px 0;
}
.quiz-score-card.fail {
  background:linear-gradient(135deg,#fef2f2,#fee2e2);
  border-color:#fecaca;
}
.quiz-score-num { font-size:2rem; font-weight:800; color:#057a55; }
.quiz-score-card.fail .quiz-score-num { color:#c81e1e; }
</style>
"""


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
def render_quiz(chapter: Chapter):
    """Render the interactive quiz section for a chapter."""
    st.markdown("---")
    st.markdown(_QUIZ_CSS, unsafe_allow_html=True)
    _init_quiz_state(chapter.id)
    key = _quiz_key(chapter.id)
    state = st.session_state[key]

    # Header
    passed = is_quiz_passed(chapter.id)
    badge = " ✅" if passed else ""
    st.markdown(
        '<div class="quiz-head">'
        '<div class="quiz-avatar">🧠</div>'
        f'<div><div class="quiz-title">Test Yourself{badge}</div>'
        '<div class="quiz-sub">Active recall quiz generated from this chapter</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # No quiz yet — show a generate button
    if not state["questions"]:
        col1, col2 = st.columns([0.3, 0.7])
        with col1:
            num_q = st.selectbox("Questions", [3, 5, 7, 10], index=1,
                                 key=f"numq_{chapter.id}",
                                 label_visibility="collapsed")
        with col2:
            if st.button("🎯  Generate Quiz", type="primary",
                         key=f"genquiz_{chapter.id}", use_container_width=True):
                with st.spinner("Generating quiz from this chapter…"):
                    try:
                        questions = asyncio.run(
                            get_quiz_generator().generate_quiz(chapter, num_q)
                        )
                        state["questions"] = questions
                        state["answers"] = {}
                        state["submitted"] = False
                        state["score"] = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not generate quiz: {e}")
                        st.caption("Make sure Apple Foundation Model is available.")
        return

    # We have questions — render them
    questions = state["questions"]
    submitted = state["submitted"]

    for i, q in enumerate(questions):
        st.markdown(
            f'<div class="quiz-q"><span class="qnum">Question {i + 1}</span>'
            f'<div class="qtext">{q["question"]}</div></div>',
            unsafe_allow_html=True,
        )

        # Radio for options. Disabled after submission.
        current = state["answers"].get(i)
        selected = st.radio(
            f"q_{chapter.id}_{i}",
            options=list(range(len(q["options"]))),
            format_func=lambda idx, opts=q["options"]: opts[idx],
            key=f"radio_{chapter.id}_{i}",
            index=current if current is not None else None,
            label_visibility="collapsed",
            disabled=submitted,
        )
        if not submitted:
            state["answers"][i] = selected

        # After submission: show correctness + explanation
        if submitted:
            chosen = state["answers"].get(i)
            correct = q["correct_index"]
            if chosen == correct:
                st.markdown(
                    f'<div class="quiz-correct">✅ Correct — '
                    f'{q["options"][correct]}</div>',
                    unsafe_allow_html=True)
            else:
                chosen_txt = q["options"][chosen] if chosen is not None else "—"
                st.markdown(
                    f'<div class="quiz-wrong">❌ You chose: {chosen_txt}</div>'
                    f'<div class="quiz-correct">Correct: {q["options"][correct]}</div>',
                    unsafe_allow_html=True)
            if q["explanation"]:
                st.markdown(f'<div class="quiz-explain">💡 {q["explanation"]}</div>',
                            unsafe_allow_html=True)

    # Action buttons
    if not submitted:
        if st.button("Submit answers", type="primary",
                     key=f"submitquiz_{chapter.id}", use_container_width=True):
            score = sum(
                1 for i, q in enumerate(questions)
                if state["answers"].get(i) == q["correct_index"]
            )
            state["score"] = score
            state["submitted"] = True
            st.rerun()
    else:
        # Score card
        score = state["score"]
        total = len(questions)
        ratio = score / total if total else 0
        passed_now = ratio >= 0.6
        card_cls = "quiz-score-card" if passed_now else "quiz-score-card fail"
        verdict = "Great job! 🎉" if passed_now else "Keep studying — you'll get it! 📚"
        st.markdown(
            f'<div class="{card_cls}">'
            f'<div class="quiz-score-num">{score} / {total}</div>'
            f'<div>{verdict}</div></div>',
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔁  Retake", key=f"retake_{chapter.id}",
                         use_container_width=True):
                state["answers"] = {}
                state["submitted"] = False
                state["score"] = None
                st.rerun()
        with col2:
            if st.button("🆕  New quiz", key=f"newquiz_{chapter.id}",
                         use_container_width=True):
                state["questions"] = []
                state["answers"] = {}
                state["submitted"] = False
                state["score"] = None
                st.rerun()
