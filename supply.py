import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px
import os

# 1. إعدادات الصفحة والـ AI
st.set_page_config(page_title="AI Smart Dashboard", layout="wide")
st.title("🤖 Supply Chain Smart Analyst")

try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("⚠️ تأكد من الـ API Key في الـ Secrets")

# 2. تحميل البيانات
file_path = "Supply_Chain_Optimization.csv"

if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    
    # --- القائمة الجانبية (Sidebar) للتحكم ---
    st.sidebar.header("⚙️ لوحة التحكم")
    show_data = st.sidebar.checkbox("عرض جدول البيانات")
    chart_type = st.sidebar.selectbox("اختر نوع الرسم البياني الأساسي", ["Bar Chart", "Line Chart", "Scatter Plot"])

    # --- عرض الإحصائيات السريعة ---
    cols = st.columns(4)
    cols[0].metric("إجمالي السجلات", len(df))
    cols[1].metric("عدد الأعمدة", len(df.columns))
    # هنا بنفترض إن عندك عمود مبيعات أو تكلفة (عدل اسم العمود حسب ملفك)
    if 'Revenue' in df.columns:
        cols[2].metric("إجمالي الإيرادات", f"{df['Revenue'].sum():,.0f}")
    
    st.divider()

    # --- قسم الرسوم البيانية التفاعلية ---
    st.subheader("📊 التحليل البصري الديناميكي")
    col_x = st.selectbox("اختر المحور الأفقي (X)", df.columns)
    col_y = st.selectbox("اختر المحور الرأسي (Y)", df.select_dtypes(include=['number']).columns)

    if chart_type == "Bar Chart":
        fig = px.bar(df.head(50), x=col_x, y=col_y, color=col_x, template="plotly_dark")
    elif chart_type == "Line Chart":
        fig = px.line(df.head(50), x=col_x, y=col_y, template="plotly_dark")
    else:
        fig = px.scatter(df.head(50), x=col_x, y=col_y, color=col_x, template="plotly_dark")
    
    st.plotly_chart(fig, use_container_width=True)

    # --- قسم الـ AI (العقل المفكر) ---
    st.divider()
    st.subheader("🧠 اسأل المحلل الذكي (الدردشة)")
    query = st.text_input("مثلاً: حلل لي أداء الموردين واقترح تحسينات؟")

    if st.button("تحليل بالذكاء الاصطناعي"):
        if query:
            with st.spinner("جاري قراءة البيانات والتحليل..."):
                # بنبعت للـ AI وصف للأعمدة وأول كام سطر
                data_summary = df.describe().to_string()
                context = df.head(20).to_string()
                prompt = f"""
                أنت خبير سلاسل إمداد. إليك ملخص البيانات:
                {data_summary}
                وعينة من البيانات:
                {context}
                بناءً على هذه البيانات، أجب على السؤال التالي بشكل احترافي ومنظم:
                السؤال: {query}
                """
                response = model.generate_content(prompt)
                st.markdown(response.text)
        else:
            st.warning("من فضلك اكتب سؤالك")

    if show_data:
        st.subheader("📋 البيانات الكاملة")
        st.write(df)

else:
    st.error("❌ لم يتم العثور على ملف البيانات")
