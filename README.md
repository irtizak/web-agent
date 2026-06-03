## Streamlit App

Run the web UI locally with:

```bash
streamlit run app.py
```

For deployment, set `OPENAI_API_KEY` and `BRIGHTDATA_API_KEY` in your host's secret manager or environment settings. Streamlit Community Cloud can use the top-level requirements file, and any host that can run `streamlit run app.py` should work.
