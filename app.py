"""IMF monthly real and nominal exchange-rate explorer (Python 3.12)."""
from io import StringIO
from datetime import date

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pycountry
import requests
import streamlit as st

BASE = "https://api.imf.org/external/sdmx/3.0"
EARLIEST = pd.Period("1976-01", freq="M")
COUNTRIES = {f"{c.name} ({c.alpha_3})": c.alpha_3 for c in pycountry.countries}
COUNTRIES["Euro area (G163)"] = "G163"
COUNTRIES = dict(sorted(COUNTRIES.items()))
LABEL_BY_CODE = {code: label for label, code in COUNTRIES.items()}

st.set_page_config(page_title="IMF Real Exchange Rate", layout="wide")
st.title("IMF Real Exchange Rate Explorer")
st.caption("Monthly IMF CPI and exchange rates · available data from January 1976 onward")

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_series(flow: str, key: str) -> pd.Series:
    """Fetch IMF SDMX CSV and convert into a monthly numeric Series."""
    url = f"{BASE}/data/dataflow/IMF.STA/{flow}/+/{key}"
    try:
        response = requests.get(
            url,
            params={"startPeriod": "1976-01", "format": "csvfile"},
            headers={"Accept": "text/csv, application/vnd.sdmx.data+csv;version=2.0, */*"},
            timeout=45,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"IMF request failed for {flow} / {key}: {exc}") from exc
    if not response.content or not response.text.strip():
        raise RuntimeError(f"IMF returned no observations for {flow} / {key}.")
    try:
        data = pd.read_csv(StringIO(response.text), low_memory=False)
    except Exception as exc:
        raise RuntimeError(f"IMF returned an unreadable CSV for {flow} / {key}.") from exc
    data.columns = data.columns.str.strip().str.upper()
    if "TIME_PERIOD" not in data or "OBS_VALUE" not in data:
        raise RuntimeError(f"Unexpected IMF response columns for {flow}: {list(data.columns)}")
    period = pd.to_datetime(data["TIME_PERIOD"].astype(str).str[:7] + "-01", errors="coerce")
    values = pd.to_numeric(data["OBS_VALUE"], errors="coerce")
    series = pd.Series(values.to_numpy(), index=period, dtype=float)
    series = series[series.index.notna()].groupby(level=0).last().sort_index()
    series = series[series.index >= EARLIEST.to_timestamp()]
    if series.dropna().empty:
        raise RuntimeError(f"No usable monthly observations for {flow} / {key}.")
    return series

@st.cache_data(ttl=3600, show_spinner=False)
def country_data(code: str) -> pd.DataFrame:
    cpi = fetch_series("CPI", f"{code}.CPI._T.IX.M").rename("cpi")
    fx = fetch_series("ER", f"{code}.XDC_USD.PA_RT.M").rename("fx_per_usd")
    return pd.concat([cpi, fx], axis=1)

names = list(COUNTRIES)
def default_code(code, backup=0):
    return names.index(LABEL_BY_CODE[code]) if code in LABEL_BY_CODE else backup

left, right = st.columns(2)
with left:
    name1 = st.selectbox("Country 1 (base currency)", names, index=default_code("USA"))
with right:
    name2 = st.selectbox("Country 2 (quote currency)", names, index=default_code("CAN", 1))
code1, code2 = COUNTRIES[name1], COUNTRIES[name2]

if code1 == code2:
    st.info("Select two different countries or currency areas.")
    st.stop()

try:
    with st.spinner("Retrieving monthly IMF observations …"):
        d1, d2 = country_data(code1), country_data(code2)
except RuntimeError as exc:
    st.error(str(exc))
    st.info("Some IMF country/series combinations are unavailable; try another pair. IMF may also revise its API or dataflow IDs.")
    st.stop()

