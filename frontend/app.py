"""
frontend/app.py
---------------
Streamlit frontend for the Voice AI Chatbot.

Pages / flow:
1. Login / Register screen  → shown when user is not authenticated
2. Main chat screen         → shown after successful login
   - Sidebar: file uploader + session controls
   - Main area: chat messages + text/voice input

Auth is handled via JWT stored in st.session_state.
All API requests include the token in the Authorization header.
"""

import streamlit as st
import requests
import time
import base64

API = "http://localhost:8000"

st.set_page_config(
    page_title="Voice AI Chat-Bot",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header { font-size: 3rem; font-weight: 800; background: linear-gradient(135deg, #1e90ff, #ff4757); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0rem; }
    .sub-header { color: #8a8d9a; font-size: 1.1rem; margin-bottom: 2rem; }
    .status-badge { display: inline-flex; align-items: center; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; background: rgba(46, 213, 115, 0.15); color: #2ed573; border: 1px solid rgba(46, 213, 115, 0.3); margin-bottom: 1.5rem; box-shadow: 0 0 10px rgba(46, 213, 115, 0.05); }
    .status-dot { width: 8px; height: 8px; background-color: #2ed573; border-radius: 50%; margin-right: 10px; box-shadow: 0 0 8px #2ed573; animation: pulse-glow 2s infinite; }
    @keyframes pulse-glow { 0% { transform: scale(0.9); opacity: 0.5; } 50% { transform: scale(1.2); opacity: 1; box-shadow: 0 0 12px #2ed573; } 100% { transform: scale(0.9); opacity: 0.5; } }
    .sidebar-card { padding: 15px; border-radius: 10px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ──────────────────────────────────────────────────────────────────

def auth_headers():
    """Return Authorization header dict for API calls."""
    return {"Authorization": f"Bearer {st.session_state.get('token', '')}"}


def init_session():
    """Initialize all session state keys once."""
    for key, val in [("token", None), ("username", None), ("messages", [])]:
        if key not in st.session_state:
            st.session_state[key] = val


init_session()

# ── Auth Screen ───────────────────────────────────────────────────────────────

def show_auth_screen():
    st.markdown('<div class="main-header">Voice Chat-Bot</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Please log in to continue</div>', unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["🔑 Login", "📝 Register"])

    with tab_login:
        username = st.text_input("Username", key="login_user")
        
        use_face = st.checkbox("Login with Face ID / Camera", value=False, key="check_use_face")
        
        if use_face:
            st.info("Position your face in the camera stream to verify your identity.")
            face_file = st.camera_input("Snap to Login", key="login_camera")
            if face_file:
                if st.button("Authenticate Face", use_container_width=True):
                    with st.spinner("Verifying face profile..."):
                        try:
                            res = requests.post(
                                f"{API}/auth/login-face",
                                data={"username": username},
                                files={"file": (f"{username}.jpg", face_file.read(), "image/jpeg")}
                            )
                            if res.status_code == 200:
                                data = res.json()
                                st.session_state.token = data["access_token"]
                                st.session_state.username = username
                                st.success("Identity verified! Logging in...")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(res.json().get("detail", "Face authentication failed."))
                        except Exception as e:
                            st.error(f"Error connecting to face auth engine: {e}")
        else:
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login", use_container_width=True, key="btn_login"):
                res = requests.post(f"{API}/auth/login", json={"username": username, "password": password})
                if res.status_code == 200:
                    data = res.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error(res.json().get("detail", "Login failed"))

    with tab_register:
        new_user = st.text_input("Choose a username", key="reg_user")
        new_pass = st.text_input("Choose a password", type="password", key="reg_pass")

        if st.button("Create Account", use_container_width=True, key="btn_register"):
            res = requests.post(f"{API}/auth/register", json={"username": new_user, "password": new_pass})
            if res.status_code == 200:
                st.success("Account created successfully!")
            else:
                st.error(res.json().get("detail", "Registration failed"))

        st.markdown("---")
        st.markdown("### 📸 Optional: Register Face ID")
        st.caption("Enter your username above, take a snapshot, and click register.")
        reg_face_file = st.camera_input("Register Face Profile", key="register_camera")
        if reg_face_file:
            if st.button("Link Face ID to Account", use_container_width=True):
                with st.spinner("Processing face embedding..."):
                    try:
                        res = requests.post(
                            f"{API}/auth/register-face",
                            data={"username": new_user},
                            files={"file": (f"{new_user}.jpg", reg_face_file.read(), "image/jpeg")}
                        )
                        if res.status_code == 200:
                            st.success("Face ID successfully linked to your account! You can now log in using your camera.")
                        else:
                            st.error(res.json().get("detail", "Face registration failed. Please try again."))
                    except Exception as e:
                        st.error(f"Error registering Face ID: {e}")


# ── Main Chat Screen ──────────────────────────────────────────────────────────

def show_chat_screen():
    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"## 👋 Hello, **{st.session_state.username}**")
        st.markdown("---")

        # Text-to-Speech toggle
        st.markdown("### 🔊 Text-to-Speech")
        enable_audio = st.toggle("Read Answers Aloud", value=False)

        st.markdown("---")

        # File uploader
        st.markdown("### 📎 Upload a File")
        st.caption("PDF, DOCX, or TXT — the bot will answer questions about it.")
        uploaded_file = st.file_uploader("", type=["pdf", "docx", "txt"], label_visibility="collapsed")

        if uploaded_file:
            if st.button("Index File into Chatbot", use_container_width=True):
                with st.spinner("Uploading & indexing..."):
                    res = requests.post(
                        f"{API}/upload",
                        files={"file": (uploaded_file.name, uploaded_file.read(), uploaded_file.type)},
                        headers=auth_headers()
                    )
                if res.status_code == 200:
                    data = res.json()
                    st.success(f"✅ {data['message']} ({data['chunks_indexed']} chunks indexed)")
                else:
                    st.error(res.json().get("detail", "Upload failed"))

        st.markdown("---")

        # DB + AI status
        st.markdown("### 🗄️ Database Status")
        st.markdown('<div class="status-badge"><span class="status-dot"></span>MongoDB Atlas Connected</div>', unsafe_allow_html=True)
        st.markdown("### 🧠 AI Engine")
        st.markdown("""
        <div class="sidebar-card">
            <strong>Model:</strong> <code style='color:#1e90ff'>gpt-4o-mini</code><br>
            <strong>Pipeline:</strong> Whisper + Kokoro ONNX
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Clear chat
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            try:
                requests.delete(f"{API}/clear", headers=auth_headers())
            except Exception as e:
                st.sidebar.error(f"Failed to clear database: {e}")
            st.session_state.messages = []
            st.rerun()

        # Logout
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.username = None
            st.session_state.messages = []
            st.rerun()

    # ── Main Chat Area ────────────────────────────────────────────────────────
    st.markdown('<div class="main-header">Voice Chat-Bot</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Intelligent Assistant equipped with a Hybrid Speech Engine</div>', unsafe_allow_html=True)

    # Voice input
    voice_file = st.audio_input("🗣️ Record your voice query")
    if voice_file:
        if "last_processed_audio" not in st.session_state or st.session_state.last_processed_audio != voice_file:
            st.session_state.last_processed_audio = voice_file
            try:
                files = {"file": ("voice.wav", voice_file.read(), "audio/wav")}
                with st.spinner("Processing speech transcription & generating response..."):
                    res = requests.post(f"{API}/chat-audio", files=files, headers=auth_headers())
                if res.status_code == 200:
                    data = res.json()
                    if "error" not in data:
                        st.session_state.messages.append({"role": "user", "content": data["user_text"]})
                        msg_obj = {"role": "assistant", "content": data["bot_text"]}
                        if data.get("bot_audio"):
                            msg_obj["audio"] = data["bot_audio"]
                        st.session_state.messages.append(msg_obj)
                    else:
                        st.sidebar.error(data["error"])
                else:
                    st.sidebar.error(f"Error {res.status_code}: {res.text}")
            except Exception as e:
                st.sidebar.error(f"Voice pipeline error: {e}")

    # Display messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])
            if "audio" in msg and msg["audio"]:
                st.audio(base64.b64decode(msg["audio"]), format="audio/wav")

    # Text input
    prompt = st.chat_input("Or type your message here instead...")
    if prompt:
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant", avatar="🤖"):
            placeholder = st.empty()
            with st.spinner("Thinking..."):
                try:
                    res = requests.post(
                        f"{API}/chat",
                        json={"message": prompt, "generate_audio": enable_audio},
                        headers=auth_headers()
                    )
                    reply_data = res.json() if res.status_code == 200 else {}
                    reply = reply_data.get("response", f"Error {res.status_code}: {res.text}")
                except requests.exceptions.ConnectionError:
                    reply = "Could not connect to the backend. Is the FastAPI server running?"
                except Exception as e:
                    reply = f"An unexpected error occurred: {e}"

            streamed_text = ""
            for word in reply.split():
                streamed_text += word + " "
                placeholder.markdown(streamed_text + "▌")
                time.sleep(0.04)
            placeholder.markdown(streamed_text.strip())

            msg_obj = {"role": "assistant", "content": reply}
            if reply_data.get("bot_audio"):
                msg_obj["audio"] = reply_data["bot_audio"]
                st.audio(base64.b64decode(msg_obj["audio"]), format="audio/wav")
            st.session_state.messages.append(msg_obj)


# ── Entry Point ───────────────────────────────────────────────────────────────

if st.session_state.token:
    show_chat_screen()
else:
    show_auth_screen()