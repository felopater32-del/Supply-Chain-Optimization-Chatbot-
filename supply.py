import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# 1. إعداد الصفحة
st.set_page_config(page_title="Supply Chain Analyst", layout="wide")
st.title("📊 Supply Chain AI Dashboard")

# 2. إعداد الـ AI (الطريقة المستقرة)
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
    # استخدام اسم الموديل بدون كلمة models/ وبدون تحديد إصدار بيتا
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"⚠️ مشكلة في الـ API: {e}")

# 3. تحميل البيانات
file_path = "Supply_Chain_Optimization.csv"

if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    st.success("✅ تم تحميل البيانات بنجاح")
    
    # عرض إحصائيات سريعة
    st.metric("إجمالي السجلات", len(df))
    
    st.divider()

    # 4. قسم الشات بوت
    st.subheader("🤖 اسأل المحلل الذكي")
    user_query = st.text_input("❓ اكتب سؤالك هنا (مثلاً: حلل لي أداء الشحن):")

    if st.button("تحليل الآن"):
        if user_query:
            with st.spinner("جاري التحليل..."):
                try:
                    # نبعت ملخص البيانات في البرومبت
                    data_info = df.head(20).to_string()
                    full_prompt = f"إليك بيانات سلاسل إمداد:\n{data_info}\n\nالسؤال: {user_query}\nأجب باللغة العربية."
                    
                    # طلب الرد
                    response = model.generate_content(full_prompt)
                    st.info(response.text)
                except Exception as e:
                    st.error(f"❌ خطأ في الرد: {e}")
        else:
            st.warning("اكتب سؤالك أولاً")
            
    if st.checkbox("عرض الجدول"):
        st.dataframe(df)
else:
    st.error(f"⚠️ الملف {file_path} غير موجود.")
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
