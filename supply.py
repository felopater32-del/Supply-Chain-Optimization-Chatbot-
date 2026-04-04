import streamlit as st
import pandas as pd
import plotly.express as px
from groq import Groq
import json
import re

st.set_page_config(page_title="Supply Chain Chatbot", page_icon="rocket", layout="wide")

api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)

@st.cache_data
def load_data():
    df = pd.read_csv("Supply_Chain_Optimization.csv")
    return df

df = load_data()

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; }
    .kpi-box { background: #1a1f2e; border: 1px solid #2d3550; border-radius: 14px; padding: 20px; text-align: center; margin-bottom: 10px; }
    .kpi-value { font-size: 2rem; font-weight: 700; color: #00d4ff; }
    .kpi-label { font-size: 0.85rem; color: #8892b0; margin-top: 4px; }
    .chat-bot { background: #1a1f2e; border-left: 4px solid #00d4ff; border-radius: 12px; padding: 16px; margin: 8px 0; color: #ccd6f6; }
    .chat-user { background: #252b3b; border-left: 4px solid #7b2ff7; border-radius: 12px; padding: 16px; margin: 8px 0; color: #ccd6f6; text-align: right; direction: rtl; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Supply Chain Intelligence Chatbot")
st.markdown("<p style='color:#8892b0;'>اسأل اي سؤال عن البيانات - هيرد بارقام وتحليلات ورسوم بيانية</p>", unsafe_allow_html=True)

numeric_cols = df.select_dtypes(include="number").columns.tolist()
kpis = []
for col in numeric_cols[:5]:
    total = df[col].sum()
    avg = df[col].mean()
    val = total if total > avg * 10 else avg
    label = col.replace("_", " ").title()
    fmt = f"{val:,.0f}" if val > 100 else f"{val:,.2f}"
    kpis.append((label, fmt))

cols = st.columns(5)
for i, (label, val) in enumerate(kpis):
    with cols[i]:
        st.markdown(
            f"<div class='kpi-box'><div class='kpi-value'>{val}</div><div class='kpi-label'>{label}</div></div>",
            unsafe_allow_html=True,
        )

st.divider()

with st.expander("عرض البيانات", expanded=False):
    st.dataframe(df.head(50), use_container_width=True, height=300)

st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='chat-user'>سؤال: {msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bot'>الاجابة: {msg['content']}</div>", unsafe_allow_html=True)
        if "chart" in msg:
            st.plotly_chart(msg["chart"], use_container_width=True)

col_input, col_btn = st.columns([5, 1])
with col_input:
    user_question = st.text_input("سؤالك", placeholder="مثال: ما هو المنتج الاعلى مبيعا؟", label_visibility="collapsed")
with col_btn:
    ask_clicked = st.button("اسأل")


def ask_groq(prompt_text):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=0.3,
        max_tokens=2000,
    )
    return response.choices[0].message.content


def try_generate_chart(question, dataframe):
    cols_info = {col: str(dataframe[col].dtype) for col in dataframe.columns}
    sample = dataframe.head(5).to_dict(orient="records")

    chart_prompt = (
        f'You are a data visualization expert. Question: "{question}"\n'
        f"Columns and types: {json.dumps(cols_info)}\n"
        f"Sample rows: {json.dumps(sample, default=str)}\n\n"
        "Respond ONLY with a valid JSON object, no markdown, no explanation:\n"
        '{"chart_type": "bar" or "line" or "pie" or "scatter" or "histogram" or "none",'
        ' "x": "column_name_or_null", "y": "column_name_or_null", "color": "column_name_or_null",'
        ' "title": "chart title in Arabic", "agg": "sum" or "mean" or "count" or "none"}'
    )

    raw = ask_groq(chart_prompt)
    raw = re.sub(r"```json|```", "", raw).strip()
    cfg = json.loads(raw)

    if cfg.get("chart_type") == "none":
        return None

    chart_type = cfg.get("chart_type", "bar")
    x_col = cfg.get("x")
    y_col = cfg.get("y")
    color_col = cfg.get("color")
    title = cfg.get("title", "")
    agg = cfg.get("agg", "none")

    plot_df = dataframe.copy()

    if agg != "none" and x_col and y_col:
        if agg == "sum":
            plot_df = plot_df.groupby(x_col)[y_col].sum().reset_index()
        elif agg == "mean":
            plot_df = plot_df.groupby(x_col)[y_col].mean().reset_index()
        elif agg == "count":
            plot_df = plot_df.groupby(x_col)[y_col].count().reset_index()

    theme = "plotly_dark"
    colors = px.colors.sequential.Plasma

    if chart_type == "bar":
        fig = px.bar(plot_df, x=x_col, y=y_col, color=color_col, title=title, template=theme, color_discrete_sequence=colors)
    elif chart_type == "line":
        fig = px.line(plot_df, x=x_col, y=y_col, color=color_col, title=title, template=theme, color_discrete_sequence=["#00d4ff"])
    elif chart_type == "pie":
        fig = px.pie(plot_df, names=x_col, values=y_col, title=title, template=theme, color_discrete_sequence=colors)
    elif chart_type == "scatter":
        fig = px.scatter(plot_df, x=x_col, y=y_col, color=color_col, title=title, template=theme)
    elif chart_type == "histogram":
        fig = px.histogram(plot_df, x=x_col, title=title, template=theme, color_discrete_sequence=["#7b2ff7"])
    else:
        return None

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,17,23,0.8)",
        font=dict(family="Cairo", color="#ccd6f6"),
        title_font_size=16,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


if ask_clicked and user_question.strip():
    st.session_state.messages.append({"role": "user", "content": user_question})

    with st.spinner("جاري التحليل..."):
        stats = df.describe(include="all").to_string()
        col_list = ", ".join(df.columns.tolist())
        sample_rows = df.head(20).to_string(index=False)

        prompt = (
            "انت محلل بيانات خبير في سلاسل التوريد. اجب باللغة العربية بشكل مفصل.\n"
            "قدم الارقام والاحصاءات. استخدم الترقيم والنقاط.\n"
            "في النهاية اذكر ملخصا يبدا بـ الخلاصة.\n\n"
            f"اعمدة البيانات: {col_list}\n\n"
            f"احصاءات:\n{stats}\n\n"
            f"عينة (اول 20 صف):\n{sample_rows}\n\n"
            f"السؤال: {user_question}"
        )

        answer = ask_groq(prompt)

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

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    "<p style='color:#4a5568; text-align:center; font-size:0.8rem;'>Powered by Groq LLaMA 3.3 | Supply Chain Intelligence</p>",
    unsafe_allow_html=True,
)
