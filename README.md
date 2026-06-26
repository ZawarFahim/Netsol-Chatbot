---
title: Netsol Chatbot
emoji: 💬
colorFrom: green
colorTo: blue
sdk: docker
app_port: 8000
pinned: false
---

# IZS — AI Voice Chatbot & Document Search (RAG) with Face ID

An advanced, secure full-stack AI assistant featuring **voice interactions (STT/TTS)**, **Document Search (RAG)**, and biometric **Face ID authentication** (powered locally by OpenCV and ONNX).

---

## 🌟 Key Features

*   **Biometric Face ID Authentication**: Secure login and sign-up using computer vision (Haar Cascade face detection and SFace ONNX embedding generation).
*   **Conversational Voice Support**: Voice input transcription and instant local audio generation (using the ultra-fast Kokoro TTS engine).
*   **Document-based RAG**: Upload and search PDF, DOCX, and TXT files. The chatbot automatically indexes and retrieves information from these files to answer queries.
*   **Modern Premium UI/UX**: Dynamic design with fluid glassmorphism, responsive sidebar, auto-sizing text areas, theme toggles (dark/light), and audio player waveforms.
*   **Secure Architecture**: JWT-based session tokens, password hashing, and user-isolated chat threads/files.

---

## 🏗️ Clean Project Architecture

The codebase follows a modular clean architecture:

```text
├── backend/                  # Fast API application
│   ├── routes/               # API endpoint routers
│   │   ├── auth.py           # Login, Register, Face ID Authentication
│   │   ├── chat.py           # LLM conversation & Audio routes
│   │   └── upload.py         # Document upload and indexing
│   ├── services/             # Core business logic
│   │   ├── audio.py          # Whisper (STT) and Kokoro (TTS)
│   │   ├── auth.py           # JWT & password security
│   │   ├── face.py           # Face detection and SFace ONNX verifier
│   │   └── llm.py            # AI OpenRouter LLM pipeline
│   ├── rag/                  # Retrieval-Augmented Generation
│   │   ├── tools.py          # LLM function calling tools
│   │   └── vectorstore.py    # Vector store integrations
│   ├── weights/              # Machine learning weights (Kokoro, SFace)
│   ├── database.py           # MongoDB connection setup
│   ├── schemas.py            # Pydantic schemas
│   └── main.py               # FastAPI entrypoint and routes hook
├── frontend/                 # Static web files served by FastAPI
│   ├── index.html            # Main Chat Application Interface
│   └── loginpage.html        # Authentication & Face Capture Panel
├── tests/                    # Testing suite
├── download_models.py        # Model weights helper script
└── requirements.txt          # Python dependencies
```

---

## 🚀 Getting Started

### 1. Prerequisites
*   Python 3.10 or 3.11
*   MongoDB Atlas cluster (or a local MongoDB instance)
*   OpenRouter or OpenAI API Key (for LLM generation)

### 2. Installation

1.  Clone this repository:
    ```bash
    git clone <repository-url>
    cd Netsol-Chatbot
    ```

2.  Create and activate a virtual environment:
    ```bash
    python -m venv .venv
    # On Windows:
    .venv\Scripts\activate
    # On macOS/Linux:
    source .venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Configure environment variables. Create a `.env` file in the root directory:
    ```env
    MONGO_URI=mongodb+srv://...
    DB_NAME=voice_rag_ai
    OPENROUTER_API_KEY=your-openrouter-key-here
    JWT_SECRET=your-jwt-secret-key
    ```

5.  Download required AI model files (Whisper, SFace ONNX, Kokoro ONNX):
    ```bash
    python download_models.py
    ```

### 3. Running the Server

Start the FastAPI application with:
```bash
python -m uvicorn backend.main:app --reload
```

Once running, access the web interface at:
*   **Sign-in / Sign-up page**: [http://localhost:8000/loginpage.html](http://localhost:8000/loginpage.html)
*   **Main Chatbot Workspace**: [http://localhost:8000/app](http://localhost:8000/app)

---

## 🔒 Security & Privacy

*   **Biometric Data Security**: Raw camera photos are never stored. The face verifier instantly processes captured frames into normalized **128-dimensional embeddings** stored in MongoDB, and discards the image.
*   **Authentication Gates**: Access to documents, vector indices, and chat histories are strictly protected by JWT verification (`Depends(decode_token)`).
*   **Session Isolation**: Chat threads are securely isolated by both `user_id` and database sessions to prevent cross-account leakage.

---

## ☁️ Deployment & CI/CD Pipeline

The project is configured for fully automated deployment to **Hugging Face Spaces (Docker SDK)**.

### 1. Cloud Architecture & Settings
*   **Hosting**: Hugging Face Spaces (CPU Basic Free Tier — 16GB RAM, 2vCPU).
*   **Database**: MongoDB Atlas (Free Tier M0 cluster).
*   **Models**: Whisper, Kokoro TTS, and SFace ONNX models are baked directly into the Docker image during the build phase (`download_models.py`).

### 2. Environment Variables & Secrets Configuration

Configure the following secrets in your **Hugging Face Space Settings** under **Variables and Secrets**:
*   `MONGO_URI`: MongoDB connection string.
*   `DB_NAME`: Database name (e.g., `chatbot_user`).
*   `OPENROUTER_API_KEY`: OpenRouter API key for LLM and embeddings logic.
*   `JWT_SECRET`: Secure secret key for signing user sessions.
*   `LANGFUSE_PUBLIC_KEY` & `LANGFUSE_SECRET_KEY`: Tracing parameters.
*   `LANGFUSE_BASE_URL`: Defaults to `https://cloud.langfuse.com`.
*   `LOGFIRE_TOKEN`: Logging telemetry token.

*(Note: Ensure there are no surrounding double or single quotes when pasting secrets).*

### 3. CI/CD Workflows (GitHub Actions)

The repository includes two active pipelines under `.github/workflows/`:
1.  **CI Pipeline (`ci.yml`)**: Installs dependencies, runs code linters (`flake8`), and executes Python test suites (`pytest`) on every commit to `main`.
2.  **CD Pipeline (`cd.yml`)**: Triggers in parallel on every push to `main` and syncs the codebase directly to your Hugging Face Space using `git` and your `HF_TOKEN` secret.

To run the CD pipeline, add your Hugging Face Access Token to your **GitHub Repository Settings** under **Secrets and variables > Actions > New repository secret** as `HF_TOKEN`.