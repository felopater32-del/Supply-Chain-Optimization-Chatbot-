import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google import genai
import json
import re

# ========================
# Page Config
# ========================
st.set_page_config(
    page_title="Supply Chain Chatbot",
    page_icon="🚀",
    layout="wide"
)

# ========================
# Load API Key from Streamlit Secrets
# ========================
api_key = st.secrets["GOOGLE_API_KEY"]
client = genai.Client(api_key=api_key)

# ========================
# Load Data from CSV (موجود في نفس الـ repository)
# ========================
@st.cache_data
def load_data():
    df = pd.read_csv("Supply_Chain_Optimization.csv")
    return df

df = load_data()

# ========================
# Styling
# ========================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
    .main { background: #0f1117; }
    .block-container { padding: 2rem 3rem; }
    h1 {
        background: linear-gradient(135deg, #00d4ff, #7b2ff7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
    }
    .kpi-box {
        background: linear-gradient(135deg, #1a1f2e, #252b3b);
        border: 1px solid #2d3550;
        border-radius: 14px;
        padding: 1.2rem 1.5rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    .kpi-value { font-size: 2rem; font-weight: 700; color: #00d4ff; }
    .kpi-label { font-size: 0.85rem; color: #8892b0; margin-top: 4px; }
    .chat-bubble-bot {
        background: linear-gradient(135deg, #1a1f2e, #1e2a45);
        border-left: 4px solid #00d4ff;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 0.8rem 0;
        color: #ccd6f6;
    }
    .chat-bubble-user {
        background: #252b3b;
        border-left: 4px solid #7b2ff7;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 0.8rem 0;
        color: #ccd6f6;
        text-align: right;
        direction: rtl;
    }
    .section-title {
        color: #8892b0;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin: 1.5rem 0 0.5rem;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #00d4ff, #7b2ff7);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        font-family: 'Cairo', sans-serif;
        transition: opacity 0.2s;
    }
    div.stButton > button:hover { opacity: 0.85; }
    .stTextInput > div > div > input {
        background: #1a1f2e !important;
        border: 1px solid #2d3550 !important;
        border-radius: 10px !important;
        color: #ccd6f6 !important;
        font-family: 'Cairo', sans-serif !important;
        direction: rtl;
    }
</style>
""", unsafe_allow_html=True)

# ========================
# Header
# ========================
st.title("🚀 Supply Chain Intelligence Chatbot")
st.markdown("<p style='color:#8892b0;'>اسأل أي سؤال عن البيانات — هيرد بأرقام وتحليلات ورسوم بيانية</p>", unsafe_allow_html=True)

# ========================
# KPI Dashboard Strip
# ========================
st.markdown("<div class='section-title'>📊 لمحة سريعة</div>", unsafe_allow_html=True)

cols = st.columns(5)
kpis = []

numeric_cols = df.select_dtypes(include='number').columns.tolist()
for i, col in enumerate(numeric_cols[:5]):
    val = df[col].sum() if df[col].sum() > df[col].mean() * 10 else df[col].mean()
    label = col.replace("_", " ").title()
    fmt = f"{val:,.0f}" if val > 100 else f"{val:,.2f}"
    kpis.append((label, fmt))

for i, (label, val) in enumerate(kpis):
    with cols[i]:
        st.markdown(f"""
        <div class='kpi-box'>
            <div class='kpi-value'>{val}</div>
            <div class='kpi-label'>{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ========================
# Data Preview Toggle
# ========================
with st.expander("📋 عرض البيانات الكاملة", expanded=False):
    st.dataframe(df.head(50), use_container_width=True, height=300)

st.divider()

# ========================
# Chat History
# ========================
if "messages" not in st.session_state:
    st.session_state.messages = []

# عرض المحادثة السابقة
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='chat-bubble-user'>❓ {msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bubble-bot'>🤖 {msg['content']}</div>", unsafe_allow_html=True)
        if "chart" in msg:
            st.plotly_chart(msg["chart"], use_container_width=True)

# ========================
# Input Box
# ========================
col_input, col_btn = st.columns([5, 1])
with col_input:
    user_question = st.text_input(
        "",
        placeholder="مثال: ما هو المنتج الأعلى مبيعاً؟ أو قارن التكاليف بالإيرادات",
        label_visibility="collapsed"
    )
with col_btn:
    ask_clicked = st.button("اسأل ✨")

# ========================
# Helper: توليد الرسم البياني تلقائياً
# ========================
def try_generate_chart(question: str, df: pd.DataFrame):
    cols_info = {col: str(df[col].dtype) for col in df.columns}
    sample = df.head(5).to_dict(orient="records")

    chart_prompt = f"""
You are a data visualization expert. Given this question: "{question}"
And a dataframe with these columns and types: {json.dumps(cols_info)}
Sample rows: {json.dumps(sample, default=str)}

Respond ONLY with a valid JSON object (no markdown, no explanation) like:
{{
  "chart_type": "bar" | "line" | "pie" | "scatter" | "histogram" | "none",
  "x": "column_name_or_null",
  "y": "column_name_or_null",
  "color": "column_name_or_null",
  "title": "Chart title in Arabic",
  "agg": "sum" | "mean" | "count" | "none"
}}
If no chart is appropriate, return {{"chart_type": "none"}}.
"""
    resp = client.models.generate_content(model="gemini-1.5-flash", contents=chart_prompt)
    raw = resp.text.strip()
    raw = re.sub(r"```json|```", "", raw).strip()
    cfg = json.loads(raw)

    if cfg.get("chart_type") == "none":
        return None

    chart_type = cfg.get("chart_type", "bar")
    x_col     = cfg.get("x")
    y_col     = cfg.get("y")
    color_col = cfg.get("color")
    title     = cfg.get("title", "")
    agg       = cfg.get("agg", "none")

    plot_df = df.copy()

    # تجميع البيانات لو مطلوب
    if agg != "none" and x_col and y_col:
        if agg == "sum":
            plot_df = plot_df.groupby(x_col)[y_col].sum().reset_index()
        elif agg == "mean":
            plot_df = plot_df.groupby(x_col)[y_col].mean().reset_index()
        elif agg == "count":
            plot_df = plot_df.groupby(x_col)[y_col].count().reset_index()

    plotly_theme = "plotly_dark"

    if chart_type == "bar":
        fig = px.bar(plot_df, x=x_col, y=y_col, color=color_col,
                     title=title, template=plotly_theme,
                     color_discrete_sequence=px.colors.sequential.Plasma)
    elif chart_type == "line":
        fig = px.line(plot_df, x=x_col, y=y_col, color=color_col,
                      title=title, template=plotly_theme,
                      color_discrete_sequence=["#00d4ff"])
    elif chart_type == "pie":
        fig = px.pie(plot_df, names=x_col, values=y_col,
                     title=title, template=plotly_theme,
                     color_discrete_sequence=px.colors.sequential.Plasma)
    elif chart_type == "scatter":
        fig = px.scatter(plot_df, x=x_col, y=y_col, color=color_col,
                         title=title, template=plotly_theme)
    elif chart_type == "histogram":
        fig = px.histogram(plot_df, x=x_col,
                           title=title, template=plotly_theme,
                           color_discrete_sequence=["#7b2ff7"])
    else:
        return None

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,17,23,0.8)",
        font=dict(family="Cairo", color="#ccd6f6"),
        title_font_size=16,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

# ========================
# Main Chat Logic
# ========================
if ask_clicked and user_question.strip():
    st.session_state.messages.append({"role": "user", "content": user_question})

    with st.spinner("جارٍ التحليل..."):
        stats       = df.describe(include='all').to_string()
        col_list    = ", ".join(df.columns.tolist())
        sample_rows = df.head(20).to_string(index=False)

        prompt = f"""أنت محلل بيانات خبير في سلاسل التوريد. أجب على السؤال التالي باللغة العربية بشكل مفصل وشامل.
قدم الأرقام والإحصاءات المحددة من البيانات. استخدم الترقيم والنقاط لتنظيم إجابتك.
في نهاية الإجابة، اذكر ملخصاً من سطر واحد يبدأ بـ "**الخلاصة:**".

أعمدة البيانات: {col_list}

إحصاءات البيانات:
{stats}

عينة من البيانات (أول 20 صف):
{sample_rows}

السؤال: {user_question}
"""
        response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        answer = response.text

        # محاولة توليد رسم بياني
        chart = None
        try:
            chart = try_generate_chart(user_question, df)
        except Exception:
            chart = None

        msg = {"role": "assistant", "content": answer}
        if chart:
            msg["chart"] = chart
        st.session_state.messages.append(msg)

    st.rerun()

# ========================
# Footer
# ========================
st.markdown("<br><hr style='border-color:#2d3550'>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#4a5568; text-align:center; font-size:0.8rem;'>"
    "Powered by Gemini 2.0 Flash · Supply Chain Intelligence"
    "</p>",
    unsafe_allow_html=True
)
