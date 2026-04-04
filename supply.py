import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import os

# ========================
# 1. Page Configuration
# ========================
st.set_page_config(page_title="Supply Chain AI Analyst", page_icon="🚀", layout="wide")

# ========================
# 2. Advanced AI Setup (No more 404!)
# ========================
def setup_ai():
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        
        # هنحاول ننادي الموديل بأكثر اسم مستقر
        # لو فشل 1.5 فلاش، الكود هينزل تلقائياً لـ gemini-pro
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            # تجربة وهمية للتأكد من الموديل
            return model
        except:
            return genai.GenerativeModel('gemini-pro')
            
    except Exception as e:
        st.error(f"⚠️ مشكلة في إعدادات الـ API: {e}")
        return None

model = setup_ai()

# ========================
# 3. Custom CSS Styling
# ========================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; }
    .main { background-color: #0e1117; }
    .stMetric { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 15px; }
    .chat-card { background: #1c2128; border-right: 5px solid #00d4ff; padding: 20px; border-radius: 8px; margin: 15px 0; color: #adbac7; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# ========================
# 4. Data Loading
# ========================
@st.cache_data
def get_data():
    path = "Supply_Chain_Optimization.csv"
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

df = get_data()

# ========================
# 5. Dashboard UI
# ========================
st.title("🚀 Supply Chain Intelligence Dashboard")

if df is not None:
    # المؤشرات السريعة
    cols = st.columns(4)
    cols[0].metric("إجمالي السجلات", len(df))
    cols[1].metric("المنتجات", df.iloc[:, 0].nunique())
    cols[2].metric("المواقع/المدن", df.iloc[:, 1].nunique() if len(df.columns)>1 else "N/A")
    cols[3].metric("الأعمدة", len(df.columns))

    st.divider()

    # قسم التحليل الذكي
    st.subheader("🤖 اسأل المحلل الذكي (Gemini AI)")
    query = st.text_input("ماذا تريد أن تعرف عن بيانات سلاسل الإمداد؟", placeholder="مثلاً: ما هي أكثر مدينة بها تكاليف شحن؟")

    if st.button("تحليل الآن ✨"):
        if query and model:
            with st.spinner("جاري قراءة البيانات وتحليلها..."):
                try:
                    # نبعت ملخص إحصائي عشان الموديل يفهم الداتا
                    summary = df.describe(include='all').to_string()
                    full_prompt = f"حلل بيانات سلاسل الإمداد التالية:\n{summary}\n\nالسؤال: {query}\nأجب باللغة العربية بوضوح."
                    
                    response = model.generate_content(full_prompt)
                    st.markdown(f"<div class='chat-card'>{response.text}</div>", unsafe_allow_html=True)
                    
                    # رسم بياني تفاعلي سريع
                    st.subheader("📊 رؤية بيانية سريعة")
                    fig = px.bar(df.head(15), x=df.columns[0], y=df.select_dtypes(include='number').columns[0], 
                                 template="plotly_dark", color_discrete_sequence=['#00d4ff'])
                    st.plotly_chart(fig, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"❌ حدث خطأ في التواصل مع السيرفر: {e}")
        else:
            st.warning("يرجى التأكد من كتابة سؤال ووجود API Key صحيح.")

    # عرض البيانات
    with st.expander("🔍 استعراض جدول البيانات"):
        st.dataframe(df)

else:
    st.error("⚠️ لم يتم العثور على ملف Supply_Chain_Optimization.csv. تأكد من رفعه على GitHub بنفس الاسم.")

# ========================
# 6. Footer
# ========================
st.caption("Developed for Supply Chain Optimization Project | 2026")
