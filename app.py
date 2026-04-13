import json
import math
import pandas as pd
import numpy as np
from dash import Dash, dcc, html, Input, Output, dash_table
import plotly.graph_objects as go

# ── Load data ────────────────────────────────────────────────────────────────
with open("data.json") as f:
    raw = json.load(f)

df = pd.DataFrame(raw)

# Global medians (crosshair lines)
PM25_MED = df["pm25"].median()
EMI_MED  = df["emi"].median()

# Income group aggregates
INCOME_ORDER = [
    "Low-income countries",
    "Lower-middle-income countries",
    "Upper-middle-income countries",
    "High-income countries",
]

INCOME_SHORT = {
    "Low-income countries":              "Low income",
    "Lower-middle-income countries":     "Lower-middle",
    "Upper-middle-income countries":     "Upper-middle",
    "High-income countries":             "High income",
}

INCOME_COLORS = {
    "Low-income countries":              "#f39c12",   # orange  (matches notebook)
    "Lower-middle-income countries":     "#2ecc71",   # green
    "Upper-middle-income countries":     "#e74c3c",   # red/pink
    "High-income countries":             "#3498db",   # blue
}

REGIONS = sorted(df["region"].unique())

# Region radar data (from your notebook, population-weighted)
REGION_RADAR = {
    "Africa":       {"income": 0.239, "pm25_n": 0.708, "emi_n": 0.031, "pm25_raw": 33.84, "emi_raw": 0.103},
    "Asia":         {"income": 0.546, "pm25_n": 1.000, "emi_n": 0.245, "pm25_raw": 44.59, "emi_raw": 0.126},
    "Europe":       {"income": 0.887, "pm25_n": 0.156, "emi_n": 0.122, "pm25_raw": 13.52, "emi_raw": 0.113},
    "Latin America and the Caribbean": {"income": 0.652, "pm25_n": 0.258, "emi_n": 0.000, "pm25_raw": 17.27, "emi_raw": 0.100},
    "Northern America": {"income": 1.000, "pm25_n": 0.014, "emi_n": 1.000, "pm25_raw": 8.30,  "emi_raw": 0.207},
    "Oceania":      {"income": 0.552, "pm25_n": 0.000, "emi_n": 0.977, "pm25_raw": 7.77,  "emi_raw": 0.204},
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def bubble_size(pop, max_pop, min_r=6, max_r=50):
    return min_r + (max_r - min_r) * math.sqrt(pop / max_pop)


def make_scatter(sub_df, title, use_log_x=True):
    """Return a plotly Figure with bubble scatter."""
    fig = go.Figure()
    max_pop = df["pop"].max()

    for income in INCOME_ORDER:
        grp = sub_df[sub_df["income"] == income]
        if grp.empty:
            continue
        fig.add_trace(go.Scatter(
            x=grp["emi"],
            y=grp["pm25"],
            mode="markers",
            name=INCOME_SHORT[income],
            marker=dict(
                size=[bubble_size(p, max_pop) for p in grp["pop"]],
                color=INCOME_COLORS[income],
                opacity=0.7,
                line=dict(width=0.5, color="white"),
            ),
            text=grp["name"],
            customdata=grp[["income", "pop", "pm25", "emi"]].values,
            hovertemplate=(
                "<b>%{text}</b><br>"
                "PM2.5: %{y:.1f} μg/m³<br>"
                "Emissions: %{x:.4f} t/person<br>"
                "Population: %{customdata[1]:,.0f}<br>"
                "Income group: %{customdata[0]}<extra></extra>"
            ),
        ))

    # Median crosshairs
    fig.add_hline(y=PM25_MED, line_dash="dash", line_color="grey", line_width=1,
                  annotation_text=f"Median PM2.5: {PM25_MED:.1f}", annotation_position="top right",
                  annotation_font_size=10)
    fig.add_vline(x=EMI_MED, line_dash="dash", line_color="grey", line_width=1,
                  annotation_text=f"Median emi: {EMI_MED:.3f}", annotation_position="top right",
                  annotation_font_size=10)

    fig.update_layout(
        title=dict(text=title, font_size=15),
        xaxis=dict(
            title="Per capita emissions (tonnes/person)",
            type="log" if use_log_x else "linear",
            showgrid=True, gridcolor="#eeeeee",
        ),
        yaxis=dict(
            title="PM2.5 concentration (μg/m³)",
            showgrid=True, gridcolor="#eeeeee",
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(title="Income group", orientation="v"),
        margin=dict(l=60, r=20, t=60, b=60),
        height=500,
    )
    return fig


def make_income_aggregate():
    """4-point aggregate scatter by income group."""
    fig = go.Figure()

    # Population-weighted averages per group
    agg_rows = []
    for g, grp in df.groupby("income"):
        w = grp["pop"]
        agg_rows.append({
            "income": g,
            "pm25":   np.average(grp["pm25"], weights=w),
            "emi":    np.average(grp["emi"],  weights=w),
            "pop":    w.sum(),
            "n":      len(grp),
        })
    agg = pd.DataFrame(agg_rows)

    # Crosshair = median of the 4 group-level values (matches notebook)
    agg_pm25_med = agg["pm25"].median()
    agg_emi_med  = agg["emi"].median()

    # Bubble size scaled to group population
    max_pop = agg["pop"].max()

    for _, row in agg.iterrows():
        inc = row["income"]
        fig.add_trace(go.Scatter(
            x=[row["emi"]],
            y=[row["pm25"]],
            mode="markers+text",
            name=INCOME_SHORT[inc],
            marker=dict(
                size=bubble_size(row["pop"], max_pop, min_r=30, max_r=70),
                color=INCOME_COLORS[inc],
                opacity=0.75,
                line=dict(width=1, color="white"),
            ),
            text=[inc],
            textposition="top center",
            hovertemplate=(
                f"<b>{inc}</b><br>"
                f"Weighted avg PM2.5: {row['pm25']:.1f} μg/m³<br>"
                f"Weighted avg emissions: {row['emi']:.4f} t/person<br>"
                f"Total population: {row['pop']:,.0f}<br>"
                f"Countries: {row['n']}<extra></extra>"
            ),
        ))

    fig.add_hline(y=agg_pm25_med, line_dash="dash", line_color="grey", line_width=1.5,
                  annotation_text=f"Median PM2.5: {agg_pm25_med:.1f}",
                  annotation_position="top right", annotation_font_size=10)
    fig.add_vline(x=agg_emi_med, line_dash="dash", line_color="grey", line_width=1.5,
                  annotation_text=f"Median emi: {agg_emi_med:.3f}",
                  annotation_position="top right", annotation_font_size=10)

    fig.update_layout(
        title=dict(text="Who emits vs who breathes worse air — income group aggregates<br>"
                        "<sup>Bubble size = total group population · Values are population-weighted averages</sup>",
                   font_size=14),
        xaxis=dict(
            title="Per capita emissions (tonnes/person)",
            type="linear",          # linear, not log — matches notebook
            showgrid=True, gridcolor="#eeeeee",
        ),
        yaxis=dict(title="PM2.5 concentration (μg/m³)", showgrid=True, gridcolor="#eeeeee"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
        margin=dict(l=60, r=20, t=80, b=60),
        height=520,
    )
    return fig


def make_radar(region):
    rd = REGION_RADAR.get(region)
    if not rd:
        return go.Figure()

    categories = ["Income score", "PM2.5\n(normalised)", "Emissions\n(normalised)"]
    values = [rd["income"], rd["pm25_n"], rd["emi_n"]]
    # Close the polygon
    cats_closed = categories + [categories[0]]
    vals_closed  = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals_closed,
        theta=cats_closed,
        fill="toself",
        fillcolor="rgba(52,152,219,0.2)",
        line=dict(color="#2471a3", width=2),
        name=region,
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], showticklabels=True, tickfont_size=9),
            angularaxis=dict(tickfont_size=11),
        ),
        title=dict(text=f"{region} — profile", font_size=13),
        showlegend=False,
        margin=dict(l=40, r=40, t=60, b=40),
        height=320,
        paper_bgcolor="white",
    )
    return fig


