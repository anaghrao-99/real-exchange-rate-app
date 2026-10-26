# LLM prompt and provenance

**Date:** 2026-10-25  
**Model:** OpenAI GPT-6 (ChatGPT)

## Prompt

Create a complete Streamlit web app with files `app.py`, `requirements.txt`, and `README.md`, compatible with Python 3.12 and deployable to Streamlit Community Cloud without local installation. Provide Country 1 and Country 2 selectors spanning IMF countries and the Euro area (G163). Retrieve monthly IMF CPI and exchange rates from January 1976 where available using IMF SDMX 3.0. CPI series key: `{ISO3}.CPI._T.IX.M`; FX key: `{ISO3}.XDC_USD.PA_RT.M`. IMF FX quotes are local currency units per USD. Convert to `S(t)` = Country 2 currency per Country 1 currency = FX2/FX1. Calculate `RER(t)=S(t)*P1(t)/P2(t)`; for selected start/end months, recompute `RER*=arithmetic mean of valid RER months` and `Real_Index(t)=100*RER(t)/RER*`. Chart Real, unnormalized Nominal S, or Both with two axes; provide CSV of all observations and calculations within selected dates. Handle missing data and API errors explicitly. Add deployment directions and validation examples. Do not fabricate IMF observations.

## Verification status

- Checked arithmetic and exchange-rate orientation by inspection.
- Python source compiled syntactically.
- Live IMF SDMX endpoint, GitHub publication, and Streamlit deployment **not verified** (no available authenticated publishing session; network request could not resolve IMF host in the execution environment).
