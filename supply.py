import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import os

# ========================
# Page Config
# ========================
st.set_page_config(page_title="Supply Chain Intelligence", page_icon="🚀", layout="wide")

# ========================
# إعداد الـ AI (التعديل الجوهري هنا)
# ========================
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    # تحديد الموديل بالمسار الكامل وبدون v1beta لضمان التوافق
    model =genai.GenerativeModel('gemini-1.5-flash') 
except Exception as e:
    st.error(f"⚠️ Error: {e}")

# ========================
# تحميل البيانات
# ========================
@st.cache_data
def load_data():
    file_name = "Supply_Chain_Optimization.csv"
    if os.path.exists(file_name):
        return pd.read_csv(file_name)
    return pd.DataFrame()

df = load_data()

# ========================
# تصميم الواجهة (CSS)
# ========================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; }
    .stMetric { background: #1a1f2e; padding: 15px; border-radius: 10px; border: 1px solid #2d3550; }
    .chat-bot { background: #1e2a45; padding: 15px; border-radius: 12px; margin: 10px 0; border-left: 5px solid #00d4ff; color: white; }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Supply Chain Intelligence Dashboard")

if not df.empty:
    # عرض الـ KPIs
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("إجمالي السجلات", len(df))
    with m2: st.metric("المنتجات الفريدة", df.iloc[:, 0].nunique())
    with m3: st.metric("أعمدة البيانات", len(df.columns))

    st.divider()

    # شات بوت التحليل
    st.subheader("🤖 اسأل المحلل الذكي")
    user_input = st.text_input("اكتب سؤالك هنا (بالعربي أو الإنجليزي):")
    
    if st.button("تحليل الآن ✨"):
        if user_input:
            with st.spinner("جاري فحص البيانات..."):
                try:
                    # إرسال عينة منظمة للـ AI
                    summary = df.describe(include='all').to_string()
                    prompt = f"حلل بيانات سلاسل الإمداد التالية:\n{summary}\n\nالسؤال: {user_input}\nأجب باللغة العربية بشكل احترافي."
                    
                    response = model.generate_content(prompt)
                    st.markdown(f"<div class='chat-bot'>{response.text}</div>", unsafe_allow_html=True)
                    
                    # رسم بياني بسيط للتوضيح
                    fig = px.histogram(df, x=df.columns[0], template="plotly_dark", title="توزيع البيانات")
                    st.plotly_chart(fig, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"❌ حدث خطأ أثناء التحدث مع Gemini: {e}")
        else:
            st.warning("برجاء إدخال سؤال أولاً")

    if st.checkbox("عرض جدول البيانات"):
        st.dataframe(df)
else:
    st.error("❌ لم يتم العثور على ملف Supply_Chain_Optimization.csv")
