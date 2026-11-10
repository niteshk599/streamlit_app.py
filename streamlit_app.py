# 1. Install dependencies and download Cloudflare
!pip install streamlit yfinance pandas plotly -q
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared
!chmod +x cloudflared

# 2. Write the app code
app_code = """
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Apex Trading App", layout="wide")
st.title("🏛️ Apex Multi-Asset Trading App")

ticker = st.sidebar.selectbox("Asset", ["BTC-USD", "GC=F", "AAPL", "XAUUSD"])
timeframe = st.sidebar.selectbox("Timeframe", ["1h", "4h", "1d"])
period = "1mo" if timeframe != "1d" else "1y"

@st.cache_data(ttl=300)
def get_data(ticker, period, interval):
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df['EMA_20'] = df['Close'].rolling(20).mean()
    df['EMA_50'] = df['Close'].rolling(50).mean()
    return df

df = get_data(ticker, period, timeframe)

if not df.empty:
    latest = df.iloc[-1]
    price = float(latest['Close'])
    trend = "BULLISH" if price > latest['EMA_50'] else "BEARISH"
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Price", f"${price:,.2f}")
    col2.metric("Trend", trend)
    col3.metric("50 EMA", f"${latest['EMA_50']:,.2f}")
    
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], line=dict(color='green', width=1.5), name='20 EMA'))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='red', width=1.5), name='50 EMA'))
    fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("🤖 Algorithmic Trade Setup")
    if trend == "BULLISH":
        st.success("**BUY SCENARIO**\\n- **Trigger:** Price holds above 20 EMA (${:,.2f})\\n- **Stop Loss:** 50 EMA (${:,.2f})".format(latest['EMA_20'], latest['EMA_50']))
    else:
        st.error("**SELL SCENARIO**\\n- **Trigger:** Rejection at 50 EMA (${:,.2f})\\n- **Stop Loss:** Above 20 EMA (${:,.2f})".format(latest['EMA_50'], latest['EMA_20']))
"""

with open("app.py", "w") as f:
    f.write(app_code)

# 3. Start Streamlit in the background
import subprocess
import time
import re

# Kill any previous streamlit instances
!pkill streamlit

# Start Streamlit
subprocess.Popen(["streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"])
time.sleep(3)

# 4. Start Cloudflare Tunnel in background
print("Starting Cloudflare Tunnel...")
!./cloudflared tunnel --url http://localhost:8501 &> cf_logs.txt &
time.sleep(5)

# 5. Extract and print the live URL
with open("cf_logs.txt", "r") as f:
    logs = f.read()
    urls = re.findall(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', logs)
    if urls:
        print("\n" + "="*60)
        print(f"✅ YOUR APP IS LIVE! Click here: {urls[0]}")
        print("="*60 + "\n")
    else:
        print("❌ Error: Could not generate link. Please try running the cell again.")
