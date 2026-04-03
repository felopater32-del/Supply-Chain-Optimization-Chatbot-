import streamlit as st
import pandas as pd
from google import genai

# 1. الـ API Key
API_KEY = "AIzaSyBZWpMlqty2iciVgr9f3n_953E5ipVPKB4"
client = genai.Client(api_key=API_KEY)

st.set_page_config(page_title="Supply Chain Analyst", layout="wide")
st.title("🤖 Supply Chain Excel Analyst")

# 2. تحميل البيانات
@st.cache_data
def load_data():
    # تأكد إن الملف مرفوع في الكود سبيس بنفس الاسم ده
        return pd.read_excel("Supply_Chain_Optimization.xlsx") 

        try:
            df = load_data()
                st.success("✅ تم تحميل البيانات بنجاح")
                    st.subheader("📊 عينة من البيانات")
                        st.dataframe(df.head(10))

                            # 3. الشات بوت
                                st.divider()
                                    user_question = st.text_input("❓ اسأل المحلل الذكي عن الجدول:")

                                        if st.button("تحليل") and user_question:
                                                with st.spinner("جاري التحليل..."):
                                                            # بناخد أول 30 سطر عشان الـ AI يفهم السياق
                                                                        context = df.head(30).to_string()
                                                                                    prompt = f"Data Context:\n{context}\n\nUser Question: {user_question}"

                                                                                                response = client.models.generate_content(
                                                                                                                model="gemini-1.5-flash",
                                                                                                                                contents=prompt
                                                                                                                                            )
                                                                                                                                                        
                                                                                                                                                                    st.info(f"🤖 رد المحلل الذكي: \n\n {response.text}")

                                                                                                                                                                    except Exception as e:
                                                                                                                                                                        st.error(f"❌ مشكلة: تأكد من رفع ملف الـ Excel. الخطأ: {e}")
                                                                        