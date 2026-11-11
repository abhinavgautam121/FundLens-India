import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COLORS = ["#16796f", "#4263b6", "#bd8b30", "#8e6eb0", "#c46b6b"]


def style(fig, title: str, y: str = "", percentage: bool = False):
    fig.update_layout(
        title=dict(text=title, font=dict(size=17)),
        template="plotly_white",
        colorway=COLORS,
        font=dict(family="Arial, sans-serif", color="#33435a"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=12, r=16, t=60, b=36),
        height=350,
        legend=dict(orientation="h", y=-0.22),
        yaxis_title=y,
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e7ecf2", zerolinecolor="#dae1e9")
    if percentage:
        fig.update_yaxes(tickformat=".0%")
    return fig


def line_chart(series: dict, title: str, y: str, percentage=False):
    fig = go.Figure()
    for name, s in series.items():
        if not s.empty:
            fig.add_trace(
                go.Scatter(
                    x=s.index,
                    y=s.values,
                    name=name,
                    mode="lines",
                    line=dict(width=2),
                    hovertemplate=(
                        "%{x|%d %b %Y}<br>%{y:.2%}<extra>%{fullData.name}</extra>"
                        if percentage
                        else "%{x|%d %b %Y}<br>%{y:.2f}<extra>%{fullData.name}</extra>"
                    ),
                )
            )
    fig.update_xaxes(title="Observation date")
    return style(fig, title, y, percentage)


def contributions(row, title="Research score · component contributions"):
    labels = ["Consistency", "Risk adjusted", "Benchmark", "Recency"]
    keys = ["consistency", "risk", "benchmark", "recency"]
    values = [row.get(f"{k}_contribution", float("nan")) for k in keys]
    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=COLORS[:4],
            text=[f"{v:.1f} pts" if pd.notna(v) else "Unavailable" for v in values],
            textposition="auto",
            hovertemplate="%{y}: %{x:.2f} points<extra></extra>",
        )
    )
    fig.update_xaxes(title="Points contributed to the 100-point composite")
    return style(fig, title)


def rolling_distribution(series: pd.Series):
    fig = px.histogram(
        x=series,
        nbins=35,
        labels={"x": "Rolling return", "y": "Observations"},
        color_discrete_sequence=COLORS,
    )
    fig.update_xaxes(tickformat=".0%")
    return style(fig, "Distribution of eligible rolling returns", "Number of windows")