def top5_table(sub_df):
    """Top 5 by PM2.5 per income group."""
    rows = []
    for income in INCOME_ORDER:
        grp = sub_df[sub_df["income"] == income].nlargest(5, "pm25")
        for _, r in grp.iterrows():
            rows.append({
                "Income group": INCOME_SHORT[income],
                "Country": r["name"],
                "PM2.5 (μg/m³)": round(r["pm25"], 1),
                "Emissions (t/p)": round(r["emi"], 4),
                "Population": f"{r['pop']:,.0f}",
            })
    return pd.DataFrame(rows)


# ── App layout ────────────────────────────────────────────────────────────────
app = Dash(__name__)
server = app.server  # for gunicorn

dropdown_options = (
    [{"label": "All regions", "value": "all"},
     {"label": "Income groups (aggregate)", "value": "income_groups"}]
    + [{"label": r, "value": r} for r in REGIONS]
)

app.layout = html.Div([

    html.H2("The Pollution Paradox", style={"marginBottom": "4px"}),
    html.P(
        "Countries that emit the least often breathe the worst air. "
        "Bubble size = population. Average 2010–2019. Source: CEDS / Our World in Data.",
        style={"color": "#666", "fontSize": "13px", "marginBottom": "20px"}
    ),

    html.Div([
        html.Label("Select view:", style={"fontWeight": "bold", "marginRight": "10px"}),
        dcc.Dropdown(
            id="view-dropdown",
            options=dropdown_options,
            value="all",
            clearable=False,
            style={"width": "320px"},
        ),
    ], style={"display": "flex", "alignItems": "center", "marginBottom": "20px"}),

    dcc.Graph(id="main-chart"),

    html.Div(id="radar-section"),

    html.Hr(style={"margin": "24px 0"}),

    html.H4("Top 5 highest PM2.5 countries per income group",
            style={"marginBottom": "12px"}),
    html.Div(id="top5-table"),

], style={"fontFamily": "sans-serif", "maxWidth": "1100px", "margin": "0 auto", "padding": "24px"})


