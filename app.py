import streamlit as st
import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="PDF Chat Assistant",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  :root {
    --bg-main:      #212121;
    --bg-sidebar:   #171717;
    --bg-input:     #2f2f2f;
    --text-primary: #ececec;
    --text-muted:   #8e8ea0;
    --accent:       #10a37f;
    --accent-hover: #0d8c6d;
    --border:       #3a3a3a;
    --radius:       12px;
  }
  .stApp { background-color: var(--bg-main) !important; }
  [data-testid="stSidebar"] {
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border);
  }
  [data-testid="stSidebar"] * { color: var(--text-primary) !important; }

  /* ── Streamlit header: style it dark, DON'T hide it (hiding breaks the sidebar toggle) ── */
  #MainMenu { visibility: hidden; }
  footer    { visibility: hidden; }
  [data-testid="stHeader"] {
    background-color: var(--bg-main) !important;
    border-bottom: 1px solid var(--border) !important;
  }
  /* Hide deploy / status widgets — keep stToolbar so sidebar toggle stays clickable */
  .stAppDeployButton             { display: none !important; }
  [data-testid="stDecoration"]   { display: none !important; }
  [data-testid="stStatusWidget"] { display: none !important; }

  /* Native sidebar open/close controls (Streamlit 1.37+ and legacy) */
  [data-testid="stSidebarCollapseButton"],
  [data-testid="collapsedControl"] {
    color: var(--text-primary) !important;
    background-color: var(--bg-sidebar) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
  }
  [data-testid="stSidebarCollapseButton"] svg,
  [data-testid="collapsedControl"] svg {
    fill: var(--text-primary) !important;
    stroke: var(--text-primary) !important;
  }


  /* ── All text elements ── */
  h1,h2,h3,h4,h5,h6,p,label,span,div,small,li,a {
    color: var(--text-primary) !important;
  }

  /* ── Chat messages ── */
  [data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
  }

  /* ── Chat input box ── */
  [data-testid="stChatInput"] {
    background-color: var(--bg-input) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
  }
  [data-testid="stChatInput"] > div {
    background-color: var(--bg-input) !important;
  }
  [data-testid="stChatInput"] textarea,
  [data-testid="stChatInput"] textarea:focus,
  [data-testid="stChatInput"] p {
    color: var(--text-primary) !important;
    background-color: transparent !important;
    -webkit-text-fill-color: var(--text-primary) !important;
  }
  [data-testid="stChatInput"] textarea::placeholder {
    color: var(--text-muted) !important;
    -webkit-text-fill-color: var(--text-muted) !important;
    opacity: 1 !important;
  }

  /* ── Buttons ── */
  .stButton > button {
    background-color: transparent !important;
    color: var(--text-primary) !important;
    -webkit-text-fill-color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    transition: background 0.2s;
  }
  .stButton > button:hover {
    background-color: var(--bg-input) !important;
    border-color: var(--accent) !important;
  }
  .stButton > button[kind="primary"] {
    background-color: var(--accent) !important;
    border-color: var(--accent) !important;
    color: #fff !important;
    -webkit-text-fill-color: #fff !important;
  }
  .stButton > button[kind="primary"]:hover {
    background-color: var(--accent-hover) !important;
  }
  /* Button inner text/p tags */
  .stButton > button p,
  .stButton > button span,
  .stButton > button div {
    color: inherit !important;
    -webkit-text-fill-color: inherit !important;
  }

  /* ── Sidebar text inputs ── */
  [data-testid="stSidebar"] input,
  [data-testid="stSidebar"] textarea,
  [data-testid="stSidebar"] input:focus,
  [data-testid="stSidebar"] textarea:focus {
    background-color: var(--bg-input) !important;
    color: var(--text-primary) !important;
    -webkit-text-fill-color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
  }
  [data-testid="stSidebar"] input::placeholder,
  [data-testid="stSidebar"] textarea::placeholder {
    color: var(--text-muted) !important;
    -webkit-text-fill-color: var(--text-muted) !important;
    opacity: 1 !important;
  }

  /* ── File uploader ── */
  [data-testid="stFileUploader"] {
    background-color: var(--bg-input) !important;
    border: 2px dashed var(--border) !important;
    border-radius: 8px !important;
  }
  [data-testid="stFileUploader"] * {
    color: var(--text-primary) !important;
    -webkit-text-fill-color: var(--text-primary) !important;
  }
  [data-testid="stFileUploader"] small,
  [data-testid="stFileUploader"] span {
    color: var(--text-muted) !important;
    -webkit-text-fill-color: var(--text-muted) !important;
  }
  /* Browse files button inside uploader */
  [data-testid="stFileUploader"] button {
    background-color: var(--bg-main) !important;
    color: var(--text-primary) !important;
    -webkit-text-fill-color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
  }
  [data-testid="stFileUploader"] button:hover {
    border-color: var(--accent) !important;
    background-color: var(--bg-input) !important;
  }
  [data-testid="stFileUploader"] button span {
    color: var(--text-primary) !important;
    -webkit-text-fill-color: var(--text-primary) !important;
  }

  /* ── Warning / info / error text ── */
  [data-testid="stAlert"] * { color: inherit !important; }

  /* ── Expander ── */
  .streamlit-expanderHeader,
  .streamlit-expanderHeader * {
    color: var(--text-primary) !important;
    background-color: var(--bg-input) !important;
  }

  /* ── Spinner text ── */
  .stSpinner > div { color: var(--text-primary) !important; }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: var(--bg-main); }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

  hr { border-color: var(--border) !important; margin: 0.5rem 0 !important; }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .welcome-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 60vh;
    text-align: center;
    gap: 1rem;
    animation: fadeIn 0.5s ease;
  }
