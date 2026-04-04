import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
import json
import re
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Page Config
st.set_page_config(page_title="Supply Chain Chatbot", page_icon="📦", layout="wide")

# API Key with better error handling
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error("""
    ⚠️ **خطأ في مفتاح API**
    
    يرجى التأكد من:
    1. إضافة مفتاح API في Secrets Management على Streamlit Cloud
    2. التأكد من صحة المفتاح
    
    [رابط إضافة المفاتيح السرية](https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)
    """)
    st.stop()

# Load Data with error handling for GitHub
@st.cache_data
def load_data():
    try:
        # محاولة تحميل الملف من نفس المجلد
        df = pd.read_csv("Supply_Chain_Optimization.csv")
        return df
    except FileNotFoundError:
        try:
            # محاولة مسار مختلف
            df = pd.read_csv("data/Supply_Chain_Optimization.csv")
            return df
        except FileNotFoundError:
            st.error("""
            ⚠️ **ملف البيانات غير موجود**
            
            يرجى التأكد من:
            1. رفع ملف Supply_Chain_Optimization.csv إلى GitHub
            2. وضع الملف في نفس مجلد التطبيق
            """)
            # إنشاء بيانات تجريبية للاختبار
            st.warning("📝 جاري إنشاء بيانات تجريبية للاختبار...")
            test_data = {
                'Product_ID': [f'P{i:03d}' for i in range(1, 101)],
                'Demand_Units': np.random.randint(500, 2000, 100),
                'Forecasted_Demand': np.random.randint(500, 2000, 100),
                'Inventory_Level': np.random.randint(300, 2500, 100),
                'Reorder_Point': np.random.randint(200, 1500, 100),
                'Lead_Time_Days': np.random.randint(5, 30, 100)
            }
            df = pd.DataFrame(test_data)
            return df

df = load_data()

# Styling
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
    }
    .kpi-box {
        background: #1a1f2e;
        border: 1px solid #2d3550;
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        margin-bottom: 10px;
        transition: all 0.3s ease;
    }
    .kpi-box:hover {
        transform: translateY(-2px);
        border-color: #00d4ff;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #00d4ff;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: #8892b0;
        margin-top: 4px;
    }
    .chat-bot {
        background: linear-gradient(135deg, #1a1f2e 0%, #1e2436 100%);
        border-left: 4px solid #00d4ff;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        color: #ccd6f6;
    }
    .chat-user {
        background: linear-gradient(135deg, #252b3b 0%, #2a3145 100%);
        border-left: 4px solid #7b2ff7;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        color: #ccd6f6;
        text-align: right;
        direction: rtl;
    }
    .stButton > button {
        background: linear-gradient(90deg, #00d4ff 0%, #7b2ff7 100%);
        color: white;
        border: none;
        font-weight: 600;
        padding: 0.5rem 2rem;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 15px rgba(0,212,255,0.3);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header with GitHub info
col1, col2 = st.columns([4, 1])
with col1:
    st.title("📊 Supply Chain Intelligence Chatbot")
    st.markdown(
        "<p style='color:#8892b0;'>اسأل أي سؤال عن البيانات — هيرد بأرقام وتحليلات ورسوم بيانية</p>",
        unsafe_allow_html=True,
    )
with col2:
    st.markdown("[![GitHub](https://img.shields.io/badge/GitHub-View_Code-181717?style=flat-square&logo=github)](https://github.com/your-repo)")

# KPI Strip
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

# Data Preview
with st.expander("📋 عرض البيانات", expanded=False):
    st.dataframe(df.head(50), use_container_width=True, height=300)
    
    # إضافة معلومات عن حجم البيانات
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 عدد الصفوف", f"{len(df):,}")
    with col2:
        st.metric("📋 عدد الأعمدة", len(df.columns))
    with col3:
        st.metric("💾 حجم البيانات", f"{df.memory_usage(deep=True).sum() / 1024:.0f} KB")

st.divider()

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(
            f"<div class='chat-user'>❓ سؤال: {msg['content']}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='chat-bot'>💡 الإجابة: {msg['content']}</div>",
            unsafe_allow_html=True,
        )
        if "chart" in msg and msg["chart"]:
            st.plotly_chart(msg["chart"], use_container_width=True, key=f"chart_{len(st.session_state.messages)}")

# Input Area
col_input, col_btn = st.columns([5, 1])
with col_input:
    user_question = st.text_input(
        "سؤالك",
        placeholder="مثال: ما هو المنتج الأعلى مبيعاً؟ أو اعرض لي توزيع المخزون",
        label_visibility="collapsed",
        key="user_input"
    )
with col_btn:
    ask_clicked = st.button("🔍 اسأل", type="primary", use_container_width=True)

# Add example questions
with st.expander("💡 أسئلة مقترحة"):
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📈 أعلى منتج مبيعاً"):
            user_question = "ما هو المنتج الأعلى مبيعاً؟"
            ask_clicked = True
        if st.button("📊 توزيع المخزون"):
            user_question = "اعرض لي توزيع المخزون"
            ask_clicked = True
    with col2:
        if st.button("⏱️ متوسط وقت التوريد"):
            user_question = "ما هو متوسط وقت التوريد؟"
            ask_clicked = True
        if st.button("🎯 نقاط إعادة الطلب"):
            user_question = "اعرض لي نقاط إعادة الطلب"
            ask_clicked = True

# Retry decorator for API calls with specific exceptions
@retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception)
)
def generate_with_retry(client, model, contents):
    """إعادة المحاولة تلقائياً عند فشل الاتصال"""
    try:
        response = client.models.generate_content(model=model, contents=contents)
        return response
    except Exception as e:
        # طباعة الخطأ للتشخيص (لن يظهر للمستخدم)
        print(f"API Error: {str(e)}")
        time.sleep(2)
        raise e

# Simplified Chart Generator with better error handling
def try_generate_chart(question, dataframe):
    """توليد رسم بياني بناءً على السؤال"""
    try:
        # محاولة بسيطة لإنشاء رسم بياني بدون Gemini للأسئلة الشائعة
        question_lower = question.lower()
        
        # رسوم بيانية محددة مسبقاً للأسئلة الشائعة
        if "المخزون" in question_lower or "inventory" in question_lower:
            numeric_col = [col for col in dataframe.columns if 'inventory' in col.lower() or 'stock' in col.lower()]
            if numeric_col:
                fig = px.histogram(dataframe, x=numeric_col[0], title="توزيع المخزون", 
                                 template="plotly_dark", color_discrete_sequence=["#00d4ff"])
                return fig
                
        elif "الطلب" in question_lower or "demand" in question_lower:
            demand_col = [col for col in dataframe.columns if 'demand' in col.lower()]
            if demand_col:
                fig = px.box(dataframe, y=demand_col[0], title="توزيع الطلب", 
                           template="plotly_dark", color_discrete_sequence=["#7b2ff7"])
                return fig
        
        # محاولة استخدام Gemini للرسوم البيانية المتقدمة
        cols_info = {col: str(dataframe[col].dtype) for col in dataframe.columns[:10]}  # Limit columns
        sample = dataframe.head(3).to_dict(orient="records")

        chart_prompt = (
            f'Question: "{question}"\n'
            f"Columns: {json.dumps(cols_info)}\n"
            f"Sample: {json.dumps(sample, default=str)}\n\n"
            "Respond ONLY with valid JSON:\n"
            '{"chart_type": "bar"|"line"|"pie"|"none",'
            ' "x": "column_name", "y": "column_name",'
            ' "title": "Arabic title"}'
        )

        response = generate_with_retry(client, "gemini-1.5-flash", chart_prompt)
        
        # تنظيف النص
        raw = re.sub(r"```json|```|`", "", response.text.strip()).strip()
        cfg = json.loads(raw)

        if cfg.get("chart_type") == "none":
            return None

        chart_type = cfg.get("chart_type", "bar")
        x_col = cfg.get("x")
        y_col = cfg.get("y")
        title = cfg.get("title", "")

        # التحقق من وجود الأعمدة
        if x_col and x_col not in dataframe.columns:
            return None
        if y_col and y_col not in dataframe.columns:
            return None

        # إنشاء الرسم البياني
        if chart_type == "bar":
            fig = px.bar(dataframe, x=x_col, y=y_col, title=title, template="plotly_dark")
        elif chart_type == "line":
            fig = px.line(dataframe, x=x_col, y=y_col, title=title, template="plotly_dark")
        elif chart_type == "pie":
            # للتجمع، خذ أول 10 قيم
            plot_df = dataframe.groupby(x_col)[y_col].sum().reset_index().head(10)
            fig = px.pie(plot_df, names=x_col, values=y_col, title=title, template="plotly_dark")
        else:
            return None

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,17,23,0.8)",
            font=dict(family="Cairo", color="#ccd6f6"),
        )
        return fig
        
    except Exception as e:
        print(f"Chart error: {str(e)}")  # للتشخيص
        return None

