#source ./venv/bin/activate
import requests
import keys
import streamlit as st
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import pandas as pd
import json

trading_client = TradingClient(keys.apiKey(), keys.secretKey(), paper=True)

timeInForce = {"Good To Cancel(GTC)":TimeInForce.GTC,"Day(DAY)":TimeInForce.DAY,"Fill Or Kill(FOK)":TimeInForce.FOK,"Immediate Or Cancel(IOC)":TimeInForce.IOC,"At The Open(OPG)":TimeInForce.OPG,"At The Close(CLS)":TimeInForce.CLS}

url = "https://paper-api.alpaca.markets/v2/account"
headers = {
    "accept": "application/json",
    "APCA-API-KEY-ID": keys.apiKey(),
    "APCA-API-SECRET-KEY": keys.secretKey()
}
response = requests.get(url, headers=headers)
print(response.text)

tif = st.selectbox(
    ("Time in Force"),
    ("Good To Cancel(GTC)","Day(DAY)","Fill Or Kill(FOK)","Immediate Or Cancel(IOC)","At The Open(OPG)","At The Close(CLS)",)
)
def OrderRequest(sym,qty,side):
    return MarketOrderRequest(
    symbol=sym,
    qty=qty,
    side=side,
    time_in_force=timeInForce[tif]
    )

sym = st.text_input("Enter a symbol", help="Type in a ticker/symbol").upper()
qty = st.number_input("Enter a qty", help="You can trade fractionally, but minimum is 0.10 shares and only DAY orders are supported",step = 0.10)
orderSide = st.selectbox(
    ("Order Side"),
    ("Buy", "Sell")
)

def marketOrder():
    trading_client.submit_order(
    order_data=OrderRequest(sym,qty,OrderSide.BUY if orderSide == "Buy" else OrderSide.SELL)
    )

portfolio = trading_client.get_all_positions()
    
st.button("Send Order", on_click=marketOrder)


st.write(portfolio)
order = trading_client.get_orders() 

orders_dicts = [o.dict() for o in order]

basic_cols = ["symbol", "side", "qty", "status", "time_in_force"]
label_map = {col: col.replace("_", " ").title() for col in basic_cols}

rows = [
    { label_map[k]: order[k] for k in basic_cols }
    for order in orders_dicts
]

st.table(rows)
