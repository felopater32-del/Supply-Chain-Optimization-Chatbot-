import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px
import os

# إعداد الصفحة
st.set_page_config(page_title="Supply Chain Analyst", layout="wide")
st.title("📊 Supply Chain AI Dashboard")

# إعداد الـ AI
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
    # استخدام الاسم المباشر بدون مسارات إضافية
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"⚠️ مشكلة في الـ API Key: {e}")

# قراءة الملف
file_path = "Supply_Chain_Optimization.csv"

if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    
    # عرض سريع للبيانات
    st.subheader("📋 ملخص البيانات")
    col1, col2 = st.columns(2)
    col1.metric("إجمالي السجلات", len(df))
    col2.metric("عدد المنتجات", df.iloc[:, 0].nunique())
    
    st.divider()

    # قسم الشات
    st.subheader("🤖 اسأل المحلل الذكي")
    user_query = st.text_input("❓ اكتب سؤالك هنا:")

    if st.button("تحليل الآن"):
        if user_query:
            with st.spinner("جاري التحليل..."):
                try:
                    # نبعت أول 50 سطر كعينة بسيطة عشان ميحصلش Crash
                    context = df.head(50).to_string()
                    full_prompt = f"إليك عينة من بيانات سلاسل الإمداد:\n{context}\n\nالسؤال: {user_query}\nأجب باللغة العربية."
                    
                    response = model.generate_content(full_prompt)
                    st.success(response.text)
                except Exception as e:
                    st.error(f"❌ حدث خطأ: {e}")
        else:
            st.warning("يرجى كتابة سؤال")
    
    if st.checkbox("عرض جدول البيانات"):
        st.dataframe(df)
else:
    st.error(f"⚠️ لم يتم العثور على ملف {file_path}")
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
