import streamlit as st
import datetime
import pandas as pd

url = "https://drive.google.com/uc?export=download&id=10TOLs-kNUbVjiESm6SuYHNEXX2J-3lla"
df = pd.read_csv(url)

st.title("Volatility Tool")

st.sidebar.header('Options')

risk_free_rate = st.sidebar.number_input(
    'Risk-Free Rate (e.g. 0.025 for 2.5%)',
    value=0.025,
    format="%.4f",
    min_value=0.005,
    max_value=0.10
)

y_axis_select = st.sidebar.selectbox(
    'Select Y-axis:',
    ('Strike Price', 'Moneyness')
)

show_data_pts = st.sidebar.checkbox("Overlay Raw Data")

input_date = st.sidebar.date_input(
    "Select Date", 
    datetime.date(2023, 3, 31),
    min_value=datetime.date(2021, 1, 4),
    max_value=datetime.date(2023, 3, 31)
)

st.write(df.head())