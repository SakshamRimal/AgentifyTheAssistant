import streamlit as st
import requests
import os
import time

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="centered")
st.title("🤖 AI Assistant")
st.set_page_config(page_title="AI Assistant | Production", page_icon="🤖", layout="wide")

# Custom styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 8px;
    }
    .badge-closed { color: #28a745; font-weight: bold; }
    .badge-open { color: #dc3545; font-weight: bold; }
    .badge-half_open { color: #ffc107; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🤖 Production AI Assistant")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    st.header("⚙️ Settings & Parameters")
    mode = st.radio(
        "Response mode",
        ["Plain chat", "Chat with tools", "RAG (grounded + sources)"],
        index=2,
        "Response Mode",
        [
            "RAG (grounded + sources)",
            "Chat with tools",
            "Structured JSON",
            "Plain chat",
        ],
        index=0,
    )

    with st.expander("🎛️ Model Hyperparameters", expanded=True):
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.5, value=0.2, step=0.05)
        top_p = st.slider("Top-p (Nucleus Sampling)", min_value=0.1, max_value=1.0, value=1.0, step=0.05)
        max_tokens = st.slider("Max Generation Tokens", min_value=64, max_value=2048, value=800, step=64)

    st.divider()
    st.subheader("Backend status")
    st.subheader("📊 System Telemetry")
    try:
        health = requests.get(f"{BACKEND_URL}/health", timeout=3).json()
        st.success(f"Connected — provider: {health.get('provider', 'unknown')}")
        st.success(f"Backend Online ({health.get('provider', 'unknown')})")
        if health.get("fallback"):
            st.info(f"Fallback: {health['fallback']}")
            st.info(f"Fallback Ready: {health['fallback']}")

        cb_state = health.get("circuit_breaker", "closed")
        if cb_state == "open":
            st.warning(f"Circuit breaker: {cb_state}")
        if cb_state == "closed":
            st.markdown(f"Circuit Breaker: <span class='badge-closed'>● CLOSED (Healthy)</span>", unsafe_allow_html=True)
        elif cb_state == "half_open":
            st.markdown(f"Circuit Breaker: <span class='badge-half_open'>● HALF-OPEN (Testing)</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"Circuit Breaker: <span class='badge-open'>● OPEN (Tripped)</span>", unsafe_allow_html=True)

        cache_stats = health.get("cache", {})
        if cache_stats:
            st.caption(f"Cache hit rate: {cache_stats.get('hit_rate', 0):.0%} ({cache_stats.get('size', 0)} entries)")
            st.metric(
                label="Cache Hit Rate",
                value=f"{cache_stats.get('hit_rate', 0):.0%}",
                delta=f"{cache_stats.get('hits', 0)} hits / {cache_stats.get('size', 0)} items",
            )
    except requests.exceptions.RequestException:
        st.error("Backend unreachable")
        st.error("Backend Unreachable")

    st.divider()
    st.subheader("📚 Knowledge Base")
    try:
        doc_info = requests.get(f"{BACKEND_URL}/rag/documents", timeout=3).json()
        total_chunks = doc_info.get("total_chunks", 0)
        docs = doc_info.get("documents", [])
        st.caption(f"Indexed Chunks: {total_chunks}")
        if docs:
            with st.expander(f"Documents ({len(docs)})", expanded=False):
                for d in docs:
                    st.caption(f"• {d['filename']} ({d['chunks']} chunks)")
    except Exception:
        pass

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Re-ingest documents"):
        if st.button("🔄 Re-ingest", use_container_width=True):
            with st.spinner("Ingesting..."):
                try:
                    resp = requests.post(f"{BACKEND_URL}/ingest", timeout=5)
                    if resp.ok:
                        st.success("Started in background")
                        st.success("Ingestion started")
                    else:
                        st.error(f"Failed: {resp.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Request failed: {e}")
                    st.error(f"Error: {e}")
    with col2:
        if st.button("Clear cache"):
        if st.button("🧹 Clear Cache", use_container_width=True):
            try:
                resp = requests.post(f"{BACKEND_URL}/cache/invalidate", timeout=5)
                if resp.ok:
                    st.success("Cache cleared")
                    st.success("Cleared")
                    time.sleep(0.5)
                    st.rerun()
            except requests.exceptions.RequestException:
                st.error("Failed")

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Session state ────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Render existing conversation ─────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("tool_calls_made"):
            st.info(f"🛠️ Tools Invoked: {', '.join(msg['tool_calls_made'])}")
        if msg.get("structured_data"):
            with st.expander("Structured Output (JSON)"):
                st.json(msg["structured_data"])
        if msg.get("sources"):
            with st.expander("Sources"):
            with st.expander(f"📄 Retrieved Sources ({len(msg['sources'])})"):
                for s in msg["sources"]:
                    st.caption(f"📄 {s['document']} (chunk: {s['chunk_id']})")
                    st.caption(f"• **{s['document']}** [chunk: `{s['chunk_id'][:8]}`]")
        if msg.get("confidence") is not None:
            st.caption(f"🎯 Model Confidence: {msg['confidence']:.0%}")
        if msg.get("response_time"):
            st.caption(f"⏱ {msg['response_time']}ms")
            st.caption(f"⏱️ {msg['response_time']}ms")
        if msg.get("error"):
            st.error(msg["error"])

# ── Chat input ───────────────────────────────────────────────────────────────
user_input = st.chat_input("Ask something...")
user_input = st.chat_input("Type your question or prompt here...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
        if m["role"] in ("user", "assistant")
    ]

    endpoint_map = {
        "Plain chat": "/chat",
        "Chat with tools": "/chat/tools",
        "Structured JSON": "/chat/structured",
        "RAG (grounded + sources)": "/chat/rag",
    }
    endpoint = endpoint_map[mode]

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
        with st.spinner("Processing request..."):
            start_time = time.time()
            try:
                payload = {
                    "message": user_input,
                    "history": history,
                    "temperature": temperature,
                    "top_p": top_p,
                    "max_tokens": max_tokens,
                }
                resp = requests.post(
                    f"{BACKEND_URL}{endpoint}",
                    json={"message": user_input, "history": history},
                    json=payload,
                    timeout=90,
                )
                elapsed_ms = round((time.time() - start_time) * 1000)

                if resp.status_code == 429:
                    retry_after = resp.json().get("retry_after", 30)
                    error_msg = f"Rate limited. Retry after {retry_after}s"
                    error_msg = f"Rate limited. Please retry after {retry_after}s"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant", "content": "(rate limited)",
                        "role": "assistant",
                        "content": "⚠️ *Request was rate-limited.*",
                        "error": error_msg,
                    })
                elif resp.status_code == 503:
                    error_msg = "LLM service temporarily unavailable. Try again shortly."
                    error_msg = "LLM service temporarily unavailable. Circuit breaker may be active."
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant", "content": "(unavailable)",
                        "role": "assistant",
                        "content": "⚠️ *Service temporarily unavailable.*",
                        "error": error_msg,
                    })
                else:
                    resp.raise_for_status()
                    data = resp.json()

                    answer = data.get("answer", "(no answer returned)")
                    sources = data.get("sources", [])
                    tools_used = data.get("tool_calls_made", [])
                    confidence = data.get("confidence")
                    structured = data.get("structured_data")

                    st.markdown(answer)

                    if tools_used:
                        st.info(f"🛠️ Tools Invoked: {', '.join(tools_used)}")
                    if structured:
                        with st.expander("Structured Output (JSON)"):
                            st.json(structured)
                    if sources:
                        with st.expander("Sources"):
                        with st.expander(f"📄 Retrieved Sources ({len(sources)})"):
                            for s in sources:
                                st.caption(f"📄 {s['document']} (chunk: {s['chunk_id']})")
                    st.caption(f"⏱ {elapsed_ms}ms")
                                st.caption(f"• **{s['document']}** [chunk: `{s['chunk_id'][:8]}`]")
                    if confidence is not None:
                        st.caption(f"🎯 Model Confidence: {confidence:.0%}")
                    st.caption(f"⏱️ {elapsed_ms}ms")

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "tool_calls_made": tools_used,
                        "confidence": confidence,
                        "structured_data": structured,
                        "response_time": elapsed_ms,
                    })

            except requests.exceptions.ConnectionError:
                error_msg = "Cannot connect to backend. Is it running?"
                error_msg = "Cannot connect to backend server. Ensure FastAPI is running on port 8000."
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant", "content": "(error)", "error": error_msg,
                    "role": "assistant", "content": "⚠️ *Connection error*", "error": error_msg,
                })
            except requests.exceptions.Timeout:
                error_msg = "Request timed out. The model may be slow or overloaded."
                error_msg = "Request timed out after 90 seconds. Backend may be experiencing heavy load."
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant", "content": "(timeout)", "error": error_msg,
                    "role": "assistant", "content": "⚠️ *Timeout*", "error": error_msg,
                })
            except requests.exceptions.RequestException as e:
                error_msg = f"Request failed: {e}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant", "content": "(error)", "error": error_msg,
                    "role": "assistant", "content": "⚠️ *Error processing request*", "error": error_msg,
                })

