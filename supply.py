import streamlit as st
import pandas as pd
from google import genai
import os

# 1. إعداد الـ API باستخدام Secrets لحماية المفتاح
# تأكد انك ضفت GOOGLE_API_KEY في Settings بتاع Streamlit Cloud
API_KEY = st.secrets["GOOGLE_API_KEY"]
client = genai.Client(api_key=API_KEY)

st.set_page_config(page_title="Supply Chain AI Analyst", layout="wide")
st.title("🤖 Supply Chain AI Analyst")

# 2. قراءة الملف
file_path = "Supply_Chain_Optimization.csv"

if os.path.exists(file_path):
    try:
        df = pd.read_csv(file_path)
        st.success("✅ تم تحميل البيانات بنجاح")
        st.dataframe(df.head(10))

        # 3. الشات بوت
        st.divider()
        user_question = st.text_input("❓ اسأل المحلل الذكي عن بياناتك:")

        if st.button("تحليل"):
            if user_question:
                with st.spinner("جاري التحليل..."):
                    context = df.head(30).to_string()
                    prompt = f"Data:\n{context}\nQuestion: {user_question}"
                    response = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=prompt
                    )
                    st.info(response.text)
            else:
                st.warning("يرجى كتابة سؤال أولاً.")
    except Exception as e:
        st.error(f"❌ خطأ في قراءة الملف: {e}")
else:
    st.error(f"⚠️ الملف {file_path} غير موجود في GitHub.")
