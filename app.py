import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import math

# ── Data ──────────────────────────────────────────────────────────────────────
df = pd.read_csv("Final_Dataset_with_Ranks.csv")
df = df[df["SIDS_category"] == 0].reset_index(drop=True)

df["Per Capita (kg/person)"] = (df["Per capita emissions"] * 1000).round(1)
df["Total Emissions (Mt)"]   = (df["total_emissions_all_pollutants"] / 1e6).round(2)
df["PM2.5 (ug/m3)"]          = df["PM25 Concentration"].round(1)

INCOME_COLORS = {
    "Low-income countries":            "#e07b54",
    "Lower-middle-income countries":   "#f5c75a",
    "Upper-middle-income countries":   "#6ab187",
    "High-income countries":           "#4a90d9",
}

REGIONS   = sorted(df["Region"].unique().tolist())
MED_PM25  = df["PM25 Concentration"].median()
MED_EMISS = df["Per capita emissions"].median()
POP_MAX   = df["Population"].max()

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
        "burdens of poverty and pollution.",
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

# ── Reusable explainer boxes ──────────────────────────────────────────────────
def scatter_explainer():
    return html.Div([
        html.P("How to read this chart", style={
            "fontWeight": "bold", "fontSize": "12px",
            "marginBottom": "8px", "color": "#333"
        }),
        html.Div([
            html.Span("PM2.5 Concentration (Y-axis)", style={"fontWeight": "bold", "color": "#555"}),
            html.Span(" — Annual mean concentration of fine particulate matter "
                      "(particles ≤2.5 μm) in ambient air. Measured in μg/m³. "
                      "WHO safe limit: 5 μg/m³.", style={"color": "#666"}),
        ], style={"marginBottom": "8px", "fontSize": "12px", "lineHeight": "1.6"}),
        html.Div([
            html.Span("Per Capita Emissions (X-axis)", style={"fontWeight": "bold", "color": "#555"}),
            html.Span(" — Total air pollutants emitted per person per year, including "
                      "NOₓ, SO₂, CO, Black Carbon, NH₃, and NMVOCs. "
                      "Measured in tonnes/person/year (log scale for all-countries view).",
                      style={"color": "#666"}),
        ], style={"marginBottom": "8px", "fontSize": "12px", "lineHeight": "1.6"}),
        html.Div([
            html.Span("Bubble size", style={"fontWeight": "bold", "color": "#555"}),
            html.Span(" — Population of the country.",
                      style={"color": "#666"}),
        ], style={"fontSize": "12px", "lineHeight": "1.6"}),
    ], style={
        "backgroundColor": "#f5f5f5",
        "borderLeft": "3px solid #ccc",
        "borderRadius": "4px",
        "padding": "14px 16px",
        "marginTop": "12px",
        "maxWidth": "520px",
    })


def gap_explainer():
    return html.Div([
        html.P("How to read this chart", style={
            "fontWeight": "bold", "fontSize": "12px",
            "marginBottom": "8px", "color": "#333"
        }),
        html.Div([
            html.Span("Pollution Emission Gap (Y-axis)", style={"fontWeight": "bold", "color": "#555"}),
            html.Span(" — Emission Rank minus PM2.5 Rank. "
                      "Ranks run from 1 (lowest) to 149 (highest) across all countries.",
                      style={"color": "#666"}),
        ], style={"marginBottom": "8px", "fontSize": "12px", "lineHeight": "1.6"}),
        html.Div([
            html.Span("Negative gap ↓", style={"fontWeight": "bold", "color": "#e07b54"}),
            html.Span(" — Country emits less than its pollution rank suggests. "
                      "Bears more pollution burden than it causes.",
                      style={"color": "#666"}),
        ], style={"marginBottom": "8px", "fontSize": "12px", "lineHeight": "1.6"}),
        html.Div([
            html.Span("Positive gap ↑", style={"fontWeight": "bold", "color": "#4a90d9"}),
            html.Span(" — Country emits more than its pollution rank suggests. "
                      "Causes more pollution than it experiences.",
                      style={"color": "#666"}),
        ], style={"fontSize": "12px", "lineHeight": "1.6"}),
    ], style={
        "backgroundColor": "#f5f5f5",
        "borderLeft": "3px solid #ccc",
        "borderRadius": "4px",
        "padding": "14px 16px",
        "marginTop": "12px",
        "maxWidth": "520px",
    })


