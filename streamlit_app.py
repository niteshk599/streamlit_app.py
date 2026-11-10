# 1. Install dependencies
!pip install streamlit yfinance pandas plotly pyngrok -q

# 2. Write the app code to a file
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

print("✅ App code written successfully!")

# 3. Ask for Token Securely
import getpass
print("\n👉 Go to https://dashboard.ngrok.com/get-started/your-authtoken to get your token.")
# This will create an input box in Colab for you to paste the token
NGROK_TOKEN = getpass.getpass("Paste your ngrok token here and press Enter: ")

# 4. Start the app and create a public link
from pyngrok import ngrok
import subprocess
import time
import os

if not NGROK_TOKEN:
    print("❌ ERROR: No token provided.")
else:
    try:
        ngrok.set_auth_token(NGROK_TOKEN.strip())
        
        # Kill any previous instances to prevent port errors
        os.system("pkill streamlit")
        
        # Run Streamlit in background
        subprocess.Popen(["streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"])
        time.sleep(5)

        # Generate public URL
        public_url = ngrok.connect(8501).public_url
        print("\n\n" + "="*50)
        print(f"✅ YOUR APP IS LIVE! Click here: {public_url}")
        print("="*50 + "\n\n")
    except Exception as e:
        print(f"❌ Authentication failed. Error: {e}")
