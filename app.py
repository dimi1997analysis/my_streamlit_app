# ============================================================
# ΕΦΑΡΜΟΓΗ ΑΞΙΟΛΟΓΗΣΗΣ ΕΠΕΝΔΥΣΕΩΝ
# Βιβλιοθήκες που χρησιμοποιούμε:
#   - streamlit : φτιάχνει την web εφαρμογή
#   - yfinance  : κατεβάζει τιμές από Yahoo Finance
#   - plotly    : κάνει τα γραφήματα
#   - pandas    : διαχειρίζεται τα δεδομένα σε πίνακες
# ============================================================

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

# --- ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(
    page_title="Αξιολόγηση Επενδύσεων",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Εφαρμογή Αξιολόγησης Επενδύσεων")
st.markdown("Ανάλυση μετοχών, κρυπτονομισμάτων, ETFs και ομολόγων σε πραγματικό χρόνο")

# ============================================================
# ΠΛΕΥΡΙΚΟ ΜΕΝΟΥ (Sidebar) - εδώ ο χρήστης βάζει τις επιλογές
# ============================================================
st.sidebar.header("⚙️ Επιλογές")

# Επιλογή κατηγορίας επένδυσης
category = st.sidebar.selectbox(
    "Κατηγορία επένδυσης:",
    ["Μετοχές", "Κρυπτονομίσματα", "ETFs / Ομόλογα"]
)

# Ανάλογα με την κατηγορία, δείχνουμε διαφορετικά παραδείγματα
if category == "Μετοχές":
    default_symbols = "AAPL, MSFT, GOOGL"
    hint = "π.χ. AAPL, MSFT, TSLA, AMZN"
elif category == "Κρυπτονομίσματα":
    default_symbols = "BTC-USD, ETH-USD"
    hint = "π.χ. BTC-USD, ETH-USD, SOL-USD"
else:
    default_symbols = "SPY, QQQ, TLT"
    hint = "π.χ. SPY, QQQ, GLD, TLT"

# Πεδίο εισαγωγής συμβόλων
symbols_input = st.sidebar.text_input(
    f"Σύμβολα ({hint}):",
    value=default_symbols
)

# Επιλογή χρονικής περιόδου
period_map = {
    "1 Εβδομάδα": "7d",
    "1 Μήνας": "1mo",
    "3 Μήνες": "3mo",
    "6 Μήνες": "6mo",
    "1 Χρόνος": "1y",
    "2 Χρόνια": "2y",
    "5 Χρόνια": "5y"
}
selected_period_label = st.sidebar.selectbox("Χρονική περίοδος:", list(period_map.keys()), index=4)
selected_period = period_map[selected_period_label]

# Κουμπί για φόρτωση δεδομένων
load_data = st.sidebar.button("🔄 Φόρτωση Δεδομένων", type="primary")

# ============================================================
# ΣΥΝΑΡΤΗΣΕΙΣ (Functions) - επαναχρησιμοποιήσιμα κομμάτια κώδικα
# ============================================================

