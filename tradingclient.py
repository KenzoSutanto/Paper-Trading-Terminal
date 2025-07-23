#source ./venv/bin/activate
from streamlit_autorefresh import st_autorefresh
import streamlit as st
import keys
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce



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
    st_autorefresh(interval=10000, key="data_refresh")

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
html = """
    <div class="tradingview-widget-container">
    <!-- force the container to be tall -->
    <div id="tv_chart_container" style="height:600px; width:100%;"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
        new TradingView.widget({
        container_id: "tv_chart_container",
        autosize: true,
        symbol: "NASDAQ:AAPL",
        interval: "60",
        timezone: "Asia/Singapore",
        theme: "Light",
        style: "1",
        toolbar_bg: "#f1f3f6",
        hide_side_toolbar: false,
        allow_symbol_change: true,
        withdateranges: true
        });
    </script>
    </div>
    """

    # specify a matching height here too
components.html(html, height=600, scrolling=True)
