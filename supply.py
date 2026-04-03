import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px
import os

# إعداد الصفحة
st.set_page_config(page_title="Supply Chain AI Dashboard", layout="wide")
st.title("📊 Supply Chain AI Analytics Dashboard")

# إعداد الـ AI
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("⚠️ تأكد من إضافة GOOGLE_API_KEY في الـ Secrets")

# قراءة الملف
file_path = "Supply_Chain_Optimization.csv"

if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    
    # صف الإحصائيات العلوي (Metrics)
    st.write("### 📈 Key Performance Indicators")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("إجمالي السجلات", len(df))
    m2.metric("عدد المنتجات", df.iloc[:, 0].nunique())
    if 'Revenue' in df.columns:
        m3.metric("إجمالي الإيرادات", f"${df['Revenue'].sum():,.0f}")
    if 'Stock levels' in df.columns:
        m4.metric("متوسط المخزون", f"{df['Stock levels'].mean():.1f}")

    st.divider()

    # قسم الرسوم البيانية التفاعلية
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔝 Top 10 Products")
        top_10 = df.iloc[:, 0].value_counts().head(10)
        fig1 = px.bar(top_10, x=top_10.index, y=top_10.values, color=top_10.values,
                     labels={'x': 'Product', 'y': 'Count'}, template="plotly_dark")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("🚚 Shipping Methods Distribution")
        if 'Shipping methods' in df.columns:
            ship_data = df['Shipping methods'].value_counts()
            fig2 = px.pie(values=ship_data.values, names=ship_data.index, hole=0.4,
                         template="plotly_dark", color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig2, use_container_width=True)

    # قسم المحلل الذكي (الدردشة)
    st.divider()
    st.subheader("🤖 اسأل المحلل الذكي عن تفاصيل البيانات")
    user_query = st.text_input("مثلاً: ما هي نقاط الضعف في سلاسل الإمداد بناءً على هذه الأرقام؟")

    if st.button("تحليل بواسطة AI"):
        if user_query:
            with st.spinner("جاري تحليل البيانات..."):
                # نبعت للـ AI ملخص إحصائي دقيق
                data_summary = df.describe(include='all').to_string()
                prompt = f"إليك ملخص لبيانات سلاسل إمداد:\n{data_summary}\n\nالسؤال: {user_query}\nأجب كخبير تحليل بيانات."
                response = model.generate_content(prompt)
                st.info(response.text)
        else:
            st.warning("يرجى كتابة سؤالك")
else:
    st.error("⚠️ لم يتم العثور على ملف Supply_Chain_Optimization.csv")
