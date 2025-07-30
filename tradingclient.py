#source ./venv/bin/activate
from streamlit_autorefresh import st_autorefresh
import streamlit as st
import keys
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
import datetime
import random



# ─── Non‑UI setup ──────────────────────────────────────────────────────────────
trading_client = TradingClient(st.secrets["api_key"], st.secrets["secret_key"], paper=True)
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
@st.dialog("Confirm Liquidation")
def liq_all():
    if "liquidation_code" not in st.session_state:
        st.session_state.liquidation_code = random.randint(100000, 999999)

    code = st.session_state.liquidation_code
    st.write(f"Enter the following liquidation code: {code}")
    reason = st.text_input("Enter the code")

    if st.button("Submit Liquidation") and reason == str(code):
        trading_client.close_all_positions(True)
        del st.session_state.liquidation_code  
        st.success("Your Liquidation order has been submitted, you may now close this window")
        
st.sidebar.button("LIQUIDATE ALL POSITONS AND ORDERS", on_click=liq_all)
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
    import streamlit as st
    import yfinance as yf
    import pandas as pd
    import altair as alt
    from datetime import datetime, timedelta
    import pytz
    from streamlit_autorefresh import st_autorefresh
    import streamlit.components.v1 as components

    def market_is_open():
        eastern = pytz.timezone("US/Eastern")
        now = datetime.now(eastern)
        is_weekday = now.weekday() < 5
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        return is_weekday and market_open <= now <= market_close
    components.html("""<!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container">
  <div class="tradingview-widget-container__widget"></div>
  <div class="tradingview-widget-copyright"><a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank"></a></div>
  <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
  {
  "symbols": [
    {
      "proName": "FOREXCOM:SPXUSD",
      "title": "S&P 500 Index"
    },
    {
      "proName": "NYSE:BLK",
      "title": "Blackrock Inc."
    },
    {
      "proName": "NASDAQ:AAPL",
      "title": "Apple Inc."
    },
    {
      "proName": "NASDAQ:TSLA",
      "title": "Tesla"
    },
    {
      "proName": "NASDAQ:META",
      "title": "Meta Inc."
    },
    {
      "proName": "NASDAQ:NVDA",
      "title": "Nvidia"
    }
  ],
  "colorTheme": "dark",
  "locale": "en",
  "largeChartUrl": "",
  "isTransparent": false,
  "showSymbolLogo": true,
  "displayMode": "adaptive"
}
  </script>
</div>
<!-- TradingView Widget END -->""")

    try:
        symbol = st.session_state.sym
        ticker = yf.Ticker(symbol)

        if market_is_open():
            st_autorefresh(interval=500, key="live_refresh") #refreshes each time

            if "live_chart_data" not in st.session_state:
                st.session_state.live_chart_data = pd.DataFrame(columns=["Time", "Price"])

            now = datetime.now() 
            price = ticker.fast_info["last_price"]
            new_row = pd.DataFrame({"Time": [now], "Price": [price]})
            st.session_state.live_chart_data = pd.concat([st.session_state.live_chart_data, new_row], ignore_index=True)
            st.session_state.live_chart_data = st.session_state.live_chart_data.tail(50)
            chart_data = st.session_state.live_chart_data.sort_index(ascending=False)
        else:
            hist = ticker.history(period="1d", interval="15m").reset_index()
            chart_data = hist[["Datetime", "Close"]].rename(columns={"Datetime": "Time", "Close": "Price"}).tail(50).sort_index(ascending=False)
            st.info("Market is closed. Showing static 15-minute chart from today.")

        min_price = float(chart_data["Price"].min())
        max_price = float(chart_data["Price"].max())
        diff = (max_price - min_price) * 0.10

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("<h4 style='margin-bottom:0;'>Open Price</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:30px; font-weight:bold;'>${ticker.info['open']}</p>", unsafe_allow_html=True)
            st.markdown("<h4 style='margin-bottom:0;'>Previous Close</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:30px; font-weight:bold;'>${ticker.info['previousClose']}</p>", unsafe_allow_html=True)

        with col2:
            st.markdown("<h4 style='margin-bottom:0;'>Day High</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:30px; font-weight:bold;'>${ticker.info['dayHigh']}</p>", unsafe_allow_html=True)
            st.markdown("<h4 style='margin-bottom:0;'>Day Low</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:30px; font-weight:bold;'>${(ticker.info['dayLow']):.2f}</p>", unsafe_allow_html=True)

        with col3:
            st.markdown("<h4 style='margin-bottom:0;'>Dividend Yield</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:30px; font-weight:bold;'>{ticker.info['dividendYield']}%</p>", unsafe_allow_html=True)
            st.markdown("<h4 style='margin-bottom:0;'>Market Cap</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='font-size:30px; font-weight:bold;'>${ticker.info['marketCap']}</p>", unsafe_allow_html=True)

        chart = alt.Chart(chart_data).mark_line().encode(
            x="Time:T",
            y=alt.Y("Price:Q", scale=alt.Scale(domain=[min_price - diff, max_price + diff]))
        ).properties(height=400)

        st.altair_chart(chart, use_container_width=True)
        st.dataframe(chart_data)

    except Exception:
        st.warning("Please enter a valid symbol in the sidebar.")

