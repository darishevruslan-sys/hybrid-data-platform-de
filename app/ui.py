import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="E-com Operations Portal", layout="wide")

st.title("🚀 E-commerce Operations Portal")

# Боковая панель с живой метрикой
st.sidebar.header("Real-time Stats")
revenue_placeholder = st.sidebar.empty()

# Основная часть: Поиск пользователя
st.header("🔎 Customer Insight")
user_id = st.number_input("Enter User ID", min_value=1, max_value=100, value=1)

if st.button("Get Purchase History"):
    response = requests.get(f"http://fastapi_app:8000/api/v1/user/{user_id}/history")
    if response.status_code == 200:
        data = response.json()
        if data['history']:
            st.write(f"Showing history for **{data['history'][0]['name']}** from **{data['history'][0]['city']}**")
            df = pd.DataFrame(data['history'])
            st.table(df)
        else:
            st.warning("No history found for this user.")

# Цикл для обновления выручки в реальном времени
while True:
    try:
        rev_resp = requests.get("http://fastapi_app:8000/api/v1/revenue").json()
        revenue_placeholder.metric("Total Revenue (Live)", f"${rev_resp['total_revenue']:,.2f}")
    except:
        pass
    time.sleep(5)