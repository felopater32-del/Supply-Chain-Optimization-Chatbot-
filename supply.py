import streamlit as st
import pandas as pd
from pandasai import SmartDataframe
from pandasai.llm import GoogleGemini
import os

st.set_page_config(page_title="AI Data Scientist", layout="wide")
st.title("🤖 Smart Supply Chain Dashboard")

# إعداد الـ LLM
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    llm = GoogleGemini(api_key=API_KEY)
except:
    st.error("⚠️ تأكد من إضافة المفتاح في الـ Secrets")

file_path = "Supply_Chain_Optimization.csv"

if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    # تفعيل خيار الحفظ التلقائي للرسومات عشان تظهر في Streamlit
    smart_df = SmartDataframe(df, config={"llm": llm, "save_charts": True})

    st.write("### عينة من البيانات:")
    st.dataframe(df.head(5))

    st.divider()

    st.subheader("📊 اطلب من الـ AI رسم بياني أو تحليل:")
    prompt = st.text_input("مثلاً: Draw a bar chart of the top 5 product types by price")

    if st.button("تنفيذ"):
        if prompt:
            with st.spinner("جاري معالجة البيانات..."):
                response = smart_df.chat(prompt)
                
                # عرض الرد (سواء كان نص أو مسار الصورة)
                if response:
                    st.write(response)
                    # لو الـ AI رسم صورة، المكتبة غالباً بتطلعها أوتوماتيك
                    # لو مظهرتش، قولي وهنضيف سطر عرض الصورة يدوياً
        else:
            st.warning("اكتب سؤالك أولاً")
else:
    st.error("❌ ملف البيانات غير موجود")
