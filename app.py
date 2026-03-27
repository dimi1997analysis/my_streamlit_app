import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# --- ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(
    page_title="Αξιολόγηση Επενδύσεων",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Εφαρμογή Αξιολόγησης Επενδύσεων")
st.markdown("Ανάλυση μετοχών, κρυπτονομισμάτων, ETFs και ομολόγων σε πραγματικό χρόνο")

# ============================================================
# ΠΛΕΥΡΙΚΟ ΜΕΝΟΥ
# ============================================================
st.sidebar.header("⚙️ Επιλογές")

category = st.sidebar.selectbox(
    "Κατηγορία επένδυσης:",
    ["Μετοχές", "Κρυπτονομίσματα", "ETFs / Ομόλογα"]
)

if category == "Μετοχές":
    default_symbols = "AAPL, MSFT, GOOGL"
    hint = "π.χ. AAPL, MSFT, TSLA"
elif category == "Κρυπτονομίσματα":
    default_symbols = "BTC-USD, ETH-USD"
    hint = "π.χ. BTC-USD, ETH-USD"
else:
    default_symbols = "SPY, QQQ, TLT"
    hint = "π.χ. SPY, GLD"

symbols_input = st.sidebar.text_input(f"Σύμβολα ({hint}):", value=default_symbols)

period_map = {
    "1 Εβδομάδα": "7d", "1 Μήνας": "1mo", "3 Μήνες": "3mo",
    "6 Μήνες": "6mo", "1 Χρόνος": "1y", "2 Χρόνια": "2y", "5 Χρόνια": "5y"
}
selected_period_label = st.sidebar.selectbox("Χρονική περίοδος:", list(period_map.keys()), index=4)
selected_period = period_map[selected_period_label]

load_data = st.sidebar.button("🔄 Φόρτωση Δεδομένων", type="primary")

# ============================================================
# ΣΥΝΑΡΤΗΣΕΙΣ (Με Caching για ταχύτητα στο Cloud)
# ============================================================

@st.cache_data(ttl=3600)  # Κρατάει τα δεδομένα στη μνήμη για 1 ώρα
def get_stock_data(symbol, period):
    try:
        ticker_obj = yf.Ticker(symbol)
        df = ticker_obj.history(period=period)
        if df.empty:
            return None, None
        return df, ticker_obj
    except Exception as e:
        return None, None

def calculate_metrics(df, ticker_obj):
    metrics = {}
    if df is None or df.empty: return metrics
    
    current_price = df['Close'].iloc[-1]
    start_price = df['Close'].iloc[0]
    roi = ((current_price - start_price) / start_price) * 100
    
    metrics['Τρέχουσα Τιμή'] = f"${current_price:.2f}"
    metrics['ROI (%)'] = f"{roi:+.2f}%"
    metrics['Υψηλό Περιόδου'] = f"${df['High'].max():.2f}"
    metrics['Χαμηλό Περιόδου'] = f"${df['Low'].min():.2f}"
    
    daily_returns = df['Close'].pct_change().dropna()
    metrics['Μεταβλητότητα (%)'] = f"{(daily_returns.std() * 100):.2f}%"

    try:
        info = ticker_obj.info
        if 'marketCap' in info:
            cap = info['marketCap']
            metrics['Κεφαλαιοποίηση'] = f"${cap/1e9:.2f}B" if cap > 1e9 else f"${cap/1e6:.2f}M"
    except: pass
    return metrics

# --- Συναρτήσεις Γραφημάτων ---
def plot_price_chart(data_dict):
    fig = go.Figure()
    for symbol, df in data_dict.items():
        normalized = (df['Close'] / df['Close'].iloc[0]) * 100
        fig.add_trace(go.Scatter(x=df.index, y=normalized, mode='lines', name=symbol))
    fig.update_layout(title="Σύγκριση Απόδοσης (Βάση 100)", height=450)
    return fig

def plot_candlestick(symbol, df):
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.update_layout(title=f"Candlestick Chart — {symbol}", xaxis_rangeslider_visible=False)
    return fig

# ============================================================
# ΚΥΡΙΟ ΜΕΡΟΣ
# ============================================================

if load_data:
    symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]
    
    with st.spinner("Γίνεται λήψη δεδομένων από Yahoo Finance..."):
        data_dict, ticker_dict, errors = {}, {}, []
        for sym in symbols:
            df, ticker = get_stock_data(sym, selected_period)
            if df is not None:
                data_dict[sym] = df
                ticker_dict[sym] = ticker
            else:
                errors.append(sym)

    if errors:
        st.error(f"❌ Αδυναμία εύρεσης δεδομένων για: {', '.join(errors)}. Ελέγξτε αν τα σύμβολα είναι σωστά (π.χ. AAPL αντί για Apple).")

    if data_dict:
        tab1, tab2, tab3 = st.tabs(["📊 Γραφήματα", "📋 Δείκτες", "📥 Εξαγωγή"])
        
        with tab1:
            st.plotly_chart(plot_price_chart(data_dict), use_container_width=True)
            selected_sym = st.selectbox("Λεπτομερές γράφημα (Candlestick):", list(data_dict.keys()))
            st.plotly_chart(plot_candlestick(selected_sym, data_dict[selected_sym]), use_container_width=True)

        with tab2:
            for sym in data_dict:
                with st.expander(f"📌 {sym} - Στατιστικά", expanded=True):
                    m = calculate_metrics(data_dict[sym], ticker_dict[sym])
                    cols = st.columns(len(m))
                    for i, (k, v) in enumerate(m.items()):
                        cols[i].metric(label=k, value=v)

        with tab3:
            for sym, df in data_dict.items():
                st.download_button(f"⬇️ Download {sym} CSV", df.to_csv().encode('utf-8'), f"{sym}.csv", "text/csv")
else:
    st.info("👈 Συμπληρώστε τα σύμβολα αριστερά και πατήστε 'Φόρτωση Δεδομένων'")