# Main Chat Function
def get_answer(question, dataframe):
    """الحصول على إجابة من Gemini"""
    try:
        # تحضير البيانات بشكل مبسط
        col_list = ", ".join(dataframe.columns.tolist()[:15])  # حدد عدد الأعمدة
        
        # إحصائيات مبسطة
        stats_summary = {}
        for col in dataframe.select_dtypes(include="number").columns[:5]:
            stats_summary[col] = {
                'mean': dataframe[col].mean(),
                'max': dataframe[col].max(),
                'min': dataframe[col].min()
            }
        
        prompt = (
            "أنت محلل بيانات خبير في سلاسل التوريد. أجب باللغة العربية.\n"
            f"الأعمدة المتاحة: {col_list}\n"
            f"الإحصائيات الأساسية: {json.dumps(stats_summary, default=str)}\n"
            f"السؤال: {question}\n\n"
            "قدم إجابة مختصرة ومفيدة تحتوي على الأرقام المطلوبة:"
        )

        response = generate_with_retry(client, "gemini-1.5-flash", prompt)
        return response.text
        
    except Exception as e:
        return f"⚠️ عذراً، حدث خطأ: {str(e)[:150]}\n\nيرجى المحاولة مرة أخرى."

# Main Chat Logic
if ask_clicked and user_question.strip():
    # إضافة سؤال المستخدم
    st.session_state.messages.append({"role": "user", "content": user_question})

    with st.spinner("🤖 جارٍ التحليل والمعالجة..."):
        # الحصول على الإجابة
        answer = get_answer(user_question, df)
        
        # محاولة إنشاء رسم بياني
        chart = try_generate_chart(user_question, df)

        # إضافة الرد
        msg = {"role": "assistant", "content": answer}
        if chart:
            msg["chart"] = chart
        
        st.session_state.messages.append(msg)

    st.rerun()

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("<p style='color:#4a5568; text-align:center; font-size:0.8rem;'>🤖 Powered by Gemini 1.5 Flash</p>", unsafe_allow_html=True)
with col2:
    st.markdown("<p style='color:#4a5568; text-align:center; font-size:0.8rem;'>📦 Supply Chain Intelligence</p>", unsafe_allow_html=True)
with col3:
    if st.button("🗑️ مسح المحادثة", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
