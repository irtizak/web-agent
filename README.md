[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/irtizak/web-agent)

# Multi-Source Research Agent

A lightweight research assistant that queries multiple sources (Google, Bing, Reddit) in parallel, analyzes results with an LLM, and synthesizes a single, combined answer.

Key features
- Parallel search across Google, Bing, and Reddit (via BrightData)
- Automated analysis per-source using configurable prompt templates
- Final synthesis step that combines insights into a single answer
- Streamlit-based web UI plus a simple CLI runner

Quick start

1. Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Set required environment variables (Streamlit Cloud or host secrets are recommended):

- `OPENAI_API_KEY` — API key for OpenAI-compatible models used by `langchain`/`langgraph`
- `BRIGHTDATA_API_KEY` — API key for BrightData (used to fetch SERP and Reddit snapshots)

3. Run the Streamlit web UI locally:

```bash
streamlit run app.py
```

4. Or run the CLI research agent:

```bash
python main.py
```

Important files
- [main.py](main.py): Orchestrates the research flow using `langgraph` StateGraph and defines nodes such as `google_search`, `reddit_search`, analysis steps, and `synthesize_analyses`.
- [app.py](app.py): Streamlit UI that runs the agent in a background thread and streams stdout/stderr to the page.
- [prompts.py](prompts.py): Centralized prompt templates and helper functions for creating message pairs used by the LLM.
- [web_operations.py](web_operations.py): Integration with BrightData APIs for SERP scraping and Reddit snapshot triggering/download.
- [snapshot_operations.py](snapshot_operations.py): Utility functions to poll and download BrightData snapshots.

How it works (high level)

1. User enters a query (CLI or Streamlit UI).
2. The StateGraph launches parallel searches (Google, Bing, Reddit).
3. Search results are analyzed individually using prompt templates and the LLM.
4. Selected Reddit URLs are retrieved (comments/posts) for deeper analysis.
5. Individual analyses are synthesized into a final answer.

Notes and cautions
- BrightData usage requires a valid account and may incur costs. The project uses a `dataset_id` and BrightData trigger endpoints — review `web_operations.py` before running against your account.
- The project initializes the chat model with `init_chat_model("gpt-4o")` in `main.py`. Change this to a model available to your account or configure `langchain` accordingly.
- The repository depends on `langchain`, `langgraph`, and `streamlit` — pinned ranges are listed in `pyproject.toml` and `requirements.txt`.

Development

- To extend prompts, edit `prompts.py` and add new template helpers.
- To add a new source, implement retrieval in `web_operations.py` and add nodes/edges in the graph in `main.py`.

Contact and source

Source repository: https://github.com/irtizak/web-agent

License: (not specified)
