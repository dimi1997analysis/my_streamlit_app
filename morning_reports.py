import yfinance as yf
import mplfinance as mpf
import pandas as pd

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

period = "3mo"
interval = "1d"

# -------------------
# Download + prepare
# -------------------
def download_data(ticker):
    data = yf.download(ticker, period=period, interval=interval, auto_adjust=True)
    
    if data.empty:
        return pd.DataFrame()
    
    # Αν είναι MultiIndex, κρατάμε μόνο level 0
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    # Φτιάχνουμε Open/High/Low/Close αν δεν υπάρχουν
    for col in ["Open", "High", "Low", "Close"]:
        if col not in data.columns:
            data[col] = data["Close"] if "Close" in data.columns else 0

    # Επιλέγουμε μόνο τις 4 στήλες
    data = data[["Open", "High", "Low", "Close"]]

    # Μετατρέπουμε σε float
    data = data.apply(pd.to_numeric, errors='coerce')
    data.dropna(inplace=True)
    
    return data

# -------------------
# Plot
# -------------------
def plot_candlestick(data, title):
    if data.empty:
        print(f"Δεν υπάρχουν δεδομένα για {title}")
        return
    mpf.plot(
        data,
        type="candle",
        style="yahoo",
        title=title,
        volume=False,
        mav=(20,50),
        figsize=(10,6)
    )

# -------------------
# Plot market assets
# -------------------
print("\n--- Χρηματιστηριακοί δείκτες & commodities ---\n")
for name, ticker in market_assets.items():
    print(f"Φόρτωση δεδομένων για: {name}")
    data = download_data(ticker)
    if not data.empty:
        last_close = data['Close'].iloc[-1].item()
        print(f"Τελευταία τιμή {name}: {last_close:.2f}\n")
        plot_candlestick(data, name)
    else:
        print(f"Δεν υπάρχουν δεδομένα για τον δείκτη {name}\n")

# -------------------
# Plot crypto
# -------------------
print("\n--- Κρυπτονομίσματα ---\n")
for name, ticker in crypto_assets.items():
    print(f"Φόρτωση δεδομένων για: {name}")
    data = download_data(ticker)
    if not data.empty:
        last_close = data['Close'].iloc[-1].item()
        print(f"Τελευταία τιμή {name}: {last_close:.2f}\n")
        plot_candlestick(data, name)
    else:
        print(f"Δεν υπάρχουν δεδομένα για το crypto {name}\n")