# ── Gap bar chart ─────────────────────────────────────────────────────────────
def make_gap_bar(region_df, region_name):
    df_sorted = region_df.sort_values("Pollution Emission Gap", ascending=True).copy()
    df_sorted = df_sorted.reset_index(drop=True)

    fig = go.Figure()

    # One trace per income group so legend works correctly
    for income, color in INCOME_COLORS.items():
        grp = df_sorted[df_sorted["Income Group"] == income]
        if grp.empty:
            continue
        fig.add_trace(go.Bar(
            x=grp["Country Name"],
            y=grp["Pollution Emission Gap"],
            name=income.replace(" countries", ""),
            marker_color=color,
            marker_line_width=0,
            customdata=grp[["Emission Rank", "PM2.5 Rank",
                             "PM25 Concentration", "Per Capita (kg/person)"]].values,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Gap: %{y:+.0f}<br>"
                "Emission rank: %{customdata[0]:.0f}<br>"
                "PM2.5 rank: %{customdata[1]:.0f}<br>"
                "PM2.5: %{customdata[2]:.1f} μg/m³<br>"
                "Per capita emi: %{customdata[3]:.1f} kg/person"
                "<extra></extra>"
            ),
        ))

    fig.add_hline(y=0, line_color="#333", line_width=1.2)

    fig.update_layout(
        title=dict(text=f"Pollution Emission Gap — {region_name}", font=dict(size=14)),
        xaxis=dict(
            title="",
            tickangle=-45,
            tickfont=dict(size=9),
            showgrid=False,
            categoryorder="array",
            categoryarray=df_sorted["Country Name"].tolist(),
        ),
   
        yaxis=dict(
            title=dict(
            text="Pollution Emission Gap (Emission rank − PM2.5 rank)",
            font=dict(size=11),
         ),
    zeroline=False,
    gridcolor="#eeeeee",
),
        plot_bgcolor="white",
        paper_bgcolor="white",
        bargap=0.15,
        barmode="overlay",
        height=420,
        margin=dict(l=60, r=20, t=50, b=130),
        legend=dict(
            title="Income group",
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=10),
        ),
    )
    return fig


# ── Population legend helper ──────────────────────────────────────────────────
def add_population_legend(fig):
    legend_pops = [1e8, 5e8, 1e9]
    labels      = ["100M", "500M", "1B"]
    for i, (pop_val, label) in enumerate(zip(legend_pops, labels)):
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(
                size=np.sqrt(POP_MAX / pop_val) * 50,
                color="rgba(150,150,150,0.35)",
                line=dict(width=0.5, color="grey"),
                sizemode="area",
            ),
            name=label,
            legendgroup="population",
            legendgrouptitle=dict(text="Population") if i == 0 else None,
            showlegend=True,
        ))
    return fig


# ── Table builder — 2 columns only ───────────────────────────────────────────
def make_table(data_df, title):
    return html.Div([
        html.H5(title, style={
            "marginBottom": "6px", "marginTop": "0",
            "fontSize": "13px", "color": "#444", "fontWeight": "bold"
        }),
        dash_table.DataTable(
            data=data_df.to_dict("records"),
            columns=[{"name": c, "id": c} for c in data_df.columns],
            style_table={"width": "100%"},
            style_header={
                "fontWeight": "bold", "backgroundColor": "#f0f0f0",
                "padding": "7px 10px", "fontSize": "12px",
                "border": "1px solid #ddd"
            },
            style_cell={
                "padding": "7px 10px", "textAlign": "left",
                "fontSize": "12px", "border": "1px solid #eee"
            },
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#fafafa"}
            ],
        ),
    ], style={"flex": "1", "minWidth": "0"})


# ── App ───────────────────────────────────────────────────────────────────────
app  = dash.Dash(__name__)
server = app.server

DROPDOWN_OPTIONS = (
    [{"label": "All Countries",          "value": "all"},
     {"label": "Income Groups",          "value": "income"}]
    + [{"label": r, "value": r} for r in REGIONS]
)

