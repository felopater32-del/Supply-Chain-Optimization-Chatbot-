import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px
import os

# 1. إعداد الصفحة
st.set_page_config(page_title="Supply Chain Analyst", layout="wide")
st.title("📊 Supply Chain AI Dashboard")

# 2. إعداد الـ AI
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"⚠️ مشكلة في الـ API Key: {e}")

# 3. قراءة الملف
file_path = "Supply_Chain_Optimization.csv"

if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    
    # عرض سريع للبيانات
    st.subheader("📋 ملخص البيانات")
    col1, col2 = st.columns(2)
    col1.metric("إجمالي السجلات", len(df))
    col2.metric("عدد المنتجات", df.iloc[:, 0].nunique())
    
    st.divider()

    # 4. قسم الشات
    st.subheader("🤖 اسأل المحلل الذكي")
    user_query = st.text_input("❓ اكتب سؤالك هنا:")

    if st.button("تحليل الآن"):
        if user_query:
            with st.spinner("جاري التحليل..."):
                try:
                    # نبعت أول 50 سطر كعينة بسيطة
                    context = df.head(50).to_string()
                    full_prompt = f"إليك عينة من بيانات سلاسل الإمداد:\n{context}\n\nالسؤال: {user_query}\nأجب باللغة العربية."
                    
                    response = model.generate_content(full_prompt)
                    st.success(response.text)
                except Exception as e:
                    st.error(f"❌ حدث خطأ في الـ AI: {e}")
        else:
            st.warning("يرجى كتابة سؤال")
    
    if st.checkbox("عرض جدول البيانات"):
        st.dataframe(df)

else:
    st.error(f"⚠️ لم يتم العثور على ملف {file_path}")