# ── Callbacks ─────────────────────────────────────────────────────────────────
@app.callback(
    Output("main-chart",   "figure"),
    Output("radar-section","children"),
    Output("top5-table",   "children"),
    Input("view-dropdown", "value"),
)
def update(view):
    radar_section = html.Div()

    if view == "all":
        fig   = make_scatter(df, "Who emits vs who breathes worse air — all countries")
        table_df = top5_table(df)

    elif view == "income_groups":
        fig   = make_income_aggregate()
        table_df = top5_table(df)

    else:
        sub   = df[df["region"] == view]
        fig   = make_scatter(sub, f"{view} — emissions vs PM2.5 exposure")
        rd    = REGION_RADAR.get(view, {})
        radar_section = html.Div([
            html.H4(f"{view} — regional profile",
                    style={"marginTop": "24px", "marginBottom": "8px"}),
            html.P(
                f"Income score: {rd.get('income',0):.2f}  ·  "
                f"PM2.5 (weighted): {rd.get('pm25_raw',0):.1f} μg/m³  ·  "
                f"Emissions (weighted): {rd.get('emi_raw',0):.3f} t/person",
                style={"color": "#666", "fontSize": "12px", "marginBottom": "8px"}
            ),
            dcc.Graph(figure=make_radar(view), style={"maxWidth": "380px"}),
        ])
        table_df = top5_table(sub)

    table = dash_table.DataTable(
        data=table_df.to_dict("records"),
        columns=[{"name": c, "id": c} for c in table_df.columns],
        style_table={"overflowX": "auto"},
        style_header={"backgroundColor": "#f5f5f5", "fontWeight": "bold", "fontSize": "12px"},
        style_cell={"fontSize": "12px", "padding": "6px 12px", "textAlign": "left"},
        style_data_conditional=[
            {"if": {"filter_query": '{Income group} = "Low income"'},
             "backgroundColor": "#ebf5fb"},
            {"if": {"filter_query": '{Income group} = "Lower-middle"'},
             "backgroundColor": "#eafaf1"},
            {"if": {"filter_query": '{Income group} = "Upper-middle"'},
             "backgroundColor": "#fef9e7"},
            {"if": {"filter_query": '{Income group} = "High income"'},
             "backgroundColor": "#fdedec"},
        ],
        page_size=20,
    )

    return fig, radar_section, table


if __name__ == "__main__":
    app.run(debug=True, port=8050)
