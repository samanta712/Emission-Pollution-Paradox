import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import pandas as pd
import numpy as np

# ── Data ──────────────────────────────────────────────────────────────────────
df = pd.read_csv("Final_Dataset.csv")
df = df[df["SIDS_category"] == 0].reset_index(drop=True)

# Derived display columns with correct units
# Raw per capita is in tonnes/person → convert to kg/person for display
# Raw total is in tonnes → convert to Mt for display
df["Per Capita (kg/person)"]  = (df["Per capita emissions"] * 1000).round(1)
df["Total Emissions (Mt)"]    = (df["total_emissions_all_pollutants"] / 1e6).round(2)
df["PM2.5 (ug/m3)"]           = df["PM25 Concentration"].round(1)

INCOME_COLORS = {
    "Low-income countries":            "#e07b54",
    "Lower-middle-income countries":   "#f5c75a",
    "Upper-middle-income countries":   "#6ab187",
    "High-income countries":           "#4a90d9",
}

REGIONS = sorted(df["Region"].unique().tolist())

MED_PM25  = df["PM25 Concentration"].median()
MED_EMISS = df["Per capita emissions"].median()

REGION_WRITEUPS = {
    "East Asia & Pacific":
        "East Asia & Pacific shows a striking polarisation: high-income exporters "
        "generate substantial per-capita emissions while lower-middle-income nations "
        "absorb disproportionate PM2.5 exposure — a clear trade-off between industrial "
        "output and public health.",
    "Europe & Central Asia":
        "Europe & Central Asia spans the widest income range of any region. Western "
        "European nations combine high emissions with relatively clean air, aided by "
        "strong regulatory frameworks, while Central Asian states face elevated pollution "
        "despite modest per-capita output.",
    "Latin America & Caribbean":
        "Latin America & Caribbean sits in a middle tier on both axes. Inequality "
        "within the region is visible: upper-middle-income countries emit more but "
        "invest in air-quality controls, while lower-income nations face compounding "
        "burdens of pollution.",
    "Middle East, North Africa, Afghanistan & Pakistan":
        "MENA & South-West Asia presents a stark paradox. Oil-rich high-income states "
        "lead on per-capita emissions, yet the heaviest PM2.5 burden falls on "
        "lower-income nations — driven by dust, informal industry, and limited "
        "environmental enforcement.",
    "North America":
        "North America's two high-income economies occupy the high-emission quadrant, "
        "yet sustained investment in clean-air policy has kept PM2.5 levels "
        "comparatively moderate. The region's story is one of historical accumulation "
        "without proportional contemporary exposure.",
    "South Asia":
        "South Asia is the region where the pollution paradox is most acute. Despite "
        "the lowest per-capita emissions among all regions, it records the highest "
        "average PM2.5 concentrations — driven by dense populations, biomass burning, "
        "and transboundary dust.",
    "Sub-Saharan Africa":
        "Sub-Saharan Africa contributes the least to global emissions on a per-capita "
        "basis, yet carries a severe PM2.5 burden from household solid-fuel use and "
        "limited urban infrastructure. The region encapsulates the core injustice of "
        "the emission-pollution paradox.",
}

# ── App ───────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__)
server = app.server

DROPDOWN_OPTIONS = (
    [{"label": "All Countries", "value": "all"},
     {"label": "Income Groups", "value": "income"}]
    + [{"label": r, "value": r} for r in REGIONS]
)

# ── Shared table style ────────────────────────────────────────────────────────
def make_table(data_df, title):
    return html.Div([
        html.H5(title, style={"marginBottom": "6px", "marginTop": "0",
                              "fontSize": "13px", "color": "#444",
                              "fontWeight": "bold"}),
        dash_table.DataTable(
            data=data_df.to_dict("records"),
            columns=[{"name": c, "id": c} for c in data_df.columns],
            style_table={"width": "100%"},
            style_header={"fontWeight": "bold", "backgroundColor": "#f0f0f0",
                          "padding": "7px 10px", "fontSize": "12px",
                          "border": "1px solid #ddd"},
            style_cell={"padding": "7px 10px", "textAlign": "left",
                        "fontSize": "12px", "border": "1px solid #eee"},
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#fafafa"}
            ],
        ),
    ], style={"flex": "1", "minWidth": "0"})


