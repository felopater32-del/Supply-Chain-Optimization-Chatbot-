import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import json
import re
import os

# ========================
# Page Config
# ========================
st.set_page_config(page_title="Supply Chain Intelligence", page_icon="🚀", layout="wide")

# ========================
# Load API Key & Setup Model
# ========================
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    # استخدام الموديل المستقر 1.5 فلاش لضمان العمل في كل المناطق
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"⚠️ Error setting up AI: {e}")

# ========================
# Load Data
# ========================
@st.cache_data
def load_data():
    if os.path.exists("Supply_Chain_Optimization.csv"):
        return pd.read_csv("Supply_Chain_Optimization.csv")
    return pd.DataFrame()

df = load_data()

# ========================
# Styling (CSS)
# ========================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; }
    .main { background: #0f1117; }
    h1 { background: linear-gradient(135deg, #00d4ff, #7b2ff7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700 !important; }
    .chat-bubble-bot { background: #1e2a45; border-left: 4px solid #00d4ff; border-radius: 12px; padding: 1rem; margin: 10px 0; color: #ccd6f6; direction: rtl; }
    .chat-bubble-user { background: #252b3b; border-right: 4px solid #7b2ff7; border-radius: 12px; padding: 1rem; margin: 10px 0; color: #ccd6f6; direction: rtl; }
</style>
""", unsafe_allow_html=True)

# ========================
# Header & KPIs
# ========================
st.title("🚀 Supply Chain Intelligence Chatbot")

if not df.empty:
    cols = st.columns(4)
    cols[0].metric("إجمالي العمليات", len(df))
    cols[1].metric("المنتجات الفريدة", df.iloc[:, 0].nunique())
    # عرض الإيرادات لو العمود موجود
    rev_cols = [c for c in df.columns if 'revenue' in c.lower()]
    if rev_cols:
        cols[2].metric("إجمالي الإيرادات", f"${df[rev_cols[0]].sum():,.0f}")
    cols[3].metric("عدد المخازن/المدن", df.iloc[:, 1].nunique() if len(df.columns) > 1 else 0)

    st.divider()

    # ========================
    # Chat Logic
    # ========================
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        role_class = "chat-bubble-user" if msg["role"] == "user" else "chat-bubble-bot"
        st.markdown(f"<div class='{role_class}'>{msg['content']}</div>", unsafe_allow_html=True)
        if "chart" in msg:
            st.plotly_chart(msg["chart"], use_container_width=True)

    # Input area
    user_question = st.text_input("اسأل أي سؤال عن بياناتك:", placeholder="مثلاً: قارن بين تكلفة الشحن للمدن المختلفة")
    
    if st.button("تحليل البيانات ✨"):
        if user_question:
            st.session_state.messages.append({"role": "user", "content": user_question})
            
            with st.spinner("جاري التفكير والتحليل..."):
                # 1. Text Analysis
                stats = df.describe(include='all').to_string()
                prompt = f"أنت خبير سلاسل إمداد. حلل هذه البيانات:\n{stats}\nالسؤال: {user_question}\nأجب بالعربية بنقاط واضحة وفي النهاية اكتب الخلاصة."
                
                response = model.generate_content(prompt)
                answer = response.text

                # 2. Chart Logic (Simplified)
                chart = None
                if "رسم" in user_question or "chart" in user_question.lower() or "قارن" in user_question:
                    # رسم بياني تلقائي لأول عمودين رقميين
                    num_cols = df.select_dtypes(include=['number']).columns
                    cat_cols = df.select_dtypes(include=['object']).columns
                    if len(num_cols) > 0 and len(cat_cols) > 0:
                        fig = px.bar(df.head(20), x=cat_cols[0], y=num_cols[0], template="plotly_dark", title="تحليل بياني مقترح")
                        chart = fig

                st.session_state.messages.append({"role": "assistant", "content": answer, "chart": chart})
                st.rerun()
else:
    st.error("⚠️ لم يتم العثور على ملف البيانات Supply_Chain_Optimization.csv")
