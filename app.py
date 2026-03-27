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
st.markdown("Ανάλυση μετοχών, κρυπτονομισμάτων και ETFs σε πραγματικό χρόνο")

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
elif category == "Κρυπτονομίσματα":
    default_symbols = "BTC-USD, ETH-USD"
else:
    default_symbols = "SPY, QQQ, GLD"

symbols_input = st.sidebar.text_input("Εισάγετε Σύμβολα (χωρισμένα με κόμμα):", value=default_symbols)

period_map = {
    "1 Εβδομάδα": "7d", "1 Μήνας": "1mo", "3 Μήνες": "3mo",
    "6 Μήνες": "6mo", "1 Χρόνος": "1y", "2 Χρόνια": "2y", "5 Χρόνια": "5y"
}
selected_period_label = st.sidebar.selectbox("Χρονική περίοδος:", list(period_map.keys()), index=4)
selected_period = period_map[selected_period_label]

load_data = st.sidebar.button("🔄 Φόρτωση Δεδομένων", type="primary")

# ============================================================
# ΣΥΝΑΡΤΗΣΕΙΣ ΛΗΨΗΣ ΔΕΔΟΜΕΝΩΝ
# ============================================================

@st.cache_data(ttl=3600)
def get_stock_data(symbol, period):
    try:
        ticker_obj = yf.Ticker(symbol)
        # Μέθοδος 1
        df = ticker_obj.history(period=period)
        
        # Μέθοδος 2 (Backup αν η πρώτη αποτύχει)
        if df.empty:
            df = yf.download(symbol, period=period, progress=False)
            
        if df.empty:
            return None, None
            
        # Καθαρισμός στηλών (για συμβατότητα με νέες εκδόσεις yfinance)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        return df, ticker_obj
    except Exception:
        return None, None

def calculate_metrics(df, ticker_obj):
    metrics = {}
    try:
        if df is None or df.empty: return metrics
        
        current_price = float(df['Close'].iloc[-1])
        start_price = float(df['Close'].iloc[0])
        roi = ((current_price - start_price) / start_price) * 100
        
        metrics['Τρέχουσα Τιμή'] = f"${current_price:.2f}"
        metrics['ROI (%)'] = f"{roi:+.2f}%"
        metrics['Υψηλό Περιόδου'] = f"${df['High'].max():.2f}"
        metrics['Χαμηλό Περιόδου'] = f"${df['Low'].min():.2f}"
        
        daily_returns = df['Close'].pct_change().dropna()
        metrics['Μεταβλητότητα (%)'] = f"{(daily_returns.std() * 100):.2f}%"
    except:
        pass
    return metrics

# ============================================================
# ΚΥΡΙΟ ΜΕΡΟΣ ΕΦΑΡΜΟΓΗΣ
# ============================================================

if load_data:
    symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]
    
    with st.spinner("Λήψη δεδομένων..."):
        data_dict = {}
        ticker_dict = {}
        errors = []
        
        for sym in symbols:
            df, ticker = get_stock_data(sym, selected_period)
            if df is not None and not df.empty:
                data_dict[sym] = df
                ticker_dict[sym] = ticker
            else:
                errors.append(sym)

    if errors:
        st.error(f"❌ Δεν βρέθηκαν δεδομένα για: {', '.join(errors)}. Δοκιμάστε ξανά σε λίγο ή ελέγξτε τα σύμβολα.")

    if data_dict:
        tab1, tab2, tab3 = st.tabs(["📊 Απόδοση", "🕯️ Candlesticks", "📋 Δείκτες"])
        
        with tab1:
            # Γράφημα Σύγκρισης
            fig = go.Figure()
            for sym, df in data_dict.items():
                norm = (df['Close'] / df['Close'].iloc[0]) * 100
                fig.add_trace(go.Scatter(x=df.index, y=norm, mode='lines', name=sym))
            fig.update_layout(title="Σύγκριση Απόδοσης (Βάση 100)", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            s_candle = st.selectbox("Επιλέξτε σύμβολο για ανάλυση:", list(data_dict.keys()))
            df_c = data_dict[s_candle]
            fig_c = go.Figure(data=[go.Candlestick(
                x=df_c.index, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close']
            )])
            fig_c.update_layout(title=f"Candlestick Chart - {s_candle}", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig_c, use_container_width=True)

        with tab3:
            for sym in data_dict:
                with st.expander(f"📊 Στατιστικά για {sym}", expanded=True):
                    m = calculate_metrics(data_dict[sym], ticker_dict[sym])
                    if m:
                        cols = st.columns(len(m))
                        for i, (k, v) in enumerate(m.items()):
                            cols[i].metric(label=k, value=v)
else:
    st.info("👈 Εισάγετε σύμβολα στο μενού και πατήστε το κουμπί για να ξεκινήσετε.")