app.layout = html.Div([

    html.H1("The Emission-Pollution Paradox",
            style={"textAlign": "center", "marginBottom": "4px"}),

    html.P("Exploring the disconnect between per-capita emissions and PM2.5 exposure for the years 2010-2019.",
           style={"textAlign": "center", "color": "grey", "marginTop": 0}),

    html.Div([
        dcc.Dropdown(
            id="view-selector",
            options=DROPDOWN_OPTIONS,
            value="all",
            clearable=False,
            style={"width": "360px", "margin": "16px auto"},
        )
    ], style={"textAlign": "center"}),

    dcc.Graph(id="main-chart",
              config={"toImageButtonOptions": {"format": "svg",
                                               "filename": "emission_pollution"},
                      "displayModeBar": True}),

    html.Div(id="secondary-content", style={"padding": "8px 0"}),

    html.Footer("* SIDS(Small Island Developing States) countries removed from all plots. ",
                style={"textAlign": "center", "color": "grey",
                       "fontSize": "11px", "marginTop": "24px",
                       "borderTop": "1px solid #eee", "paddingTop": "12px"}),

], style={"fontFamily": "Arial, sans-serif", "maxWidth": "1100px", "margin": "0 auto",
          "padding": "0 16px"})


# ── Callback ──────────────────────────────────────────────────────────────────
@app.callback(
    Output("main-chart",        "figure"),
    Output("secondary-content", "children"),
    Input("view-selector",      "value"),
)
def update(view):

    # ── ALL COUNTRIES ─────────────────────────────────────────────────────────
    if view == "all":
        fig = px.scatter(
            df,
            x="Per capita emissions",
            y="PM25 Concentration",
            size="Population",
            color="Income Group",
            hover_name="Country Name",
            hover_data={"Per Capita (kg/person)": True,
                        "Total Emissions (Mt)": True,
                        "PM2.5 (ug/m3)": True,
                        "Per capita emissions": False,
                        "Population": False},
            size_max=50,
            color_discrete_map=INCOME_COLORS,
            log_x=True,
            title="Per Capita Emissions vs PM2.5 — All Countries",
            labels={
                "Per capita emissions": "Per Capita Emissions (log scale)",
                "PM25 Concentration":   "PM2.5 Concentration (ug/m3)",
            },
        )
        fig.add_vline(x=MED_EMISS, line_dash="dash", line_color="steelblue",
                      annotation_text=f"Global Median Per Capita Emission: {MED_EMISS*1000:.0f} kg/person")
        fig.add_hline(y=MED_PM25, line_dash="dash", line_color="tomato",
                      annotation_text=f"Global Median PM 2.5 Concentration {MED_PM25:.1f} ug/m3")
        fig.update_layout(
            height=600,
            margin=dict(l=60, r=140, t=60, b=60),
        )

        # ── Three tables ──────────────────────────────────────────────────
        # Table 1: Top 5 total emitters
        t1 = (df.nlargest(5, "total_emissions_all_pollutants")
                [["Country Name", "Total Emissions (Mt)", "PM2.5 (ug/m3)"]]
                .rename(columns={"Country Name": "Country"}))

        # Table 2: Top 5 most polluted (PM2.5)
        t2 = (df.nlargest(5, "PM25 Concentration")
                [["Country Name", "PM2.5 (ug/m3)", "Per Capita (kg/person)"]]
                .rename(columns={"Country Name": "Country"}))

        # Table 3: Top 5 per capita emitters
        t3 = (df.nlargest(5, "Per capita emissions")
                [["Country Name", "Per Capita (kg/person)", "Total Emissions (Mt)"]]
                .rename(columns={"Country Name": "Country"}))

        secondary = html.Div([
            html.Div([
                make_table(t1, "Top 5 — Total Emitters"),
                html.Div(style={"width": "16px"}),
                make_table(t2, "Top 5 — Most Polluted (PM2.5)"),
                html.Div(style={"width": "16px"}),
                make_table(t3, "Top 5 — Highest Per Capita Emissions"),
            ], style={"display": "flex", "alignItems": "flex-start",
                      "gap": "16px"}),
        ])
        return fig, secondary

    # ── INCOME GROUPS ─────────────────────────────────────────────────────────
    elif view == "income":
        rows = []
        total_pop = df["Population"].sum()
        for ig, grp in df.groupby("Income Group"):
            pop = grp["Population"].sum()
            pct = pop / total_pop * 100
            rows.append({
                "Income Group":         ig,
                "PM25 Concentration":   (grp["PM25 Concentration"]  * grp["Population"]).sum() / pop,
                "Per capita emissions": (grp["Per capita emissions"] * grp["Population"]).sum() / pop,
                "Population":           pop,
                "Pop_pct":              pct,
                "Bubble Label":         ig.replace(" countries", "") + f"\n{pct:.0f}% of world pop",
            })
        ig_df = pd.DataFrame(rows)

        fig = px.scatter(
            ig_df,
            x="Per capita emissions",
            y="PM25 Concentration",
            size="Population",
            color="Income Group",
            hover_name="Income Group",
            text="Bubble Label",
            size_max=70,
            color_discrete_map=INCOME_COLORS,
            title="Population-Weighted Emissions vs PM2.5 — by Income Group",
            labels={
                "Per capita emissions": "Wtd. Per Capita Emissions (kg/person)",
                "PM25 Concentration":   "Wtd. PM2.5 Concentration (ug/m3)",
            },
        )
        #fig.add_vline(x=MED_EMISS, line_dash="dash", line_color="steelblue",
                      #annotation_text=f"Median {MED_EMISS*1000:.0f} kg/person")
        #fig.add_hline(y=MED_PM25, line_dash="dash", line_color="tomato",
                      #annotation_text=f"Median PM2.5 {MED_PM25:.1f} ug/m3")
        fig.add_vline(x=MED_EMISS, line_dash="dash", line_color="steelblue",
                      annotation_text=f"Global Median Per Capita Emission: {MED_EMISS*1000:.0f} kg/person")
        fig.add_hline(y=MED_PM25, line_dash="dash", line_color="tomato",
                      annotation_text=f"Global Median PM 2.5 Concentration {MED_PM25:.1f} ug/m3")
        fig.update_traces(textposition="top center", textfont=dict(size=11))
        fig.update_layout(
            height=600,
            margin=dict(l=60, r=140, t=60, b=120),
        )

        secondary = html.Div(
            style={"backgroundColor": "#f9f9f9", "borderRadius": "8px",
                   "padding": "16px 20px", "marginTop": "8px",
                   "fontSize": "13px", "color": "#444", "lineHeight": "1.6"},
            children=[
                html.Strong("How to read this chart: "),
                "Each bubble represents an income group. Position shows the "
                "population-weighted average PM2.5 and per-capita emissions. "
                "Bubble size and the percentage label both show share of world population. "
                "The paradox is visible: lower-middle income countries sit in the "
                "high-pollution zone despite low emissions, while high-income countries "
                "emit far more but face lower PM2.5 exposure.",
            ]
        )
        return fig, secondary

    # ── REGION ────────────────────────────────────────────────────────────────
    else:
        region_df = df[df["Region"] == view].copy()

        fig = px.scatter(
            region_df,
            x="Per capita emissions",
            y="PM25 Concentration",
            size="Population",
            color="Income Group",
            hover_name="Country Name",
            hover_data={"Per Capita (kg/person)": True,
                        "Total Emissions (Mt)": True,
                        "PM2.5 (ug/m3)": True,
                        "Per capita emissions": False,
                        "Population": False},
            size_max=50,
            color_discrete_map=INCOME_COLORS,
            title=f"Per Capita Emissions vs PM2.5 — {view}",
            labels={
                "Per capita emissions": "Per Capita Emissions (kg/person)",
                "PM25 Concentration":   "PM2.5 Concentration (ug/m3)",
            },
        )
        fig.add_vline(x=MED_EMISS, line_dash="dash", line_color="steelblue",
                      annotation_text=f"Global median Per Capita Emission {MED_EMISS*1000:.0f} kg/person")
        fig.add_hline(y=MED_PM25, line_dash="dash", line_color="tomato",
                      annotation_text=f"Global median PM 2.5 Conencentration{MED_PM25:.1f} ug/m3")
        fig.update_layout(
            height=600,
            margin=dict(l=60, r=140, t=60, b=60),
        )

        # Normalise spokes against global min/max
        norm_df = region_df.copy()
        for col in ["GDP Per Capita", "PM25 Concentration", "Per capita emissions"]:
            mn, mx = float(df[col].min()), float(df[col].max())
            norm_df[col] = (norm_df[col] - mn) / (mx - mn)

        pop = float(norm_df["Population"].sum())
        r_income = float((norm_df["GDP Per Capita"]       * norm_df["Population"]).sum() / pop)
        r_pm25   = float((norm_df["PM25 Concentration"]   * norm_df["Population"]).sum() / pop)
        r_emiss  = float((norm_df["Per capita emissions"] * norm_df["Population"]).sum() / pop)

        radar_df = pd.DataFrame({
            "Spoke": ["Income (GDP)", "PM2.5", "Emissions"],
            "Value": [r_income, r_pm25, r_emiss],
        })

        radar_fig = px.line_polar(
            radar_df,
            r="Value",
            theta="Spoke",
            line_close=True,
            title=f"Regional Profile — {view}",
        )
        radar_fig.update_traces(fill="toself")
        radar_fig.update_layout(height=380)

        writeup = REGION_WRITEUPS.get(
            view,
            "This region's profile reflects a unique combination of income, "
            "pollution exposure, and emissions. Explore the scatter above to "
            "understand how individual countries contribute to the regional pattern."
        )

        secondary = html.Div([
            html.Div([
                html.Div(
                    dcc.Graph(figure=radar_fig,
                              config={"toImageButtonOptions": {"format": "svg"}}),
                    style={"flex": "1"}
                ),
                html.Div([
                    html.H4(view, style={"marginTop": 0, "marginBottom": "6px"}),
                    html.P("Regional Story",
                           style={"fontSize": "11px", "color": "#6ab187",
                                  "fontWeight": "bold", "textTransform": "uppercase",
                                  "letterSpacing": "0.08em", "marginBottom": "8px",
                                  "marginTop": 0}),
                    html.P(writeup,
                           style={"color": "#444", "lineHeight": "1.7",
                                  "fontSize": "13px"}),
                    html.Hr(style={"margin": "12px 0", "borderColor": "#e0e0e0"}),
                    html.P(
                        f"Normalised values (pop-weighted):  "
                        f"Income = {r_income:.2f}  |  PM2.5 = {r_pm25:.2f}  |  Emissions = {r_emiss:.2f}",
                        style={"fontSize": "11px", "color": "grey", "margin": 0}
                    ),
                ], style={"flex": "1", "padding": "24px",
                          "backgroundColor": "#f9f9f9",
                          "borderRadius": "8px",
                          "marginLeft": "16px",
                          "alignSelf": "center"}),
            ], style={"display": "flex", "alignItems": "flex-start"}),
        ])
        return fig, secondary



server = app.server

if __name__ == "__main__":
    app.run(debug=True)


