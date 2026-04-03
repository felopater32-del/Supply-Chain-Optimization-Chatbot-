
import streamlit as st
import pandas as pd
import pyodbc
from google import genai
import os

# ========================
# Configure Gemini API
# ========================
API_KEY = " "
# set environment variable instead of configure
# genai.Client auto picks up GOOGLE_API_KEY from env

os.environ["GOOGLE_API_KEY"] = API_KEY

# ========================
# Create GenAI Client
# ========================
client = genai.Client()

# ========================
# Streamlit Setup
# ========================
st.set_page_config(page_title="Hospitals Chatbot", page_icon="🤖", layout="wide")
st.title("🤖 Hospitals Chatbot with Gemini (Google GenAI)")

st.markdown("""
اسأل عن بيانات الوظائف من قاعدة البيانات، و Gemini هيرد عليك.
""")

# ========================
# SQL Connection
# ========================
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=cleaning_c_db;"
    "TrustServerCertificate=yes;"
    "Trusted_Connection=yes;"
)

df_clean_hospitals = pd.read_sql("SELECT * FROM clean_hospitals", conn)

st.subheader("Hospitals Table Preview")
st.dataframe(df_clean_hospitals.head(10), use_container_width=True)

# ========================
# Chatbot Input
# ========================
user_question = st.text_input("❓ اسأل عن الوظائف:")

if st.button("Ask") and user_question:
    with st.spinner("Thinking..."):
        try:
            # prepare context
            context = df_clean_hospitals.to_string()
            prompt = f"Answer user based on Hospitals data:\n{context}\nUser question: {user_question}"

            # ========================
            # Gemini text generation call
            # ========================
            response = client.models.generate_content(
                model="gemini-2.5-flash",       # Model name
                contents=prompt,                # prompt text
            )

            answer = response.text
            st.markdown(f"*🤖 إجابة الشات بوت:* {answer}")

        except Exception as e:
            st.error(f"❌ حدث خطأ أثناء طلب الإجابة: {e}")

بس اعدل فيه اسم ال داتا بيز و اسم الجدول 
و اضيف ال project ID