frame = pd.DataFrame(index=d1.index.union(d2.index).sort_values())
frame["CPI_1"] = d1["cpi"]
frame["CPI_2"] = d2["cpi"]
frame["FX_1_per_USD"] = d1["fx_per_usd"]
frame["FX_2_per_USD"] = d2["fx_per_usd"]
# IMF quotes are local currency per USD. The ratio is currency 2 / currency 1.
frame["Nominal_S"] = frame["FX_2_per_USD"] / frame["FX_1_per_USD"]
frame["RER"] = frame["Nominal_S"] * frame["CPI_1"] / frame["CPI_2"]
for col in ["CPI_1", "CPI_2", "FX_1_per_USD", "FX_2_per_USD"]:
    frame.loc[frame[col] <= 0, col] = float("nan")
# Recalculate from validated inputs (avoid dividing by zero/non-positive levels).
frame["Nominal_S"] = frame["FX_2_per_USD"] / frame["FX_1_per_USD"]
frame["RER"] = frame["Nominal_S"] * frame["CPI_1"] / frame["CPI_2"]
valid = frame["RER"].notna() & (frame["RER"] > 0)
if not valid.any():
    st.warning("These countries have no overlapping, positive monthly CPI and exchange-rate observations.")
    st.stop()

lo, hi = frame.index[valid].min().date(), frame.index[valid].max().date()
start_default = max(lo, date(2000, 1, 1))
c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    start = st.date_input("Start month", value=start_default, min_value=lo, max_value=hi)
with c2:
    end = st.date_input("End month", value=hi, min_value=lo, max_value=hi)
with c3:
    view = st.radio("Chart", ["Real", "Nominal", "Both"], horizontal=True)

start_m, end_m = pd.Period(start, freq="M"), pd.Period(end, freq="M")
if start_m > end_m:
    st.error("Start month must not be after end month.")
    st.stop()
sample = frame.loc[(frame.index.to_period("M") >= start_m) & (frame.index.to_period("M") <= end_m)].copy()
complete = sample["RER"].notna() & (sample["RER"] > 0)
if not complete.any():
    st.warning("No valid overlapping observations within the selected dates.")
    st.stop()
rer_star = sample.loc[complete, "RER"].mean()
sample["RER_star"] = rer_star
sample["Real_Index"] = 100 * sample["RER"] / rer_star
sample.index.name = "Month"

m1, m2, m3 = st.columns(3)
m1.metric("Sample mean RER (RER*)", f"{rer_star:.5g}")
m2.metric("Valid real observations", f"{complete.sum():,}")
m3.metric("Period", f"{start_m} to {end_m}")

fig = make_subplots(specs=[[{"secondary_y": True}]])
if view in ("Real", "Both"):
    fig.add_trace(go.Scatter(x=sample.index, y=sample["Real_Index"], name="Real index (mean = 100)", mode="lines"), secondary_y=False)
    fig.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.5)
if view in ("Nominal", "Both"):
    fig.add_trace(go.Scatter(x=sample.index, y=sample["Nominal_S"], name=f"Nominal S ({code2} / {code1})", mode="lines"), secondary_y=(view == "Both"))
fig.update_yaxes(title_text="Real exchange rate index (sample mean = 100)" if view != "Nominal" else f"Nominal S ({code2} per {code1})", secondary_y=False)
if view == "Both":
    fig.update_yaxes(title_text=f"Nominal S ({code2} per {code1})", secondary_y=True)
fig.update_layout(height=520, xaxis_title="Month", legend=dict(orientation="h", y=1.12), hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

st.markdown("**Definitions:** IMF FX rates are local currency units per USD. "
            "S = FX₂/USD ÷ FX₁/USD, so it measures Country 2 currency per Country 1 currency. "
            "RER = S × CPI₁ / CPI₂. RER* is the arithmetic mean of valid RER observations **within the selected sample**. "
            "Real Index = 100 × RER / RER*. The nominal series is never indexed or normalized.")
st.caption("Missing months remain missing. CPI series may use different reference bases and coverage may differ; the sample mean rebases the real index for comparison, not for absolute PPP estimation.")
with st.expander("View observations and calculations"):
    st.dataframe(sample, use_container_width=True)
st.download_button("Download selected-period CSV", sample.to_csv(float_format="%.10g").encode("utf-8"),
                   file_name=f"imf_rer_{code1}_{code2}_{start_m}_{end_m}.csv", mime="text/csv")
