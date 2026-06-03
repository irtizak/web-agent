from contextlib import redirect_stderr, redirect_stdout
import queue
import threading
import time
import traceback

import streamlit as st

from main import run_research_agent


class QueueWriter:
    def __init__(self, output_queue: queue.Queue[str], stream_name: str):
        self.output_queue = output_queue
        self.stream_name = stream_name

    def write(self, text: str) -> int:
        if text:
            self.output_queue.put((self.stream_name, text))
        return len(text)

    def flush(self) -> None:
        return None


def start_streaming_run(user_question: str):
    stdout_queue: queue.Queue[tuple[str, str]] = queue.Queue()
    stderr_queue: queue.Queue[tuple[str, str]] = queue.Queue()
    result_queue: queue.Queue[tuple[str, object]] = queue.Queue()

    def worker() -> None:
        stdout_writer = QueueWriter(stdout_queue, "stdout")
        stderr_writer = QueueWriter(stderr_queue, "stderr")

        try:
            with redirect_stdout(stdout_writer), redirect_stderr(stderr_writer):
                result = run_research_agent(user_question)

            result_queue.put(("result", result))
        except Exception:
            result_queue.put(("error", traceback.format_exc()))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread, stdout_queue, stderr_queue, result_queue


st.set_page_config(
    page_title="Research Agent",
    page_icon="search",
    layout="wide",
)


st.markdown(
    """
    <style>
        .stApp {
            background: radial-gradient(circle at top, #f3f7ff 0%, #eef2f7 38%, #f8fafc 100%);
        }
        .hero {
            padding: 2rem 2rem 1.25rem;
            border-radius: 1.5rem;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.92));
            color: white;
            box-shadow: 0 24px 60px rgba(15, 23, 42, 0.18);
            margin-bottom: 1.25rem;
        }
        .hero h1 {
            margin: 0;
            font-size: 2.5rem;
        }
        .hero p {
            margin: 0.65rem 0 0;
            color: rgba(255, 255, 255, 0.78);
            max-width: 52rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="hero">
        <h1>Multi-Source Research Agent</h1>
        <p>Ask a question and the agent searches Google, Bing, and Reddit, then synthesizes the results into a single answer.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.header("Deployment")
    st.write("Set these secrets in Streamlit Cloud or your hosting provider:")
    st.code("OPENAI_API_KEY\nBRIGHTDATA_API_KEY", language="text")
    st.caption("The app reads environment variables through python-dotenv and the hosting platform.")
    st.markdown("[View the source on GitHub](https://github.com/irtizak/web-agent)")


question = st.text_area(
    "What do you want the agent to research?",
    placeholder="Example: What are people saying about the latest OpenAI models?",
    height=140,
)


col1, col2 = st.columns([1, 3])
run_clicked = col1.button("Run research", type="primary", use_container_width=True)
clear_clicked = col2.button("Clear", use_container_width=True)


if clear_clicked:
    st.session_state.pop("last_result", None)
    st.session_state.pop("last_question", None)
    st.rerun()


if run_clicked:
    if not question.strip():
        st.warning("Enter a question before running the agent.")
    else:
        live_output = st.container(border=True)
        live_output.subheader("Live command line messages")
        live_stdout = live_output.empty()
        live_stderr = live_output.empty()
        live_status = live_output.empty()

        stdout_chunks: list[str] = []
        stderr_chunks: list[str] = []
        thread, stdout_queue, stderr_queue, result_queue = start_streaming_run(question.strip())

        live_status.info("Researching across sources...")

        while thread.is_alive() or not stdout_queue.empty() or not stderr_queue.empty():
            updated = False

            while True:
                try:
                    _, stdout_text = stdout_queue.get_nowait()
                    stdout_chunks.append(stdout_text)
                    updated = True
                except queue.Empty:
                    break

            while True:
                try:
                    _, stderr_text = stderr_queue.get_nowait()
                    stderr_chunks.append(stderr_text)
                    updated = True
                except queue.Empty:
                    break

            if updated:
                live_stdout.code("".join(stdout_chunks).strip() or "Waiting for stdout...", language="text")
                live_stderr.code("".join(stderr_chunks).strip() or "Waiting for stderr...", language="text")

            time.sleep(0.1)

        live_stdout.code("".join(stdout_chunks).strip() or "No stdout was captured.", language="text")
        live_stderr.code("".join(stderr_chunks).strip() or "No stderr was captured.", language="text")

        try:
            result_type, payload = result_queue.get_nowait()
        except queue.Empty:
            st.error("The agent finished without returning a result.")
        else:
            if result_type == "result":
                result = payload
                st.session_state["last_result"] = result
                st.session_state["last_question"] = question.strip()
                st.session_state["last_stdout"] = "".join(stdout_chunks)
                st.session_state["last_stderr"] = "".join(stderr_chunks)
                live_status.success("Research completed.")
            else:
                live_status.error("The agent failed to run.")
                st.session_state["last_stdout"] = "".join(stdout_chunks)
                st.session_state["last_stderr"] = "".join(stderr_chunks)
                st.error(str(payload))


if "last_result" in st.session_state:
    result = st.session_state["last_result"]
    st.subheader("Answer")
    st.write(result.get("final_answer", "No answer was produced."))

    with st.expander("Command line messages", expanded=False):
        stdout_text = st.session_state.get("last_stdout", "").strip()
        stderr_text = st.session_state.get("last_stderr", "").strip()

        if stdout_text:
            st.markdown("**stdout**")
            st.code(stdout_text, language="text")

        if stderr_text:
            st.markdown("**stderr**")
            st.code(stderr_text, language="text")

        if not stdout_text and not stderr_text:
            st.write("No command line output was captured for this run.")

    with st.expander("Raw outputs", expanded=False):
        st.markdown("**Google results**")
        st.write(result.get("google_results"))
        st.markdown("**Bing results**")
        st.write(result.get("bing_results"))
        st.markdown("**Reddit results**")
        st.write(result.get("reddit_results"))
        st.markdown("**Selected Reddit URLs**")
        st.write(result.get("selected_reddit_urls"))
        st.markdown("**Reddit post data**")
        st.write(result.get("reddit_post_data"))
        st.markdown("**Google analysis**")
        st.write(result.get("google_analysis"))
        st.markdown("**Bing analysis**")
        st.write(result.get("bing_analysis"))
        st.markdown("**Reddit analysis**")
        st.write(result.get("reddit_analysis"))
else:
    st.info("Run a query to see the synthesized answer and underlying research outputs.")