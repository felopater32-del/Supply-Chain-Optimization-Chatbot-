import streamlit as st
import pandas as pd
import plotly.express as px
from groq import Groq
import json
import re

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
</style>
""", unsafe_allow_html=True)

# ========================
# 2. الربط مع Groq وتحميل البيانات
# ========================
try:
    api_key = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=api_key)
except Exception as e:
    st.error("⚠️ تأكد من إضافة GROQ_API_KEY في Streamlit Secrets")

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
        st.markdown(f"<div class='kpi-box'><div class='kpi-value'>{fmt}</div><div class='kpi-label'>{label}</div></div>", unsafe_allow_html=True)

st.divider()

# ========================
# 4. محرك الرسوم البيانية المتطور
# ========================
def build_chart(cfg):
    chart_type = cfg.get("chart_type", "bar")
    x_col = cfg.get("x")
    y_col = cfg.get("y")
    title = cfg.get("title", "")
    agg = cfg.get("agg", "none")

    if not x_col or x_col not in df.columns: return None
    
    plot_df = df.copy()
    if agg != "none" and y_col and y_col in df.columns:
        if agg == "sum": plot_df = plot_df.groupby(x_col)[y_col].sum().reset_index()
        elif agg == "mean": plot_df = plot_df.groupby(x_col)[y_col].mean().reset_index()

    layout_args = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,17,23,0.5)",
        font=dict(family="Cairo", color="#ccd6f6"),
        hovermode="x unified",
        margin=dict(l=10, r=10, t=50, b=10)
    )

    if chart_type == "bar":
        fig = px.bar(plot_df, x=x_col, y=y_col, title=f"📊 {title}", color_discrete_sequence=['#00d4ff'])
    elif chart_type == "line":
        fig = px.line(plot_df, x=x_col, y=y_col, title=f"📈 {title}", markers=True, line_shape="spline")
        fig.update_traces(line_color='#7b2ff7')
    elif chart_type == "pie":
        fig = px.pie(plot_df, names=x_col, values=y_col, title=f"🍩 {title}", hole=0.4, color_discrete_sequence=px.colors.sequential.Plasma_r)
    elif chart_type == "scatter":
        fig = px.scatter(plot_df, x=x_col, y=y_col, title=f"🎯 {title}", color_discrete_sequence=['#00ff88'])
    else: return None

    fig.update_layout(**layout_args)
    return fig

def try_generate_charts(question):
    cols_list = list(df.columns)
    # برومبت صارم لمنع التكرار وإجبار الموديل على التنوع
    prompt = (
        f"You are a Senior Supply Chain Analyst. User Question: '{question}'\n"
        f"Available Columns: {json.dumps(cols_list)}\n\n"
        "Instructions:\n"
        "1. Choose 3 DIFFERENT charts that best answer the question.\n"
        "2. DO NOT repeat the same column choices every time.\n"
        "3. Respond with ONLY a JSON object: {'charts': [{'chart_type': 'bar|line|pie|scatter', 'x': 'col_name', 'y': 'col_name', 'agg': 'sum|mean|none', 'title': 'Arabic Title'}]}"
    )
    
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8, # زيادة العشوائية للإبداع
            response_format={"type": "json_object"}
        )
        configs = json.loads(resp.choices[0].message.content).get("charts", [])
        charts = [build_chart(cfg) for cfg in configs if build_chart(cfg) is not None]
        return charts[:3]
    except:
        return []

# ========================
# 5. منطق المحادثة والتحليل
# ========================
if "history" not in st.session_state: st.session_state.history = []

col_in, col_btn = st.columns([5, 1])
with col_in:
    user_q = st.text_input("اسأل عن أي تحليل في بياناتك:", placeholder="مثلاً: قارن بين كفاءة المناطق المختلفة وتكلفة النقل")
with col_btn:
    if st.button("تحليل الآن ✨") and user_q:
        with st.spinner("جاري فحص البيانات وتوليد الرسوم..."):
            # 1. تحليل نصي
            stats_summary = df.describe(include='all').to_string()
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "انت خبير سلاسل إمداد. حلل الأرقام بدقة وأجب بالعربية."},
                          {"role": "user", "content": f"إحصائيات: {stats_summary}\nالسؤال: {user_q}"}]
            )
            ans = res.choices[0].message.content
            
            # 2. توليد رسوم بيانية
            charts = try_generate_charts(user_q)
            
            st.session_state.history.append({"q": user_q, "a": ans, "charts": charts})

# عرض المحادثة (من الأحدث للأقدم)
for item in reversed(st.session_state.history):
    st.markdown(f"<div class='chat-user'>👤 {item['q']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='chat-bot'>🤖 {item['a']}</div>", unsafe_allow_html=True)
    if item['charts']:
        c_cols = st.columns(len(item['charts']))
        for i, f in enumerate(item['charts']):
            with c_cols[i]: st.plotly_chart(f, use_container_width=True)

# ========================
# 6. القائمة الجانبية (Sidebar)
# ========================
st.sidebar.title("🛠️ أدوات التحكم")
if st.sidebar.button("🗑️ مسح المحادثة"):
    st.session_state.history = []
    st.rerun()

if st.sidebar.checkbox("عرض البيانات المصدر"):
    st.dataframe(df.head(50))
