# IMF Real Exchange Rate Explorer

Streamlit app for monthly IMF CPI and foreign-exchange observations from January 1976, where available. Select Country 1 and Country 2 (including the euro area, IMF code `G163`), date range, and Real / Nominal / Both, then download a CSV of the selected months and calculations.

## Economics

- IMF `XDC_USD` data are **local-currency units per USD**.
- The required nominal rate, **Country 2 currency per Country 1 currency**, is `S = (FX_2 per USD) / (FX_1 per USD)`.
- `RER = S * CPI_1 / CPI_2`.
- `RER_star` is the **arithmetic mean of available positive RERs inside the chosen dates**, recalculated when dates change.
- `Real_Index = 100 * RER / RER_star`. Nominal `S` remains in actual currency units, not normalized.
- The combined chart uses a second y-axis for nominal `S`. CSV includes input observations, rates, RER, sample mean, and indexed RER.

## Files and requirements

- `app.py`: Streamlit application
- `requirements.txt`: Python 3.12 dependencies
- `README.md`: documentation

## Deploy without local Python

1. Create a **public** GitHub repository named `real-exchange-rate-app`, with a README.
2. Upload `app.py` and `requirements.txt`; replace the starter README with this file.
3. Open [Streamlit Community Cloud](https://share.streamlit.io/), sign in using GitHub, choose **Create app**, select the repository and `main` branch, and set entry point `app.py`.
4. Under Advanced settings choose Python **3.12** when offered, then deploy. Copy the resulting URL into your assignment submission.
5. Test at least USA/CAN and USA/G163, several sample windows, each chart view, and the CSV export.

## IMF API

Uses the official [IMF SDMX 3.0 API](https://api.imf.org/external/sdmx/3.0) with dataset keys:

- CPI: `{ISO3}.CPI._T.IX.M` (dataflow `IMF.STA/CPI`)
- FX: `{ISO3}.XDC_USD.PA_RT.M` (dataflow `IMF.STA/ER`)

The app requests SDMX CSV, caches queries for one hour, reports missing/unavailable data, and does not fill gaps. IMF may change dataflows, schemas, download formats or coverage. **The live IMF connection has not been validated in this deliverable**; verify that the dataflow identifiers and CSV response are accepted in the deployed environment before submitting.

## Validation examples

- If Country 1 USD and Country 2 CAD, `S` should be CAD per USD: if FX_USA=1 and FX_CAN=1.35, then S=1.35.
- If Country 1 CAD and Country 2 USD, `S` should be USD per CAD: 1/1.35 ≈ 0.74074.
- In any selected sample with valid RER observations, the arithmetic average of Real_Index across those observations should equal 100 (subject to rounding).
- Changing only the selected date range should change `RER_star` and indexed values, but **not** S for a given month.

## Limitations

- Not all ISO3 territories/countries have IMF data. `pycountry` supplies selection labels, not a guaranteed IMF-availability list.
- IMF CPI coverage and base years vary; this app is a descriptive normalized comparison, not an estimate of fundamental currency misvaluation.
- Missing/invalid values are retained as blank CSV cells; sample normalization uses only positive, nonmissing RER values.
