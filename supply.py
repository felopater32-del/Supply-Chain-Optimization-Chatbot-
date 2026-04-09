import streamlit as st
import pandas as pd
import plotly.express as px
from groq import Groq
import json

# ========================
# 1. إعدادات الصفحة والتصميم
# ========================
st.set_page_config(page_title="Supply Chain Expert AI", page_icon="📊", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; }
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
    .kpi-value { font-size: 1.6rem; font-weight: 700; color: #00d4ff; }
    .kpi-label { font-size: 0.8rem; color: #8892b0; margin-top: 4px; }
    .kpi-answer { font-size: 1.6rem; font-weight: 700; color: #f0a500; }
    .chat-bot {
        background: #1a1f2e;
        border-right: 5px solid #00d4ff;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        color: #ccd6f6;
        line-height: 1.6;
        direction: rtl;
    }
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
        font-size: 1.1rem;
        font-weight: 700;
        margin: 16px 0 8px 0;
        text-align: right;
        direction: rtl;
    }
</style>
""", unsafe_allow_html=True)

# ========================
# 2. الربط مع Groq وتحميل البيانات
# ========================
try:
    api_key = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=api_key)
except KeyError:
    st.error("⚠️ مفيش GROQ_API_KEY في Secrets")
    st.stop()
except Exception as e:
    st.warning(f"تحذير: {e}")
@st.cache_data
def load_data():
    return pd.read_csv("Supply_Chain_Optimization.csv")

df = load_data()

# ========================
# 3. واجهة الـ KPIs (لوحة التحكم العلوية)
# ========================
st.title("🚀 Supply Chain Smart Analyst")

k1, k2, k3, k4, k5, k6 = st.columns(6)
metrics = [
    (df['Demand_Units'].sum(), "Total Demand"),
    (df['Transportation_Cost_USD'].mean(), "Avg Transport Cost"),
    (df['Supplier_Reliability_Score'].mean(), "Supplier Reliability"),
    (df['Stockout_Incidents'].sum(), "Stockout Incidents"),
    (df['Supply_Chain_Efficiency_Index'].mean(), "Efficiency Index"),
    (df['Lead_Time_Days'].mean(), "Lead Time")
]
for idx, (val, label) in enumerate(metrics):
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
# 4. دوال بناء الـ Dashboard
# ========================

def get_dashboard_config(question):
    cols_info = {col: str(df[col].dtype) for col in df.columns}

    numeric_stats = {}
    for col in df.select_dtypes(include='number').columns:
        numeric_stats[col] = {
            "sum": float(round(df[col].sum(), 2)),
            "mean": float(round(df[col].mean(), 2)),
            "min": float(round(df[col].min(), 2)),
            "max": float(round(df[col].max(), 2))
        }

    cat_cols = list(df.select_dtypes(exclude='number').columns)

    prompt = f"""
You are a Senior Supply Chain Analyst building a data dashboard.

User Question: "{question}"
Available Columns: {json.dumps(cols_info)}
Numeric Stats: {json.dumps(numeric_stats)}
Categorical Columns: {cat_cols}

Design a COMPLETE dashboard to answer the question. Return ONLY valid JSON:

{{
  "dashboard_title": "Arabic title for this dashboard",
  "kpis": [
    {{"label": "Arabic label", "column": "col_name", "agg": "sum|mean|max|min|count"}}
  ],
  "charts": [
    {{
      "chart_type": "bar|line|pie|scatter|histogram|box",
      "x": "col_name",
      "y": "col_name_or_null",
      "agg": "sum|mean|count|none",
      "title": "Arabic chart title",
      "color_col": "col_name_or_null"
    }}
  ],
  "insight_prompt": "A focused prompt to generate 3 key Arabic insights from the data"
}}

Rules:
- kpis: exactly 4 KPIs
- charts: exactly 4 DIFFERENT charts using DIFFERENT columns
- All titles/labels in English
- kpi labels in English
- color_col: use a categorical column if it adds value, else null
"""

    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        return None


def get_ai_insights(insight_prompt, stats_summary):
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a Supply Chain Expert. Write 3 brief analytical insights in English. Each insight on one line starting with ✅"
                },
                {
                    "role": "user",
                    "content": f"{insight_prompt}\n\nإحصائيات: {stats_summary}"
                }
            ]
        )
        return resp.choices[0].message.content
    except Exception:
        return "لم يتمكن النظام من توليد الرؤى."


def build_kpi_cards(kpi_configs):
    kpi_data = []
    for kpi in kpi_configs:
        col = kpi.get("column")
        agg = kpi.get("agg", "mean")
        label = kpi.get("label", col)

        if not col or col not in df.columns:
            continue

        try:
            if agg == "sum":
                val = df[col].sum()
            elif agg == "mean":
                val = df[col].mean()
            elif agg == "max":
                val = df[col].max()
            elif agg == "min":
                val = df[col].min()
            elif agg == "count":
                val = df[col].count()
            else:
                val = df[col].mean()

            fmt = f"{val:,.1f}" if val < 10000 else f"{val:,.0f}"
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
    x_col = cfg.get("x")
    y_col = cfg.get("y")
    title = cfg.get("title", "")
    agg = cfg.get("agg", "none")
    color_col = cfg.get("color_col")

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
        plot_bgcolor="rgba(15,17,23,0.5)",
        font=dict(family="Cairo", color="#ccd6f6", size=11),
        title=dict(text=f"<b>{title}</b>", font=dict(size=13, color="#00d4ff")),
        hovermode="x unified",
        margin=dict(l=10, r=10, t=50, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#ccd6f6")),
        xaxis=dict(gridcolor="#1e2433", tickfont=dict(size=9)),
        yaxis=dict(gridcolor="#1e2433")
    )

    color_seq = ['#00d4ff', '#7b2ff7', '#f0a500', '#00ff88', '#ff6b6b', '#a8edea']

    try:
        if chart_type == "bar":
            fig = px.bar(
                plot_df, x=x_col, y=y_col, color=color_col,
                color_discrete_sequence=color_seq, barmode="group"
            )
        elif chart_type == "line":
            fig = px.line(
                plot_df, x=x_col, y=y_col, color=color_col,
                markers=True, line_shape="spline",
                color_discrete_sequence=color_seq
            )
        elif chart_type == "pie":
            fig = px.pie(
                plot_df, names=x_col, values=y_col, hole=0.45,
                color_discrete_sequence=px.colors.sequential.Plasma_r
            )
            fig.update_traces(textfont_color="#fff")
        elif chart_type == "scatter":
            fig = px.scatter(
                plot_df, x=x_col, y=y_col, color=color_col,
                color_discrete_sequence=color_seq, opacity=0.75
            )
        elif chart_type == "histogram":
            fig = px.histogram(
                plot_df, x=x_col, color=color_col,
                color_discrete_sequence=color_seq, nbins=20
            )
        elif chart_type == "box":
            fig = px.box(
                plot_df, x=x_col, y=y_col, color=color_col,
                color_discrete_sequence=color_seq
            )
        else:
            return None

        fig.update_layout(**layout_args)
        return fig
    except Exception:
        return None


def render_full_dashboard(question):
    with st.spinner("🔍 جاري تحليل بياناتك وبناء الـ Dashboard..."):
        config = get_dashboard_config(question)

    if not config:
        st.error("لم يتمكن النظام من توليد الـ Dashboard. حاول مرة أخرى.")
        return None

    # عنوان الـ Dashboard
    st.markdown(
        f"<div class='dashboard-title'>📊 {config.get('dashboard_title', 'تحليل البيانات')}</div>",
        unsafe_allow_html=True
    )

    # KPI Cards
    if config.get("kpis"):
        build_kpi_cards(config["kpis"])

    st.markdown("<br>", unsafe_allow_html=True)

    # المخططات في grid 2x2
    charts_cfg = config.get("charts", [])
    valid_figs = []
    for cfg in charts_cfg:
        fig = build_chart_fig(cfg)
        if fig is not None:
            valid_figs.append(fig)

    if valid_figs:
        # الصف الأول
        if len(valid_figs) >= 2:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(valid_figs[0], use_container_width=True)
            with col2:
                st.plotly_chart(valid_figs[1], use_container_width=True)
        elif len(valid_figs) == 1:
            st.plotly_chart(valid_figs[0], use_container_width=True)

        # الصف الثاني
        if len(valid_figs) >= 4:
            col3, col4 = st.columns(2)
            with col3:
                st.plotly_chart(valid_figs[2], use_container_width=True)
            with col4:
                st.plotly_chart(valid_figs[3], use_container_width=True)
        elif len(valid_figs) == 3:
            st.plotly_chart(valid_figs[2], use_container_width=True)

    # الرؤى التحليلية
    st.markdown(
        "<div class='dashboard-title'>💡 الرؤى التحليلية</div>",
        unsafe_allow_html=True
    )

    with st.spinner("جاري توليد الرؤى..."):
        stats_summary = df.describe().to_string()
        insight_prompt = config.get("insight_prompt", f"حلل البيانات وأجب عن: {question}")
        insights = get_ai_insights(insight_prompt, stats_summary)

    st.markdown(f"<div class='chat-bot'>{insights}</div>", unsafe_allow_html=True)

    return {"question": question, "insights": insights}


# ========================
# 5. واجهة المحادثة
# ========================
if "history" not in st.session_state:
    st.session_state.history = []

col_in, col_btn = st.columns([5, 1])
with col_in:
    user_q = st.text_input(
        "اسأل عن أي تحليل في بياناتك:",
        placeholder="مثلاً: قارن بين كفاءة المناطق المختلفة وتكلفة النقل"
    )
with col_btn:
    analyze_clicked = st.button("تحليل الآن ✨")

if analyze_clicked and user_q:
    st.markdown(f"<div class='chat-user'>👤 {user_q}</div>", unsafe_allow_html=True)
    result = render_full_dashboard(user_q)
    if result:
        st.session_state.history.append(result)
    st.divider()

# عرض السجل السابق
if st.session_state.history:
    st.markdown("### 📂 التحليلات السابقة")
    previous = st.session_state.history[:-1] if (analyze_clicked and user_q) else st.session_state.history
    for item in reversed(previous):
        with st.expander(f"🔹 {item['question']}", expanded=False):
            st.markdown(
                f"<div class='chat-bot'>{item['insights']}</div>",
                unsafe_allow_html=True
            )

# ========================
# 6. القائمة الجانبية
# ========================
st.sidebar.title("🛠️ أدوات التحكم")

if st.sidebar.button("🗑️ مسح المحادثة"):
    st.session_state.history = []
    st.rerun()

if st.sidebar.checkbox("عرض البيانات المصدر"):
    st.dataframe(df.head(50))

st.sidebar.divider()
st.sidebar.markdown("**📋 أعمدة البيانات المتاحة:**")
for col in df.columns:
    dtype = str(df[col].dtype)
    icon = "🔢" if ("int" in dtype or "float" in dtype) else "🔤"
    st.sidebar.markdown(f"{icon} `{col}`")
