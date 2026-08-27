import os

import httpx
import pandas as pd
import plotly.express as px
import streamlit as st

API_URL = os.getenv("MARKET_INTEL_API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(
    page_title="LATAM Market Intelligence",
    page_icon="🌎",
    layout="wide",
)


@st.cache_data(ttl=300)
def api_get(path: str, params: dict[str, object] | None = None) -> object:
    response = httpx.get(f"{API_URL}{path}", params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def load_rankings(scenario: str) -> pd.DataFrame:
    payload = api_get("/v1/rankings", {"scenario": scenario})
    return pd.json_normalize(payload)


st.title("LATAM Market Intelligence")
st.caption(
    "Explainable market comparison using World Bank indicators. "
    "A portfolio decision-support model—not investment or expansion advice."
)

scenario = st.sidebar.selectbox(
    "Strategic scenario",
    options=["base", "growth", "resilience"],
    format_func=lambda value: value.title(),
)

try:
    rankings = load_rankings(scenario)
except (httpx.HTTPError, ValueError) as exc:
    st.error(f"The API is unavailable or has no rankings yet: {exc}")
    st.code(
        "market-intel pipeline --snapshot data/sample/world_bank_snapshot.json",
        language="bash",
    )
    st.stop()

if rankings.empty:
    st.warning("No rankings are available for this scenario.")
    st.stop()

top = rankings.iloc[0]
metric_columns = st.columns(4)
metric_columns[0].metric("Leading market", top["country_name"])
metric_columns[1].metric("Leading score", f"{top['overall_score']:.1f}/100")
metric_columns[2].metric("Reference year", int(top["reference_year"]))
metric_columns[3].metric("Data coverage", f"{top['coverage_ratio']:.0%}")

overview_tab, dimensions_tab, trends_tab, method_tab = st.tabs(
    ["Ranking", "Dimensions", "Country trends", "Methodology"]
)

with overview_tab:
    figure = px.bar(
        rankings.sort_values("overall_score"),
        x="overall_score",
        y="country_name",
        orientation="h",
        text="overall_score",
        range_x=[0, 100],
        labels={"overall_score": "Score", "country_name": "Market"},
        color="overall_score",
        color_continuous_scale="Tealgrn",
    )
    figure.update_layout(coloraxis_showscale=False, height=430)
    st.plotly_chart(figure, use_container_width=True)
    st.dataframe(
        rankings[
            ["rank", "country_name", "overall_score", "coverage_ratio", "reference_year"]
        ].rename(
            columns={
                "rank": "Rank",
                "country_name": "Market",
                "overall_score": "Score",
                "coverage_ratio": "Coverage",
                "reference_year": "Year",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

with dimensions_tab:
    dimension_rows: list[dict[str, object]] = []
    for row in rankings.to_dict(orient="records"):
        for key, value in row.items():
            if key.startswith("dimensions."):
                dimension_rows.append(
                    {
                        "Market": row["country_name"],
                        "Dimension": key.removeprefix("dimensions.").title(),
                        "Score": value,
                    }
                )
    dimensions = pd.DataFrame(dimension_rows)
    if not dimensions.empty:
        selected_markets = st.multiselect(
            "Compare markets",
            rankings["country_name"].tolist(),
            default=rankings["country_name"].head(3).tolist(),
        )
        filtered = dimensions[dimensions["Market"].isin(selected_markets)]
        figure = px.bar(
            filtered,
            x="Dimension",
            y="Score",
            color="Market",
            barmode="group",
            range_y=[0, 100],
        )
        st.plotly_chart(figure, use_container_width=True)

with trends_tab:
    country_options = dict(zip(rankings["country_name"], rankings["country_code"], strict=True))
    country_name = st.selectbox("Market", list(country_options))
    indicators = api_get("/v1/indicators")
    indicator_options = {item["name"]: item["code"] for item in indicators}
    indicator_name = st.selectbox("Indicator", list(indicator_options))
    history = api_get(
        f"/v1/countries/{country_options[country_name]}/history",
        {"indicator": indicator_options[indicator_name]},
    )
    history_frame = pd.DataFrame(history)
    if history_frame.empty:
        st.info("No observations are available for this selection.")
    else:
        history_frame = history_frame.sort_values("year")
        figure = px.line(
            history_frame,
            x="year",
            y="value",
            markers=True,
            labels={"year": "Year", "value": indicator_name},
        )
        st.plotly_chart(figure, use_container_width=True)
        st.caption(f"Source updated: {history_frame['source_updated_at'].iloc[-1]}")

with method_tab:
    methodology = api_get("/v1/methodology")
    st.subheader("Transparent methodology")
    st.write(methodology["normalization"])
    st.write(methodology["outlier_treatment"])
    st.write(methodology["missing_data"])
    st.json(methodology["scenarios"], expanded=False)
    st.warning(methodology["disclaimer"])

st.divider()
st.caption("Data source: World Bank World Development Indicators (CC BY 4.0).")
