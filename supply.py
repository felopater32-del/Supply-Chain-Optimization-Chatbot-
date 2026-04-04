import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px
import os

# إعداد الصفحة
st.set_page_config(page_title="Supply Chain AI Analyst", layout="wide")
st.title("📊 Supply Chain AI Analyst Dashboard")

# إعداد الـ AI
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
    # استخدام المسار الكامل لتجنب خطأ NotFound
    model = genai.GenerativeModel('models/gemini-1.5-flash')
except Exception as e:
    st.error(f"⚠️ تأكد من إعداد المفتاح في Secrets: {e}")

# قراءة الملف
file_path = "Supply_Chain_Optimization.csv"

if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    
    # صف المؤشرات (Metrics)
    st.write("### 📈 Key Metrics")
    m1, m2, m3 = st.columns(3)
    m1.metric("إجمالي السجلات", len(df))
    m2.metric("عدد المنتجات", df.iloc[:, 0].nunique())
    m3.metric("عدد الأعمدة", len(df.columns))

    st.divider()

    # الرسوم البيانية
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔝 Top Products")
        top_items = df.iloc[:, 0].value_counts().head(10)
        fig1 = px.bar(top_items, template="plotly_dark", color=top_items.values)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("📦 Data Distribution")
        if len(df.columns) > 1:
            pie_data = df.iloc[:, 1].value_counts().head(5)
            fig2 = px.pie(values=pie_data.values, names=pie_data.index, hole=0.4, template="plotly_dark")
            st.plotly_chart(fig2, use_container_width=True)

    # قسم الشات بوت
    st.divider()
    st.subheader("🤖 اسأل المحلل الذكي")
    user_query = st.text_input("❓ ماذا تريد أن تعرف عن سلاسل الإمداد الخاصة بك؟")

    if st.button("حلل الآن"):
        if user_query:
            with st.spinner("جاري التحليل..."):
                try:
                    data_summary = df.describe(include='all').to_string()
                    prompt = f"Analyze this supply chain data summary:\n{data_summary}\nQuestion: {user_query}\nAnswer in Arabic."
                    response = model.generate_content(prompt)
                    st.info(response.text)
                except Exception as e:
                    st.error(f"❌ حدث خطأ: {e}")
else:
    st.error("⚠️ لم يتم العثور على الملف. تأكد من رفعه باسم Supply_Chain_Optimization.csv")
