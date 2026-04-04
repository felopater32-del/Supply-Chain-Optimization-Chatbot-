import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px
import os

# 1. إعداد الصفحة بشكل عريض واحترافي
st.set_page_config(page_title="Supply Chain AI Analyst", layout="wide")
st.title("📊 Supply Chain Smart Dashboard")

# 2. الربط مع الـ AI (استخدام موديل 1.5 المستقر)
try:
    # جلب المفتاح من الـ Secrets الخاصة بـ Streamlit
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
    # استخدام المسار الكامل للموديل لتجنب خطأ NotFound
    model = genai.GenerativeModel('models/gemini-1.5-flash')
except Exception as e:
    st.error(f"⚠️ خطأ في إعداد الـ AI: {e}")

# 3. قراءة ملف البيانات
file_path = "Supply_Chain_Optimization.csv"

if os.path.exists(file_path):
    # قراءة البيانات
    df = pd.read_csv(file_path)
    
    # صف المؤشرات الرئيسية (Metrics)
    st.write("### 📈 Key Performance Indicators")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Rows", len(df))
    m2.metric("Unique Products", df.iloc[:, 0].nunique())
    
    # محاولة حساب الإيرادات لو العمود موجود
    revenue_col = [col for col in df.columns if 'revenue' in col.lower()]
    if revenue_col:
        m3.metric("Total Revenue", f"${df[revenue_col[0]].sum():,.0f}")
    else:
        m3.metric("Total Revenue", "N/A")
        
    m4.metric("Columns Count", len(df.columns))

    st.divider()

    # 4. الرسوم البيانية التفاعلية (Plotly)
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔝 Top 10 Items")
        top_items = df.iloc[:, 0].value_counts().head(10)
        fig1 = px.bar(top_items, x=top_items.index, y=top_items.values, 
                     color=top_items.values, template="plotly_dark")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("📦 Data Distribution")
        # اختيار ثاني عمود غالباً بيكون Category أو Shipping
        if len(df.columns) > 1:
            pie_data = df.iloc[:, 1].value_counts().head(5)
            fig2 = px.pie(values=pie_data.values, names=pie_data.index, 
                         hole=0.4, template="plotly_dark")
            st.plotly_chart(fig2, use_container_width=True)

    # 5. قسم المحلل الذكي (الدردشة)
    st.divider()
    st.subheader("🤖 اسأل المحلل الذكي (AI Analysis)")
    user_query = st.text_input("❓ اكتب سؤالك عن البيانات هنا:")

    if st.button("تحليل الآن"):
        if user_query:
            with st.spinner("جاري تحليل البيانات..."):
                try:
                    # إرسال ملخص إحصائي كامل للموديل ليفهم البيانات
                    data_summary = df.describe(include='all').to_string()
                    
                    full_prompt = f"""
                    You are an expert Supply Chain Data Analyst.
                    Here is a statistical summary of the dataset:
                    {data_summary}
                    
                    User Question: {user_query}
                    
                    Task:
                    - Analyze the data summary to provide an accurate answer.
                    - Identify any visible trends or risks.
                    - Provide your response in ARABIC in a clear, professional way.
                    """
                    
                    response = model.generate_content(full_prompt)
                    st.info(response.text)
                except Exception as e:
                    st.error(f"❌ حدث خطأ أثناء التحليل: {e}")
        else:
            st.warning("يرجى كتابة سؤال أولاً")

    # خيار لعرض البيانات الخام
    if st.checkbox("عرض جدول البيانات"):
        st.dataframe(df)

else:
    st.error(f"⚠️ الملف {file_path} غير موجود على GitHub. تأكد من رفعه بنفس الاسم.")
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
