import streamlit as st
import pandas as pd
import plotly.express as px
from groq import Groq
import json

# ========================
# 1. Page Config & Styling
# ========================
st.set_page_config(page_title="Supply Chain Expert AI", page_icon="📊", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
    .main { background: #0f1117; }
    .kpi-box {
        background: linear-gradient(135deg, #1a1f2e, #252b3b);
        border: 1px solid #2d3550;
        border-radius: 14px;
        padding: 18px;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .kpi-value  { font-size: 1.6rem; font-weight: 700; color: #00d4ff; }
    .kpi-answer { font-size: 1.6rem; font-weight: 700; color: #f0a500; }
    .kpi-label  { font-size: 0.8rem; color: #8892b0; margin-top: 4px; }
    .chat-user {
        background: #252b3b;
        border-left: 5px solid #7b2ff7;
        border-radius: 12px;
        padding: 16px;
        margin: 10px 0;
        color: #ccd6f6;
        text-align: right;
        direction: rtl;
    }
    .dashboard-title {
        color: #00d4ff;
        font-size: 1.2rem;
        font-weight: 700;
        margin: 20px 0 10px 0;
        padding-bottom: 6px;
        border-bottom: 1px solid #2d3550;
    }
    .insight-box {
        background: linear-gradient(135deg, #1a1f2e, #0f1117);
        border: 1px solid #2d3550;
        border-left: 4px solid #00ff88;
        border-radius: 10px;
        padding: 18px 22px;
        margin: 8px 0;
        color: #ccd6f6;
        line-height: 1.8;
        direction: ltr;
        text-align: left;
    }
</style>
""", unsafe_allow_html=True)

# ========================
# 2. Groq Client & Data
# ========================
try:
    api_key = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=api_key)
except KeyError:
    st.error("Add GROQ_API_KEY to Streamlit Secrets")
    st.stop()
except Exception as e:
    st.warning(f"Warning: {e}")

@st.cache_data
def load_data():
    return pd.read_csv("Supply_Chain_Optimization.csv")

df = load_data()

# ========================
# 3. Top KPI Bar
# ========================
st.title("🚀 Supply Chain Smart Analyst")

k1, k2, k3, k4, k5, k6 = st.columns(6)
top_metrics = [
    (df['Demand_Units'].sum(),                  "Total Demand"),
    (df['Transportation_Cost_USD'].mean(),       "Avg Transport Cost"),
    (df['Supplier_Reliability_Score'].mean(),    "Supplier Reliability"),
    (df['Stockout_Incidents'].sum(),             "Stockout Incidents"),
    (df['Supply_Chain_Efficiency_Index'].mean(), "Efficiency Index"),
    (df['Lead_Time_Days'].mean(),                "Lead Time (days)"),
]
for idx, (val, label) in enumerate(top_metrics):
    with [k1, k2, k3, k4, k5, k6][idx]:
        fmt = f"{val:,.1f}" if val < 1000 else f"{val:,.0f}"
        st.markdown(
            f"<div class='kpi-box'>"
            f"<div class='kpi-value'>{fmt}</div>"
            f"<div class='kpi-label'>{label}</div>"
            f"</div>",
            unsafe_allow_html=True
        )

st.divider()

# ========================
# 4. Smart Dashboard Engine
# ========================

def get_smart_dashboard_config(question):
    cols_info = {col: str(df[col].dtype) for col in df.columns}

    numeric_stats = {}
    for col in df.select_dtypes(include='number').columns:
        numeric_stats[col] = {
            "sum":  float(round(df[col].sum(), 2)),
            "mean": float(round(df[col].mean(), 2)),
            "min":  float(round(df[col].min(), 2)),
            "max":  float(round(df[col].max(), 2)),
            "std":  float(round(df[col].std(), 2)),
        }

    cat_cols = {}
    for col in df.select_dtypes(exclude='number').columns:
        cat_cols[col] = df[col].unique().tolist()[:10]

    prompt = f"""
You are a world-class Supply Chain Data Scientist and BI Analyst.

=== USER QUESTION ===
"{question}"

=== DATASET CONTEXT ===
Columns & Types: {json.dumps(cols_info)}
Numeric Statistics: {json.dumps(numeric_stats)}
Categorical Columns & Sample Values: {json.dumps(cat_cols)}
Total Rows: {len(df)}

=== YOUR TASK ===
Think step by step:
1. Understand exactly what the user is asking.
2. Identify the most relevant columns that directly answer the question.
3. Design 4 KPIs that give immediate numeric answers to the question.
4. Design 4 charts that visually explain the answer — each chart must tell a different part of the story.
5. Write a smart insight_prompt that will guide generating deep analytical observations.

=== CHART STRATEGY ===
- Use bar charts for comparisons between categories
- Use line charts for trends over time or ordered data
- Use scatter charts for correlations between two numeric variables
- Use pie/donut for part-of-whole distributions
- Use histogram for distributions of a single numeric variable
- Use box plots for spread and outliers comparison
- NEVER repeat the same x-column in two charts
- ALWAYS pick the chart type that best fits the data shape

=== OUTPUT FORMAT ===
Return ONLY a valid JSON object:

{{
  "dashboard_title": "Short descriptive English title for this analysis",
  "analysis_focus": "One sentence explaining what this dashboard reveals",
  "kpis": [
    {{
      "label": "English KPI label",
      "column": "exact_column_name",
      "agg": "sum|mean|max|min|count"
    }}
  ],
  "charts": [
    {{
      "chart_type": "bar|line|pie|scatter|histogram|box",
      "x": "exact_column_name",
      "y": "exact_column_name_or_null",
      "agg": "sum|mean|count|none",
      "title": "English chart title describing the insight",
      "color_col": "exact_column_name_or_null"
    }}
  ],
  "insight_prompt": "Detailed prompt asking for 4 specific analytical insights. Reference specific column names and expected patterns."
}}

Rules:
- kpis: exactly 4, all directly relevant to the question
- charts: exactly 4, each using DIFFERENT x columns
- All labels and titles in English
- column names must EXACTLY match the dataset columns
- color_col must be a categorical column name or null
"""

    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        st.error(f"Config error: {e}")
        return None


def get_smart_insights(insight_prompt, question, numeric_stats):
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Senior Supply Chain Analyst. "
                        "Write sharp, specific, data-driven insights in English. "
                        "Each insight must reference actual numbers or patterns from the data. "
                        "Format: 4 insights, each on its own line starting with an emoji bullet. "
                        "Be direct and actionable — no vague statements."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"User Question: {question}\n\n"
                        f"Analysis Task: {insight_prompt}\n\n"
                        f"Data Statistics:\n{json.dumps(numeric_stats, indent=2)}"
                    )
                }
            ],
            temperature=0.5
        )
        return resp.choices[0].message.content
    except Exception:
        return "Could not generate insights. Please try again."


def build_kpi_cards(kpi_configs):
    kpi_data = []
    for kpi in kpi_configs:
        col   = kpi.get("column")
        agg   = kpi.get("agg", "mean")
        label = kpi.get("label", col)

        if not col or col not in df.columns:
            continue

        try:
            if agg == "sum":     val = df[col].sum()
            elif agg == "mean":  val = df[col].mean()
            elif agg == "max":   val = df[col].max()
            elif agg == "min":   val = df[col].min()
            elif agg == "count": val = df[col].count()
            else:                val = df[col].mean()

            if val >= 1_000_000:
                fmt = f"{val/1_000_000:.2f}M"
            elif val >= 1_000:
                fmt = f"{val:,.0f}"
            else:
                fmt = f"{val:,.2f}"
        except Exception:
            fmt = "N/A"

        kpi_data.append((label, fmt))

    if kpi_data:
        cols = st.columns(len(kpi_data))
        for i, (label, val) in enumerate(kpi_data):
            with cols[i]:
                st.markdown(
                    f"<div class='kpi-box'>"
                    f"<div class='kpi-answer'>{val}</div>"
                    f"<div class='kpi-label'>{label}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )


def build_chart_fig(cfg):
    chart_type = cfg.get("chart_type", "bar")
    x_col      = cfg.get("x")
    y_col      = cfg.get("y")
    title      = cfg.get("title", "")
    agg        = cfg.get("agg", "none")
    color_col  = cfg.get("color_col")

    if not x_col or x_col not in df.columns:
        return None
    if color_col and color_col not in df.columns:
        color_col = None

    plot_df = df.copy()

    if agg != "none" and y_col and y_col in df.columns:
        group_cols = [x_col]
        if color_col and color_col != x_col:
            group_cols.append(color_col)
        try:
            if agg == "sum":
                plot_df = plot_df.groupby(group_cols)[y_col].sum().reset_index()
            elif agg == "mean":
                plot_df = plot_df.groupby(group_cols)[y_col].mean().reset_index()
            elif agg == "count":
                plot_df = plot_df.groupby(group_cols)[y_col].count().reset_index()
        except Exception:
            plot_df = df.copy()

    layout_args = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,17,23,0.6)",
        font=dict(family="Cairo", color="#ccd6f6", size=11),
        title=dict(text=f"<b>{title}</b>", font=dict(size=13, color="#00d4ff")),
        hovermode="x unified",
        margin=dict(l=10, r=10, t=55, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#ccd6f6")),
        xaxis=dict(gridcolor="#1e2433", tickfont=dict(size=9), linecolor="#2d3550"),
        yaxis=dict(gridcolor="#1e2433", linecolor="#2d3550")
    )

    color_seq = ['#00d4ff', '#7b2ff7', '#f0a500', '#00ff88', '#ff6b6b', '#a8edea', '#ff9f43']

    try:
        if chart_type == "bar":
            fig = px.bar(
                plot_df, x=x_col, y=y_col, color=color_col,
                color_discrete_sequence=color_seq, barmode="group"
            )
            fig.update_traces(marker_line_width=0)

        elif chart_type == "line":
            fig = px.line(
                plot_df, x=x_col, y=y_col, color=color_col,
                markers=True, line_shape="spline",
                color_discrete_sequence=color_seq
            )
            fig.update_traces(line_width=2.5)

        elif chart_type == "pie":
            fig = px.pie(
                plot_df, names=x_col, values=y_col, hole=0.45,
                color_discrete_sequence=px.colors.sequential.Plasma_r
            )
            fig.update_traces(textfont_color="#fff", textfont_size=11)

        elif chart_type == "scatter":
            fig = px.scatter(
                plot_df, x=x_col, y=y_col, color=color_col,
                color_discrete_sequence=color_seq, opacity=0.7
            )

        elif chart_type == "histogram":
            fig = px.histogram(
                plot_df, x=x_col, color=color_col,
                color_discrete_sequence=color_seq, nbins=25, opacity=0.85
            )

        elif chart_type == "box":
            fig = px.box(
                plot_df, x=x_col, y=y_col, color=color_col,
                color_discrete_sequence=color_seq, notched=True
            )
        else:
            return None

        fig.update_layout(**layout_args)
        return fig

    except Exception:
        return None


def render_full_dashboard(question):
    with st.spinner("🧠 Analyzing your question and designing the dashboard..."):
        config = get_smart_dashboard_config(question)

    if not config:
        st.error("Could not generate dashboard. Please try again.")
        return None

    # Dashboard Header
    st.markdown(
        f"<div class='dashboard-title'>"
        f"📊 {config.get('dashboard_title', 'Supply Chain Analysis')}"
        f"</div>",
        unsafe_allow_html=True
    )

    focus = config.get("analysis_focus", "")
    if focus:
        st.caption(f"🎯 {focus}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Smart KPIs
    if config.get("kpis"):
        build_kpi_cards(config["kpis"])

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Grid 2x2
    charts_cfg  = config.get("charts", [])
    valid_figs  = []
    for cfg in charts_cfg:
        fig = build_chart_fig(cfg)
        if fig is not None:
            valid_figs.append(fig)

    if valid_figs:
        if len(valid_figs) >= 2:
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(valid_figs[0], use_container_width=True)
            with c2:
                st.plotly_chart(valid_figs[1], use_container_width=True)
        elif len(valid_figs) == 1:
            st.plotly_chart(valid_figs[0], use_container_width=True)

        if len(valid_figs) >= 4:
            c3, c4 = st.columns(2)
            with c3:
                st.plotly_chart(valid_figs[2], use_container_width=True)
            with c4:
                st.plotly_chart(valid_figs[3], use_container_width=True)
        elif len(valid_figs) == 3:
            st.plotly_chart(valid_figs[2], use_container_width=True)
    else:
        st.warning("No charts could be rendered. Try rephrasing your question.")

    # Smart Insights
    st.markdown(
        "<div class='dashboard-title'>💡 Key Insights</div>",
        unsafe_allow_html=True
    )

    numeric_stats = {}
    for col in df.select_dtypes(include='number').columns:
        numeric_stats[col] = {
            "mean": float(round(df[col].mean(), 2)),
            "max":  float(round(df[col].max(), 2)),
            "min":  float(round(df[col].min(), 2)),
        }

    with st.spinner("Generating insights..."):
        insight_prompt = config.get("insight_prompt", f"Analyze the data for: {question}")
        insights = get_smart_insights(insight_prompt, question, numeric_stats)

    st.markdown(f"<div class='insight-box'>{insights}</div>", unsafe_allow_html=True)

    return {
        "question": question,
        "title":    config.get("dashboard_title", ""),
        "insights": insights
    }


# ========================
# 5. Chat Interface
# ========================
if "history" not in st.session_state:
    st.session_state.history = []

col_in, col_btn = st.columns([5, 1])
with col_in:
    user_q = st.text_input(
        "Ask anything about your supply chain data:",
        placeholder="e.g. What regions have the highest transportation cost and lowest efficiency?"
    )
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_clicked = st.button("Analyze ✨", use_container_width=True)

if analyze_clicked and user_q:
    st.markdown(f"<div class='chat-user'>👤 {user_q}</div>", unsafe_allow_html=True)
    result = render_full_dashboard(user_q)
    if result:
        st.session_state.history.append(result)
    st.divider()

# Previous Analyses
if st.session_state.history:
    previous = (
        st.session_state.history[:-1]
        if (analyze_clicked and user_q)
        else st.session_state.history
    )
    if previous:
        st.markdown("### 📂 Previous Analyses")
        for item in reversed(previous):
            label = item.get("title") or item["question"]
            with st.expander(f"🔹 {label}", expanded=False):
                st.markdown(f"**Question:** {item['question']}")
                st.markdown(
                    f"<div class='insight-box'>{item['insights']}</div>",
                    unsafe_allow_html=True
                )

# ========================
# 6. Sidebar
# ========================
st.sidebar.title("🛠️ Controls")

if st.sidebar.button("🗑️ Clear History"):
    st.session_state.history = []
    st.rerun()

st.sidebar.divider()

if st.sidebar.checkbox("Show Raw Data"):
    st.dataframe(df.head(50))

st.sidebar.divider()
st.sidebar.markdown("**📋 Available Columns:**")
for col in df.columns:
    dtype = str(df[col].dtype)
    icon  = "🔢" if ("int" in dtype or "float" in dtype) else "🔤"
    st.sidebar.markdown(f"{icon} `{col}`")