app.layout = html.Div([

    # ── Hero header ───────────────────────────────────────────────────────────
    html.Div([
        html.H1("The Emission-Pollution Paradox",
                style={
                    "fontSize": "32px", "fontWeight": "700",
                    "marginBottom": "10px", "color": "#1a1a1a",
                    "fontFamily": "Georgia, serif",
                }),
        html.P(
            "Higher-income countries emit the most pollutants but experience lower "
            "pollution levels. Lower-income countries, however, bear the greatest "
            "pollution burden despite contributing far less to global emissions. "
            "This dashboard explores that disconnect across 149 countries, averaged "
            "over 2010–2019.",
            style={
                "fontSize": "15px", "color": "#555", "lineHeight": "1.7",
                "maxWidth": "780px", "marginBottom": "0",
            }
        ),
    ], style={
        "backgroundColor": "#f9f7f4",
        "borderLeft": "5px solid #4a90d9",
        "borderRadius": "4px",
        "padding": "24px 28px",
        "marginBottom": "24px",
    }),

    # ── Dropdown ──────────────────────────────────────────────────────────────
    html.Div([
        html.Label("Select view:",
                   style={"fontWeight": "bold", "marginRight": "10px",
                          "fontSize": "13px", "color": "#333"}),
        dcc.Dropdown(
            id="view-selector",
            options=DROPDOWN_OPTIONS,
            value="all",
            clearable=False,
            style={"width": "360px"},
        ),
    ], style={"display": "flex", "alignItems": "center", "marginBottom": "20px"}),

    # ── Main chart ────────────────────────────────────────────────────────────
    dcc.Graph(id="main-chart",
              config={"toImageButtonOptions": {"format": "svg",
                                               "filename": "emission_pollution"},
                      "displayModeBar": True}),

    # ── Explainer box (updates with view) ─────────────────────────────────────
    html.Div(id="explainer-box"),

    # ── Secondary content (tables / writeup / gap chart) ──────────────────────
    html.Div(id="secondary-content", style={"padding": "8px 0"}),

    html.Footer(
        "* SIDS (Small Island Developing States) removed from all analyses. "
        "Emissions cover NOₓ, SO₂, CO, Black Carbon, NH₃, NMVOCs. "
        "Source: CEDS via Our World in Data · WHO Global Air Quality Database.",
        style={
            "textAlign": "center", "color": "#aaa",
            "fontSize": "11px", "marginTop": "32px",
            "borderTop": "1px solid #eee", "paddingTop": "14px",
            "marginBottom": "24px",
        }
    ),

], style={
    "fontFamily": "Arial, sans-serif",
    "maxWidth": "1200px",
    "margin": "0 auto",
    "padding": "24px 20px 0",
})


