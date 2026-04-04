import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import os

# ========================
# 1. إعدادات الصفحة
# ========================
st.set_page_config(page_title="Supply Chain Analyst", page_icon="📊", layout="wide")

# ========================
# 2. إعداد الـ AI (نسخة مستقرة تماماً)
# ========================
@st.cache_resource
def load_genai_model():
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        # استخدام gemini-pro مباشرة لتفادي مشاكل v1beta مع النسخ الجديدة
        return genai.GenerativeModel('gemini-pro')
    except Exception as e:
        st.error(f"⚠️ خطأ في الربط: {e}")
        return None

model = load_genai_model()

# ========================
# 3. تحميل البيانات
# ========================
@st.cache_data
def load_data():
    if os.path.exists("Supply_Chain_Optimization.csv"):
        return pd.read_csv("Supply_Chain_Optimization.csv")
    return None

df = load_data()

# ========================
# 4. واجهة المستخدم والتصميم
# ========================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; }
    .chat-bubble { background-color: #1e2a45; padding: 20px; border-radius: 10px; border-right: 5px solid #00d4ff; color: #ffffff; }
</style>
""", unsafe_allow_html=True)

st.title("🚀 المحلل الذكي لسلاسل الإمداد")

if df is not None:
    # عرض العدادات
    c1, c2, c3 = st.columns(3)
    c1.metric("عدد السجلات", len(df))
    c2.metric("المنتجات", df.iloc[:, 0].nunique())
    c3.metric("الأعمدة", len(df.columns))

    st.divider()

    # قسم السؤال والجواب
    st.subheader("🤖 اسأل عن بياناتك")
    user_query = st.text_input("اكتب سؤالك هنا:", placeholder="مثلاً: ما هي المدن الأكثر طلباً للمنتجات؟")

    if st.button("تحليل الآن ✨"):
        if user_query and model:
            with st.spinner("جاري التحليل..."):
                try:
                    # نبعت أول 30 سطر كـ Context عشان نضمن السرعة وعدم تجاوز الـ Tokens
                    data_context = df.head(30).to_string()
                    prompt = f"حلل البيانات التالية:\n{data_context}\n\nالسؤال: {user_query}\nأجب بالعربية بوضوح."
                    
                    response = model.generate_content(prompt)
                    st.markdown(f"<div class='chat-bubble'>{response.text}</div>", unsafe_allow_html=True)
                    
                    # رسم بياني تلقائي
                    fig = px.pie(df.head(10), names=df.columns[0], values=df.select_dtypes(include='number').columns[0], 
                                 title="توزيع أولي للبيانات", template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"❌ حدث خطأ: {e}")
        else:
            st.warning("تأكد من كتابة سؤالك.")
    
    with st.expander("🔍 معاينة البيانات"):
        st.dataframe(df)
else:
    st.error("⚠️ ملف Supply_Chain_Optimization.csv غير موجود في GitHub.")
