#source ./venv/bin/activate
from streamlit_autorefresh import st_autorefresh
import streamlit as st
import keys
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import datetime



# ─── Non‑UI setup ──────────────────────────────────────────────────────────────
trading_client = TradingClient(keys.apiKey(), keys.secretKey(), paper=True)
timeInForce = {
    "Good To Cancel(GTC)": TimeInForce.GTC,
    "Day(DAY)":            TimeInForce.DAY,
    "Fill Or Kill(FOK)":   TimeInForce.FOK,
    "Immediate Or Cancel(IOC)": TimeInForce.IOC,
    "At The Open(OPG)":    TimeInForce.OPG,
    "At The Close(CLS)":   TimeInForce.CLS,
}

def OrderRequest(sym, qty, side, tif):
    return MarketOrderRequest(
        symbol=sym, qty=qty, side=side, time_in_force=timeInForce[tif]
    )

def marketOrder():
    side = OrderSide.BUY if st.session_state.orderSide=="Buy" else OrderSide.SELL
    req  = OrderRequest(
        st.session_state.sym,
        st.session_state.qty,
        side,
        st.session_state.tif

    )
    trading_client.submit_order(order_data=req)

# ─── Static UI (keys preserve state across reruns) ────────────────────────────

st.sidebar.selectbox("Time in Force", list(timeInForce), key="tif")
st.sidebar.text_input("Symbol", key="sym",    help="Ticker").upper()
st.sidebar.number_input("Qty",    key="qty",   min_value=0.1, step=0.1,
                        help="Min 0.1 shares")
st.sidebar.selectbox("Side", ["Buy","Sell"], key="orderSide")
st.sidebar.button("Send Order", on_click=marketOrder)

# ─── Dynamic Refresh ───────────────────────────────────────────────────────────
screen = st.sidebar.radio("View", ["Dashboard", "Chart"])
if screen == "Dashboard":
    

    pnl_ph      = st.empty()
    orders_ph   = st.empty()
    positions_ph= st.empty()
    

    # ─── Fetch + Populate Placeholders ─────────────────────────────────────────────
    account = trading_client.get_account()
    bal_chg = float(account.equity) - float(account.last_equity)
    if bal_chg >= 0:
        pnl_ph.markdown(f"**Today's P/L:** :green[$ {bal_chg:.2f}]")
    else:
        pnl_ph.markdown(f"**Today's P/L:** :red[$ {bal_chg:.2f}]")

    orders    = [o.dict() for o in trading_client.get_orders()]
    positions = [p.dict() for p in trading_client.get_all_positions()]

    orders_ph.markdown("### Orders").table([
        {
        "Symbol": o["symbol"],
        "Side":   o["side"],
        "Qty":    o["qty"],
        "Status": o["status"],
        "TIF":    o["time_in_force"]
        }
        for o in orders
    ])

    positions_ph.markdown("### Positions").table([
        {
        "Symbol": p["symbol"],
        "Qty":    p["qty"],
        "Side":   p["side"],
        }
        for p in positions
    ])
elif screen == "Chart":
    import streamlit.components.v1 as components
    import yfinance as yf
    import pandas as pd
    import altair as alt
    import datetime
    from datetime import timedelta
    from datetime import datetime
    @st.cache_data
    def fetch_stock(sym):
       return yf.download(sym,datetime.now()-timedelta(days=7))
    try:
        ticker = yf.Ticker(st.session_state.sym)
        data = (fetch_stock(st.session_state.sym))
        data["Date"] = data.index
        data = data[["Date","Open","Close","Volume"]]
        max_date = max(data["Date"])
        min_date = max_date - timedelta(days=7)
        filtered = data[(data["Date"] >= min_date) & (data["Date"] <= max_date)]
        min_price = float(filtered['Close'].min())
        max_price = float(filtered['Close'].max())
        diff = (max_price - min_price) * 0.10



        def chart(filtered):
            chart = alt.Chart(filtered).mark_line().encode(
                x=alt.X('Date:T', axis=alt.Axis(title='Date')),
                y=alt.Y('Close:Q',scale=alt.Scale(domain=[min_price - diff, max_price + diff]), axis=alt.Axis(title='Close Price'))
            )
            return chart
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("<h4 style='margin-bottom:0;'>Current Price</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:30px;  font-weight:bold;'>${ticker.info['currentPrice']}</p>", unsafe_allow_html=True)
            st.markdown("<h4 style='margin-bottom:0;'>Previous Close</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:30px;  font-weight:bold;'>${ticker.info['previousClose']}</p>", unsafe_allow_html=True)

        with col2:
            st.markdown("<h4 style='margin-bottom:0;'>Day High</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:30px;  font-weight:bold;'>${ticker.info['dayHigh']}</p>", unsafe_allow_html=True)
            st.markdown("<h4 style='margin-bottom:0;'>Day Low</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:30px; font-weight:bold;'>${ticker.info['dayLow']}</p>", unsafe_allow_html=True)

        with col3:
            st.markdown("<h4 style='margin-bottom:0;'>Dividend Yield</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:30px; font-weight:bold;'>{ticker.info['dividendYield']}%</p>", unsafe_allow_html=True)
            st.markdown("<h4 style='margin-bottom:0;'>Market Cap</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:30px; font-weight:bold;'>${ticker.info['marketCap']}</p>", unsafe_allow_html=True)



        st.altair_chart(chart(filtered), use_container_width=True)
        st.dataframe(data)
    except ValueError:
        st.write("Enter a symbol with the sidebar")

    


    
    
    


   

