import streamlit as st
import datetime
import pandas as pd
from py_vollib.black_scholes.implied_volatility import implied_volatility
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import griddata

@st.cache_data
def get_data():
    url = "https://drive.google.com/uc?export=download&id=10TOLs-kNUbVjiESm6SuYHNEXX2J-3lla"
    return pd.read_csv(url,
        dtype = {"C_LAST": float, "P_LAST": float, "UNDERLYING_LAST": float, "STRIKE": float},
        na_values = [" "],
        skipinitialspace = True,
        parse_dates = ["QUOTE_DATE", "EXPIRE_DATE"]
    )

def get_volatility(row):
    try:
        return implied_volatility(
            price = row["C_LAST"],
            S = row["UNDERLYING_LAST"],
            K = row["STRIKE"],
            t = row["T_EXP"],
            r = risk_free_rate,
            flag = "c"
        )
    except Exception:
        return float("nan")

df = get_data()

st.title("Volatility Tool")
st.sidebar.header('Options (Ticker: AAPL)')

risk_free_rate = st.sidebar.number_input(
    'Risk-Free Rate (min: 0.005, max: 0.15)',
    value = 0.025,
    format = "%.4f",
    min_value = 0.005,
    max_value = 0.15
)

y_axis_select = st.sidebar.selectbox(
    'Select Y-axis:',
    ('Strike Price', 'Moneyness')
)

show_data_pts = st.sidebar.checkbox("Overlay Raw Data")

input_date = st.sidebar.date_input(
    "Select Date (01/3/23 to 31/3/23)", 
    datetime.date(2023, 3, 31),
    min_value = datetime.date(2023, 3, 1),
    max_value = datetime.date(2023, 3, 31)
)

show_underlying = st.sidebar.checkbox("Show Underlying Price")

df.dropna(inplace = True)
df["QUOTE_DATE"] = df["QUOTE_DATE"].dt.date
df["EXPIRE_DATE"] = df["EXPIRE_DATE"].dt.date
df["T_EXP"] = (df["EXPIRE_DATE"] - df["QUOTE_DATE"]).apply(lambda x: x.days / 365)
df = df[df["T_EXP"] > 0]

if input_date.weekday() == 5:
    input_date = input_date - datetime.timedelta(days = 1)
elif input_date.weekday() == 6:
    input_date = input_date - datetime.timedelta(days = 2)

filtered = df[df["QUOTE_DATE"] == input_date].copy()
filtered = filtered[filtered["C_LAST"] > 0]
filtered["C_IMPVOL"] = filtered.apply(get_volatility, axis = 1)
filtered.dropna(inplace = True)
filtered = filtered[(filtered["C_IMPVOL"] > 0.01) & (filtered["C_IMPVOL"] < 2.0)]
filtered["C_IV_PCT"] = 100 * filtered["C_IMPVOL"]
filtered["MONEYNESS"] = filtered["STRIKE"] / filtered["UNDERLYING_LAST"]
filtered = filtered[(filtered["MONEYNESS"] >= 0.5) & (filtered["MONEYNESS"] <= 1.5)]

X = filtered["T_EXP"].values
if y_axis_select == 'Strike Price':
    Y = filtered["STRIKE"].values
    yaxis_title = "Strike Price ($)"
else:
    Y = filtered["MONEYNESS"].values
    yaxis_title = "Moneyness"
Z = filtered["C_IV_PCT"].values
Xarr = np.linspace(X.min(), X.max(), 100)
Yarr = np.linspace(Y.min(), Y.max(), 100)
Xgrid, Ygrid = np.meshgrid(Xarr, Yarr)
Zgrid = griddata((X, Y), Z, (Xgrid, Ygrid), method = 'linear', rescale = True)

fig = go.Figure()

fig.add_trace(go.Surface(
    x = Xgrid,
    y = Ygrid,
    z = Zgrid,
    colorscale = "Viridis",
    name = "Implied Volatility Surface",
    showscale = True
))

 
fig.update_layout(
    title = "Implied Volatility Surface for AAPL",
    scene = dict(
        xaxis_title = "Time to Expiration (Years)",
        yaxis_title = yaxis_title,
        zaxis_title = "Implied Volatility (%)",
    ),
    autosize = False,
    width = 1000,
    height = 800,
    margin = dict(l=50, r=50, b=50, t=80)
)

if show_data_pts:
    fig.add_trace(go.Scatter3d(
        x = X,
        y = Y,
        z = Z,
        mode = 'markers',
        marker = dict(
            size = 3,
            color = 'red',
            opacity = 1.0
        ),
        name = "Observed Data"
    ))

if show_underlying and y_axis_select == "Strike Price":
    underlying_price = filtered.iloc[0]["UNDERLYING_LAST"]
    planeX_vals = [X.min(), X.max()]
    planeZ_vals = [Z.min(), Z.max()]
    planeX_grid, planeZ_grid = np.meshgrid(planeX_vals, planeZ_vals)
    planeY_grid = np.full_like(planeX_grid, fill_value = underlying_price)

    fig.add_trace(go.Surface(
        x = planeX_grid,
        y = planeY_grid,
        z = planeZ_grid,
        showscale = False,
        opacity = 0.5,
        colorscale = "Reds",
        hoverinfo = 'skip'
    ))

st.plotly_chart(fig)

st.subheader("Notes:", divider = False)
st.markdown("""
- Assumed stock pays no dividend.
- Volatilities calculated for call options.
- By assuming do dividend, American calls are equal in value to European calls.
- Volatility surface created by triangulating the input data and performing barycentric interpolation.
- Data from [Kaggle Apple Options dataset](https://www.kaggle.com/datasets/kylegraupe/aapl-options-data-2016-2020). 
- To limit data usages, time range limited to March, 2023.
""")
st.write("---")
st.markdown("Code by Ajinkya Bhalerao")