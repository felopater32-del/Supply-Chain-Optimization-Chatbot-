import streamlit as st
import pandas as pd
from pandasai import SmartDataframe
from pandasai.llm import GoogleGemini
import os

st.set_page_config(page_title="AI Data Scientist", layout="wide")
st.title("🤖 PandasAI: Smart Supply Chain Analyst")

# 1. إعداد الـ LLM (Gemini) داخل PandasAI
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    llm = GoogleGemini(api_key=API_KEY)
except:
    st.error("⚠️ تأكد من إضافة المفتاح في الـ Secrets")

# 2. تحميل البيانات
file_path = "Supply_Chain_Optimization.csv"

if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    
    # تحويل الـ DataFrame العادي لـ Smart Dataframe
    smart_df = SmartDataframe(df, config={"llm": llm})

    st.write("### عينة من البيانات:")
    st.dataframe(df.head(5))

    st.divider()

    # 3. صندوق الدردشة الذكي
    st.subheader("📊 اسأل الـ AI ليرسم أو يحلل:")
    prompt = st.text_input("مثلاً: 'Draw a bar chart of top 5 products by revenue' أو 'ماهي أعلى 5 مدن في التكلفة؟'")

    if st.button("تنفيذ الأمر"):
        if prompt:
            with st.spinner("جاري التفكير والرسم..."):
                # هنا السحر: المكتبة هي اللي بتقرر تطلع نص أو رسمة
                response = smart_df.chat(prompt)
                
                # عرض النتيجة (سواء كانت نص أو صورة الرسم البياني)
                if response:
                    st.write(response)
                    # ملاحظة: PandasAI بتحفظ الصورة في مجلد exports وتظهرها أوتوماتيك
        else:
            st.warning("اكتب سؤالك أو أمر الرسم أولاً")

else:
    st.error("❌ ملف البيانات غير موجود")
