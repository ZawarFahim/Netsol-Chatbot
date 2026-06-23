import streamlit as st
import requests
import time
import base64

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

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown("## ⚙️ Control Center")
    st.markdown("---")
    
    st.markdown("### 🔊 Text-to-Speech")
    enable_audio = st.toggle("Read Answers Aloud", value=False)
    
    st.markdown("---")
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
    if st.button(" Clear Chat History", use_container_width=True):
        try:
            requests.delete("http://localhost:8000/clear")
        except Exception as e:
            st.sidebar.error(f"Failed to clear database: {e}")
        st.session_state.messages = []
        st.rerun()

st.markdown('<div class="main-header">Voice Chat-Bot</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Intelligent Assistant equipped with a Hybrid Speech Engine</div>', unsafe_allow_html=True)

# Handle Audio Upload
voice_file = st.audio_input("🗣️ Record your voice query")
if voice_file:
    if "last_processed_audio" not in st.session_state or st.session_state.last_processed_audio != voice_file:
        st.session_state.last_processed_audio = voice_file
        
        try:
            files = {"file": ("voice.wav", voice_file.read(), "audio/wav")}
            with st.spinner("Processing speech transcription & generating response..."):
                res = requests.post("http://localhost:8000/chat-audio", files=files)
                
                if res.status_code == 200:
                    data = res.json()
                    if "error" not in data:
                        st.session_state.messages.append({"role": "user", "content": data["user_text"]})
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": data["bot_text"],
                            "audio": data["bot_audio"]
                        })
                        # Removed st.rerun() to prevent the frontend widget from crashing
                    else:
                        st.sidebar.error(data["error"])
                else:
                    st.sidebar.error(f"Error {res.status_code}: {res.text}")
        except Exception as e:
            st.sidebar.error(f"Voice pipeline error: {e}")



for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])
        if "audio" in msg:
            audio_bytes = base64.b64decode(msg["audio"])
            st.audio(audio_bytes, format="audio/wav")

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
                    "http://localhost:8000/chat",
                    json={"message": prompt, "generate_audio": enable_audio}
                )
                
                reply_data = {}
                if res.status_code == 200:
                    reply_data = res.json()
                    reply = reply_data.get("response", "")
                else:
                    reply = f"Error {res.status_code}: {res.text}"
                    
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
        if "bot_audio" in reply_data:
            msg_obj["audio"] = reply_data["bot_audio"]
            st.audio(base64.b64decode(msg_obj["audio"]), format="audio/wav")
            
        st.session_state.messages.append(msg_obj)