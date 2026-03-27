import yfinance as yf
import mplfinance as mpf
import pandas as pd
import matplotlib.pyplot as plt

# -------------------
# Assets
# -------------------
market_assets = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "DAX": "^GDAXI",
    "SSE Composite (Κίνα)": "000001.SS",
    "Gold": "GC=F",
    "Oil": "CL=F"
}

crypto_assets = {
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
    "Solana": "SOL-USD",
    "XRP": "XRP-USD"
}

assets = list(market_assets.items()) + list(crypto_assets.items())
period = "3mo"
interval = "1d"

# -------------------
# Download + clean
# -------------------
def download_data(ticker):
    data = yf.download(ticker, period=period, interval=interval, auto_adjust=True)
    if data.empty:
        return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    for col in ["Open","High","Low","Close"]:
        if col not in data.columns:
            data[col] = data["Close"] if "Close" in data.columns else 0
    data = data[["Open","High","Low","Close"]].apply(pd.to_numeric, errors='coerce')
    data.dropna(inplace=True)
    return data

# -------------------
# Load all data
# -------------------
plots = []
names = []
for name, ticker in assets:
    df = download_data(ticker)
    if not df.empty:
        plots.append(df)
        names.append(name)

# -------------------
# Interactive navigation
# -------------------
index = 0
fig, ax = plt.subplots(figsize=(10,6))
plt.ion()  # interactive mode ON

def show_plot(i):
    ax.clear()
    mpf.plot(plots[i], type='candle', style='yahoo', mav=(20,50), volume=False, ax=ax, show_nontrading=False)
    ax.set_title(names[i], fontsize=16)
    fig.canvas.draw()

def on_key(event):
    global index
    if event.key in ['right','down','enter',' ']:
        index = (index + 1) % len(plots)
    elif event.key in ['left','up']:
        index = (index - 1) % len(plots)
    show_plot(index)

# Show first plot
show_plot(index)
fig.canvas.mpl_connect('key_press_event', on_key)
plt.show(block=True)