# ── Callback ──────────────────────────────────────────────────────────────────
@app.callback(
    Output("main-chart",       "figure"),
    Output("explainer-box",    "children"),
    Output("secondary-content","children"),
    Input("view-selector",     "value"),
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
            hover_data={
                "Per Capita (kg/person)": True,
                "Total Emissions (Mt)":   True,
                "PM2.5 (ug/m3)":          True,
                "Per capita emissions":   False,
                "Population":             False,
            },
            size_max=50,
            color_discrete_map=INCOME_COLORS,
            log_x=True,
            title="Per Capita Emissions vs PM2.5 — All Countries",
            labels={
                "Per capita emissions": "Per Capita Emissions — log scale (tonnes/person/year)",
                "PM25 Concentration":   "PM2.5 Concentration (μg/m³)",
            },
        )
        fig.add_vline(
            x=MED_EMISS, line_dash="dash", line_color="steelblue",
            annotation_text=f"Median {MED_EMISS*1000:.0f} kg/person",
            annotation_position="top right",
        )
        fig.add_hline(
            y=MED_PM25, line_dash="dash", line_color="tomato",
            annotation_text=f"Median PM2.5 {MED_PM25:.1f} μg/m³",
            annotation_position="top right",
        )
        fig.update_layout(
            height=600,
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=60, r=160, t=60, b=60),
        )
        fig = add_population_legend(fig)

        # 2-column tables
        t1 = (df.nlargest(5, "total_emissions_all_pollutants")
                [["Country Name", "Total Emissions (Mt)"]]
                .rename(columns={"Country Name": "Country"}))
        t2 = (df.nlargest(5, "PM25 Concentration")
                [["Country Name", "PM2.5 (ug/m3)"]]
                .rename(columns={"Country Name": "Country"}))
        t3 = (df.nlargest(5, "Per capita emissions")
                [["Country Name", "Per Capita (kg/person)"]]
                .rename(columns={"Country Name": "Country"}))

        secondary = html.Div([
            html.Hr(style={"borderColor": "#e0e0e0", "margin": "20px 0 14px"}),
            html.Div([
                make_table(t1, "Top 5 — Highest Total Emissions"),
                html.Div(style={"width": "16px"}),
                make_table(t2, "Top 5 — Highest PM2.5 Exposure"),
                html.Div(style={"width": "16px"}),
                make_table(t3, "Top 5 — Highest Per Capita Emissions"),
            ], style={"display": "flex", "alignItems": "flex-start"}),
        ])
        return fig, scatter_explainer(), secondary

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
                "Per capita emissions": "Wtd. Per Capita Emissions (tonnes/person/year)",
                "PM25 Concentration":   "Wtd. PM2.5 Concentration (μg/m³)",
            },
        )
        fig.add_vline(
            x=MED_EMISS, line_dash="dash", line_color="steelblue",
            annotation_text=f"Global median {MED_EMISS*1000:.0f} kg/person",
        )
        fig.add_hline(
            y=MED_PM25, line_dash="dash", line_color="tomato",
            annotation_text=f"Global median PM2.5 {MED_PM25:.1f} μg/m³",
        )
        fig.update_traces(textposition="top center", textfont=dict(size=11))
        fig.update_layout(
            height=600,
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=60, r=160, t=60, b=120),
        )
        fig = add_population_legend(fig)

        secondary = html.Div(
            style={
                "backgroundColor": "#f9f9f9", "borderRadius": "6px",
                "padding": "16px 20px", "marginTop": "8px",
                "fontSize": "13px", "color": "#444", "lineHeight": "1.6",
                "borderLeft": "3px solid #6ab187",
            },
            children=[
                html.Strong("Reading this chart: "),
                "Each bubble is a population-weighted average for an income group. "
                "Bubble size shows share of world population. "
                "The paradox is visible: lower-middle income countries sit in the "
                "high-pollution, low-emission quadrant. High-income countries occupy "
                "the opposite — high emissions, lower exposure.",
            ]
        )
        return fig, scatter_explainer(), secondary

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
            hover_data={
                "Per Capita (kg/person)": True,
                "Total Emissions (Mt)":   True,
                "PM2.5 (ug/m3)":          True,
                "Per capita emissions":   False,
                "Population":             False,
            },
            size_max=50,
            color_discrete_map=INCOME_COLORS,
            title=f"Per Capita Emissions vs PM2.5 — {view}",
            labels={
                "Per capita emissions": "Per Capita Emissions (tonnes/person/year)",
                "PM25 Concentration":   "PM2.5 Concentration (μg/m³)",
            },
        )
        fig.add_vline(
            x=MED_EMISS, line_dash="dash", line_color="steelblue",
            annotation_text=f"Global median {MED_EMISS*1000:.0f} kg/person",
        )
        fig.add_hline(
            y=MED_PM25, line_dash="dash", line_color="tomato",
            annotation_text=f"Global median PM2.5 {MED_PM25:.1f} μg/m³",
        )
        fig.update_layout(
            height=520,
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=60, r=160, t=60, b=60),
        )
        fig = add_population_legend(fig)

        writeup = REGION_WRITEUPS.get(view, "")
        gap_fig  = make_gap_bar(region_df, view)

        secondary = html.Div([

            # Region description
            html.Div(
                style={
                    "backgroundColor": "#f9f7f4",
                    "borderLeft": "4px solid #6ab187",
                    "borderRadius": "4px",
                    "padding": "16px 20px",
                    "marginTop": "12px",
                    "marginBottom": "20px",
                },
                children=[
                    html.H4(view, style={"marginTop": 0, "marginBottom": "6px",
                                         "fontSize": "15px", "color": "#222"}),
                    html.Span("Regional Story  ",
                              style={"fontSize": "10px", "color": "#6ab187",
                                     "fontWeight": "bold", "textTransform": "uppercase",
                                     "letterSpacing": "0.1em"}),
                    html.P(writeup, style={"color": "#555", "lineHeight": "1.7",
                                           "fontSize": "13px", "marginBottom": 0,
                                           "marginTop": "6px"}),
                ]
            ),

            html.Hr(style={"borderColor": "#e0e0e0", "margin": "8px 0 16px"}),

            # Gap bar chart
            dcc.Graph(
                figure=gap_fig,
                config={"toImageButtonOptions": {"format": "svg",
                                                 "filename": f"gap_{view}"}},
            ),

            # Gap explainer
            gap_explainer(),
        ])

        return fig, scatter_explainer(), secondary




server = app.server

if __name__ == "__main__":
    app.run(debug=True)


