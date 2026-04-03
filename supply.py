import streamlit as st
import pandas as pd
from google import genai
import os

# 1. إعداد الـ API
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    st.error("⚠️ تأكد من إضافة GOOGLE_API_KEY في الـ Secrets")

st.set_page_config(page_title="Supply Chain AI", layout="wide")
st.title("🤖 Supply Chain AI Analyst")

# 2. قراءة الملف
file_path = "Supply_Chain_Optimization.csv"

if os.path.exists(file_path):
    try:
        df = pd.read_csv(file_path)
        st.success("✅ تم تحميل البيانات بنجاح")
        st.dataframe(df.head(50))
        
        st.divider()
        user_question = st.text_input("❓ اسأل المحلل الذكي عن بياناتك:")
        if st.button("تحليل"):
            if user_question:
                with st.spinner("جاري التحليل..."):
                    context = df.head(30).to_string()
                    prompt = f"Data:\n{context}\nQuestion: {user_question}"
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )
                    st.info(response.text)
            else:
                st.warning("يرجى كتابة سؤال أولاً.")
    except Exception as e:
        st.error(f"❌ خطأ في قراءة الملف: {e}")
else:
    st.error(f"⚠️ الملف {file_path} غير موجود.")
