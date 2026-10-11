"""
Interactive Chat Assistant using Apple Foundation Model.
Provides on-device LLM-powered conversation about system design concepts with history.
Uses Streamlit's native chat components for a polished experience with Enter-key support.
"""

import asyncio
import streamlit as st
import apple_fm_sdk as fm
from schema import Chapter


class ChatAssistant:
    """Manages multi-turn chat with the on-device Apple Foundation Model."""

    def __init__(self):
        self.model = fm.SystemLanguageModel()
        self.session = None

    async def _get_session(self):
        """Lazily initialize and return the language model session."""
        if self.session is None:
            is_available, reason = self.model.is_available()
            if not is_available:
                raise RuntimeError(f"Apple Foundation Model not available: {reason}")
            self.session = fm.LanguageModelSession(model=self.model)
        return self.session

    async def send_message(self, message: str, chapter: Chapter,
                           conversation_history: list) -> str:
        """
        Send a message and get a response in the context of conversation history.

        Args:
            message: The user's current message
            chapter: The current Chapter object for context
            conversation_history: List of (role, content) tuples from prior messages

        Returns:
            The LLM's response as a string
        """
        chapter_context = (
            "You are a friendly system design expert helping users understand "
            'concepts from the book "System Design Interview".\n\n'
            f"Current Chapter: {chapter.number}. {chapter.title}\n"
            f"Tagline: {chapter.tagline}\n"
            f"Overview: {chapter.overview[:500]}...\n\n"
            "You are having a conversation about this chapter. Be conversational, "
            "helpful, and clear. Reference the chapter when relevant. Keep answers "
            "concise but thorough (1-3 paragraphs)."
        )

        conv_context = ""
        if conversation_history:
            conv_context = "\n\nPrevious conversation:\n"
            for role, content in conversation_history[-6:]:
                conv_context += f"{role}: {content}\n"

        prompt = f"{chapter_context}{conv_context}\nUser: {message}\n\nSend a thoughtful response."

        session = await self._get_session()
        response = await session.respond(prompt=prompt)
        return response


@st.cache_resource
def get_chat_assistant():
    """Get or create a cached chat assistant instance."""
    return ChatAssistant()


def init_chat_history(chapter_id: str):
    """Initialize chat history for a specific chapter if it doesn't exist."""
    history_key = f"chat_history_{chapter_id}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []


# ---- styling for the native chat components -------------------------------
_CHAT_CSS = """
<style>
/* chat panel wrapper */
.chat-panel-head {
  display:flex; align-items:center; gap:10px; margin:6px 0 4px 0;
}
.chat-panel-head .chat-avatar {
  width:34px; height:34px; border-radius:50%; flex:none;
  background:#1a73e8;
  display:flex; align-items:center; justify-content:center; font-size:16px;
}
.chat-panel-head .chat-title { font-weight:500; font-size:1.05rem; color:#202124; line-height:1.1; }
.chat-panel-head .chat-sub   { font-size:0.78rem; color:#5f6368; }

/* native chat message bubbles */
[data-testid="stChatMessage"] {
  border-radius:8px; padding:2px 4px; margin-bottom:6px;
  background:transparent;
}
/* user messages: GCC blue tint */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background:#e8f0fe;
}
/* the inline form input box */
[data-testid="stForm"] {
  border:1px solid #dadce0; border-radius:8px; padding:10px 12px;
  background:#ffffff;
}
[data-testid="stForm"] input {
  border-radius:4px !important;
}
/* Send button: GCC blue */
[data-testid="stForm"] button {
  background:#1a73e8 !important;
  color:#ffffff !important; border:none !important; font-weight:500 !important;
  border-radius:4px !important;
}
[data-testid="stForm"] button:hover {
  background:#1765cc !important;
}
[data-testid="stForm"] button p { color:#ffffff !important; }
</style>
"""


def render_chat_assistant(chapter: Chapter):
    """
    Render a polished chat assistant using Streamlit's native chat widgets.
    - st.chat_input handles the Enter key automatically.
    - st.chat_message renders proper chat bubbles with avatars.

    Args:
        chapter: The current Chapter object
    """
    st.markdown("---")
    st.markdown(_CHAT_CSS, unsafe_allow_html=True)

    init_chat_history(chapter.id)
    history_key = f"chat_history_{chapter.id}"

    # Header row with avatar + clear button
    head_col, clear_col = st.columns([0.8, 0.2])
    with head_col:
        st.markdown(
            '<div class="chat-panel-head">'
            '<div class="chat-avatar">🤖</div>'
            '<div><div class="chat-title">AI Tutor</div>'
            '<div class="chat-sub">Ask about this chapter · Enter to send</div></div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with clear_col:
        if st.session_state[history_key]:
            if st.button("🗑️ Clear", key=f"clear_{chapter.id}",
                         use_container_width=True):
                st.session_state[history_key] = []
                st.rerun()

    # Render the conversation so far in native chat bubbles
    for role, content in st.session_state[history_key]:
        if role == "User":
            with st.chat_message("user", avatar="🧑‍💻"):
                st.markdown(content)
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(content)

    # Inline input using a FORM. A form submits when the user presses Enter
    # inside the text box, and — unlike st.chat_input — it stays inline in the
    # page flow instead of docking to the bottom of the viewport.
    with st.form(key=f"chat_form_{chapter.id}", clear_on_submit=True):
        in_col, btn_col = st.columns([0.85, 0.15])
        with in_col:
            user_input = st.text_input(
                "Message",
                placeholder="Ask me anything about this chapter…",
                label_visibility="collapsed",
                key=f"chat_text_{chapter.id}",
            )
        with btn_col:
            submitted = st.form_submit_button("Send ➤", use_container_width=True)

    if submitted and user_input and user_input.strip():
        # Store the user's message and get the assistant reply
        st.session_state[history_key].append(("User", user_input.strip()))
        with st.spinner("Thinking…"):
            try:
                response = asyncio.run(
                    get_chat_assistant().send_message(
                        user_input.strip(),
                        chapter,
                        st.session_state[history_key][:-1],
                    )
                )
                st.session_state[history_key].append(("Assistant", response))
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.caption("Make sure Apple Foundation Model is available on your system.")
                st.session_state[history_key].pop()
        # Re-run so the new messages render as bubbles above the form
        st.rerun()