</style>
""", unsafe_allow_html=True)

# ---- Session State ----
for k, v in {
    "user_id": "default_user",
    "current_chat_id": None,
    "current_chat_name": None,
    "conversations": [],
    "show_new_chat": False,
    "user_initialized": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ---- API Helpers ----
def ensure_user():
    if st.session_state.user_initialized:
        return
    try:
        r = requests.get(f"{API_URL}/user/by-username/default_user", timeout=5)
        if r.status_code == 200:
            uid = r.json().get("user", {}).get("id", "default_user")
        else:
            r2 = requests.post(
                f"{API_URL}/user/create",
                json={"username": "default_user", "email": None},
                timeout=5,
            )
            uid = (
                r2.json().get("user", {}).get("id", "default_user")
                if r2.status_code == 200
                else "default_user"
            )
        st.session_state.user_id = uid
        st.session_state.user_initialized = True
    except Exception:
        pass


def fetch_chats():
    try:
        r = requests.get(
            f"{API_URL}/user/{st.session_state.user_id}/chats", timeout=5
        )
        return r.json().get("chats", []) if r.status_code == 200 else []
    except Exception:
        return []


def load_chat(chat_id):
    try:
        r = requests.get(f"{API_URL}/chat/{chat_id}", timeout=5)
        st.session_state.conversations = (
            r.json().get("conversations", []) if r.status_code == 200 else []
        )
    except Exception:
        st.session_state.conversations = []


def delete_chat(chat_id):
    try:
        r = requests.delete(f"{API_URL}/chat/{chat_id}", timeout=5)
        if r.status_code == 200:
            if st.session_state.current_chat_id == chat_id:
                st.session_state.current_chat_id = None
                st.session_state.current_chat_name = None
                st.session_state.conversations = []
    except Exception:
        pass


def create_chat(name, pdf_file):
    try:
        files = {"file": (pdf_file.name, pdf_file.getvalue(), "application/pdf")}
        up = requests.post(f"{API_URL}/upload", files=files, timeout=120)
        if up.status_code != 200:
            st.sidebar.error(f"Upload failed: {up.json().get('error', up.text)}")
            return
        cr = requests.post(
            f"{API_URL}/chat/create",
            json={
                "user_id": st.session_state.user_id,
                "name": name,
                "pdf_filename": pdf_file.name,
            },
            timeout=10,
        )
        if cr.status_code == 200:
            d = cr.json()["chat"]
            st.session_state.current_chat_id = d["id"]
            st.session_state.current_chat_name = d["name"]
            st.session_state.conversations = []
            st.session_state.show_new_chat = False
            st.rerun()
        else:
            st.sidebar.error(f"Error: {cr.json().get('error', cr.text)}")
    except Exception as e:
        st.sidebar.error(f"Connection error: {e}")


# ---- Init ----
ensure_user()


# ---- Sidebar ----
with st.sidebar:
    st.markdown(
        "<div style='padding:0.5rem 0 1rem 0'>"
        "<span style='font-size:1.35rem;font-weight:700'>💬 PDF Chat</span><br>"
        "<span style='font-size:0.75rem;color:#8e8ea0'>RAG-powered document assistant</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    if st.button("+ New Chat", use_container_width=True, type="primary"):
        st.session_state.show_new_chat = not st.session_state.show_new_chat
        st.rerun()

    if st.session_state.show_new_chat:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Create New Chat**")
        chat_name = st.text_input(
            "Name",
            placeholder="e.g. Research Paper",
            key="nc_name",
            label_visibility="collapsed",
        )
        pdf_file = st.file_uploader(
            "PDF", type=["pdf"], key="nc_pdf", label_visibility="collapsed"
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Create", type="primary", use_container_width=True):
                if chat_name and pdf_file:
                    with st.spinner("Uploading..."):
                        create_chat(chat_name, pdf_file)
                else:
                    st.warning("Need name + PDF.")
        with c2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_new_chat = False
                st.rerun()

    st.markdown("---")
    st.markdown(
        "<span style='font-size:0.72rem;color:#8e8ea0;text-transform:uppercase;letter-spacing:.05em'>Your Chats</span>",
        unsafe_allow_html=True,
    )

    chats = fetch_chats()
    if chats:
        for chat in chats:
            is_active = chat["id"] == st.session_state.current_chat_id
            ca, cb = st.columns([5, 1])
            with ca:
                label = (">> " if is_active else "   ") + chat["name"]
                if st.button(label, key=f"open_{chat['id']}", use_container_width=True):
                    st.session_state.current_chat_id = chat["id"]
                    st.session_state.current_chat_name = chat["name"]
                    load_chat(chat["id"])
                    st.rerun()
            with cb:
                if st.button("🗑", key=f"del_{chat['id']}"):
                    delete_chat(chat["id"])
                    st.rerun()
    else:
        st.markdown(
            "<p style='color:#8e8ea0;font-size:.85rem;font-style:italic'>No chats yet.</p>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(
        "<p style='color:#8e8ea0;font-size:.72rem;text-align:center'>Powered by AI • RAG System</p>",
        unsafe_allow_html=True,
    )


# ---- Main Chat Area ----
if not st.session_state.current_chat_id:
    st.markdown(
        """
        <div class="welcome-wrap">
          <div style="font-size:4rem">💬</div>
          <div style="font-size:2rem;font-weight:700">How can I help you today?</div>
          <div style="color:#8e8ea0;max-width:480px">
            Select a chat from the sidebar, or click <b>+ New Chat</b> to upload a PDF
            and start a conversation.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:.75rem;padding:.25rem 0 .75rem;
                       border-bottom:1px solid #3a3a3a;margin-bottom:1rem">
          <span style="font-size:1.25rem">📄</span>
          <span style="font-weight:600;font-size:1.1rem">{st.session_state.current_chat_name}</span>
        </div>""",
        unsafe_allow_html=True,
    )

    # Render chat history
    for conv in st.session_state.conversations:
        with st.chat_message("user", avatar="👤"):
            st.markdown(conv["question"])
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(conv["answer"])
            if conv.get("sources"):
                with st.expander("📚 Sources"):
                    for s in conv["sources"]:
                        st.markdown(
                            f"- **{s.get('document', 'Unknown')}** - Page {s.get('page', 'N/A')}"
                        )

    # Chat input
    question = st.chat_input("Message your PDF...")
    if question:
        with st.chat_message("user", avatar="👤"):
            st.markdown(question)

        with st.chat_message("assistant", avatar="🤖"):
            placeholder = st.empty()
            full_answer = ""
            sources = []

            try:
                resp = requests.post(
                    f"{API_URL}/conversation/ask/stream",
                    json={
                        "chat_id": st.session_state.current_chat_id,
                        "question": question,
                        "top_k": 5,
                    },
                    stream=True,
                    timeout=120,
                )

                if resp.status_code == 200:
                    for line in resp.iter_lines():
                        if line:
                            line = line.decode("utf-8")
                            if line.startswith("data:"):
                                try:
                                    d = json.loads(line[5:].strip())
                                    if d["type"] == "sources":
                                        sources = d["data"]
                                    elif d["type"] == "chunk":
                                        full_answer += d["data"]
                                        placeholder.markdown(full_answer + " ▮")
                                    elif d["type"] == "done":
                                        placeholder.markdown(full_answer)
                                        st.session_state.conversations.append(
                                            {
                                                "id": d.get("conversation_id"),
                                                "question": question,
                                                "answer": full_answer,
                                                "sources": sources,
                                            }
                                        )
                                        if sources:
                                            with st.expander("📚 Sources"):
                                                for s in sources:
                                                    st.markdown(
                                                        f"- **{s.get('document', 'Unknown')}** - Page {s.get('page', 'N/A')}"
                                                    )
                                        break
                                except json.JSONDecodeError:
                                    continue
                else:
                    st.error(f"Error {resp.status_code}: {resp.text}")

            except requests.exceptions.ConnectionError:
                st.error(
                    f"Cannot reach API at {API_URL}. Make sure the backend is running."
                )
            except Exception as e:
                st.error(f"Error: {e}")