def get_stock_data(symbol, period):
    """
    Κατεβάζει ιστορικά δεδομένα για ένα σύμβολο.
    Επιστρέφει DataFrame με τιμές ή None αν υπάρξει σφάλμα.
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        return df, ticker
    except Exception as e:
        return None, None


def calculate_metrics(df, ticker_obj):
    """
    Υπολογίζει βασικούς δείκτες από τα δεδομένα.
    """
    metrics = {}

    if df is None or df.empty:
        return metrics

    # Τρέχουσα και αρχική τιμή
    current_price = df['Close'].iloc[-1]
    start_price = df['Close'].iloc[0]

    # Συνολική απόδοση (ROI)
    roi = ((current_price - start_price) / start_price) * 100
    metrics['Τρέχουσα Τιμή'] = f"${current_price:.2f}"
    metrics['ROI (%)'] = f"{roi:+.2f}%"

    # Υψηλό / Χαμηλό περιόδου
    metrics['Υψηλό Περιόδου'] = f"${df['High'].max():.2f}"
    metrics['Χαμηλό Περιόδου'] = f"${df['Low'].min():.2f}"

    # Μέσος όγκος συναλλαγών
    metrics['Μέσος Όγκος'] = f"{df['Volume'].mean():,.0f}"

    # Μεταβλητότητα (τυπική απόκλιση ημερήσιων αποδόσεων)
    daily_returns = df['Close'].pct_change().dropna()
    volatility = daily_returns.std() * 100
    metrics['Μεταβλητότητα (ημερήσια %)'] = f"{volatility:.2f}%"

    # Πληροφορίες από Yahoo Finance (για μετοχές)
    try:
        info = ticker_obj.info
        if 'trailingPE' in info and info['trailingPE']:
            metrics['P/E Ratio'] = f"{info['trailingPE']:.2f}"
        if 'marketCap' in info and info['marketCap']:
            cap = info['marketCap']
            if cap >= 1e12:
                metrics['Κεφαλαιοποίηση'] = f"${cap/1e12:.2f}T"
            elif cap >= 1e9:
                metrics['Κεφαλαιοποίηση'] = f"${cap/1e9:.2f}B"
            else:
                metrics['Κεφαλαιοποίηση'] = f"${cap/1e6:.2f}M"
        if 'dividendYield' in info and info['dividendYield']:
            metrics['Μερίσματα (%)'] = f"{info['dividendYield']*100:.2f}%"
    except:
        pass  # Αν δεν υπάρχουν πληροφορίες, συνεχίζουμε

    return metrics


def plot_price_chart(data_dict, period_label):
    """
    Δημιουργεί γράφημα τιμών για όλα τα σύμβολα μαζί.
    Κανονικοποιεί στο 100 για να μπορούμε να συγκρίνουμε.
    """
    fig = go.Figure()

    for symbol, df in data_dict.items():
        if df is not None and not df.empty:
            # Κανονικοποίηση: αρχική τιμή = 100 (για σύγκριση)
            normalized = (df['Close'] / df['Close'].iloc[0]) * 100
            fig.add_trace(go.Scatter(
                x=df.index,
                y=normalized,
                mode='lines',
                name=symbol,
                hovertemplate=f'<b>{symbol}</b><br>Τιμή: %{{y:.2f}}<br>Ημερομηνία: %{{x|%d/%m/%Y}}<extra></extra>'
            ))

    fig.update_layout(
        title=f"Σύγκριση Απόδοσης (Βάση = 100) — {period_label}",
        xaxis_title="Ημερομηνία",
        yaxis_title="Κανονικοποιημένη Τιμή (Βάση 100)",
        hovermode='x unified',
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig


def plot_candlestick(symbol, df):
    """
    Δημιουργεί κηροπηγοειδές γράφημα (candlestick) για ένα σύμβολο.
    """
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name=symbol
    )])

    fig.update_layout(
        title=f"Candlestick Chart — {symbol}",
        xaxis_title="Ημερομηνία",
        yaxis_title="Τιμή ($)",
        height=400,
        xaxis_rangeslider_visible=False
    )

    return fig


def plot_returns_bar(data_dict):
    """
    Γράφημα ράβδων με την απόδοση (ROI) κάθε επένδυσης.
    """
    symbols = []
    returns = []
    colors = []

    for symbol, df in data_dict.items():
        if df is not None and not df.empty:
            roi = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
            symbols.append(symbol)
            returns.append(roi)
            colors.append('green' if roi >= 0 else 'red')

    fig = go.Figure(go.Bar(
        x=symbols,
        y=returns,
        marker_color=colors,
        text=[f"{r:+.2f}%" for r in returns],
        textposition='outside'
    ))

    fig.update_layout(
        title="Σύγκριση Αποδόσεων (ROI %)",
        xaxis_title="Σύμβολο",
        yaxis_title="Απόδοση (%)",
        height=350
    )

    return fig


# ============================================================
# ΚΥΡΙΟ ΜΕΡΟΣ ΤΗΣ ΕΦΑΡΜΟΓΗΣ
# ============================================================

if load_data:
    # Διαβάζουμε τα σύμβολα που έβαλε ο χρήστης
    # split(',') χωρίζει το κείμενο στα κόμματα
    # .strip() αφαιρεί κενά, .upper() τα κάνει κεφαλαία
    symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]

    if not symbols:
        st.error("Παρακαλώ εισάγετε τουλάχιστον ένα σύμβολο!")
    else:
        # Δείχνουμε μήνυμα φόρτωσης
        with st.spinner("Φόρτωση δεδομένων..."):
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

        # Εμφάνιση σφαλμάτων αν υπάρχουν
        if errors:
            st.warning(f"Δεν βρέθηκαν δεδομένα για: {', '.join(errors)}")

        if not data_dict:
            st.error("Δεν φορτώθηκαν δεδομένα. Ελέγξτε τα σύμβολα.")
        else:
            # ---- ΚΑΡΤΕΛΕΣ (Tabs) ----
            tab1, tab2, tab3, tab4 = st.tabs([
                "📊 Σύγκριση & Αποδόσεις",
                "🕯️ Candlestick Charts",
                "📋 Δείκτες & Στατιστικά",
                "📥 Εξαγωγή Δεδομένων"
            ])

            # ========== TAB 1: ΣΥΓΚΡΙΣΗ ==========
            with tab1:
                st.subheader("Σύγκριση Απόδοσης")
                fig_compare = plot_price_chart(data_dict, selected_period_label)
                st.plotly_chart(fig_compare, use_container_width=True)

                st.subheader("ROI ανά Επένδυση")
                fig_bar = plot_returns_bar(data_dict)
                st.plotly_chart(fig_bar, use_container_width=True)

            # ========== TAB 2: CANDLESTICK ==========
            with tab2:
                selected_sym = st.selectbox("Επιλέξτε σύμβολο:", list(data_dict.keys()))
                if selected_sym:
                    fig_candle = plot_candlestick(selected_sym, data_dict[selected_sym])
                    st.plotly_chart(fig_candle, use_container_width=True)

            # ========== TAB 3: ΔΕΙΚΤΕΣ ==========
            with tab3:
                st.subheader("Βασικοί Χρηματοοικονομικοί Δείκτες")

                for sym in data_dict:
                    with st.expander(f"📌 {sym}", expanded=True):
                        metrics = calculate_metrics(data_dict[sym], ticker_dict[sym])
                        if metrics:
                            # Εμφανίζουμε τους δείκτες σε στήλες
                            cols = st.columns(3)
                            for i, (key, val) in enumerate(metrics.items()):
                                cols[i % 3].metric(label=key, value=val)
                        else:
                            st.info("Δεν υπάρχουν διαθέσιμα δεδομένα.")

                # Πίνακας ημερήσιων αποδόσεων
                st.subheader("Ημερήσιες Αποδόσεις (%)")
                returns_df = pd.DataFrame()
                for sym, df in data_dict.items():
                    returns_df[sym] = df['Close'].pct_change() * 100
                returns_df = returns_df.dropna()
                st.dataframe(returns_df.tail(20).style.format("{:.2f}%").background_gradient(cmap='RdYlGn', axis=None))

            # ========== TAB 4: ΕΞΑΓΩΓΗ ==========
            with tab4:
                st.subheader("Εξαγωγή Δεδομένων σε CSV")
                for sym, df in data_dict.items():
                    csv = df.to_csv().encode('utf-8')
                    st.download_button(
                        label=f"⬇️ Κατέβασε δεδομένα {sym}",
                        data=csv,
                        file_name=f"{sym}_{selected_period}.csv",
                        mime='text/csv'
                    )

else:
    # Αρχική οθόνη — πριν ο χρήστης πατήσει φόρτωση
    st.info("👈 Επιλέξτε σύμβολα από το μενού αριστερά και πατήστε **Φόρτωση Δεδομένων**")

    st.markdown("""
    ### Οδηγός Συμβόλων
    | Κατηγορία | Παραδείγματα |
    |-----------|-------------|
    | Μετοχές ΗΠΑ | `AAPL`, `MSFT`, `TSLA`, `GOOGL`, `AMZN` |
    | Μετοχές Ευρώπης | `ASML.AS`, `SAP.DE`, `OR.PA` |
    | Κρυπτονομίσματα | `BTC-USD`, `ETH-USD`, `SOL-USD` |
    | ETFs | `SPY`, `QQQ`, `VTI`, `GLD` |
    | Ομόλογα | `TLT`, `IEF`, `SHY` |
    """)