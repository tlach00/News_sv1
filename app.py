import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Finnhub API Key
api_key = st.secrets["FINNHUB_API_KEY"]

# Function to fetch stock symbols for autocomplete search
@st.cache_data
def fetch_stock_symbols():
    url = f"https://finnhub.io/api/v1/stock/symbol?exchange=US&token={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return [stock["symbol"] for stock in data]
    else:
        return []

# Get stock symbols for autocomplete
stock_symbols = fetch_stock_symbols()

# Function to fetch news based on stock symbol
def fetch_news(symbol):
    url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from=2025-03-13&to=2025-03-20&token={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return []

# Function to perform sentiment analysis
def analyze_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(text)
    return sentiment["compound"]

# Streamlit UI
st.title("📉 Financial News Sentiment Analysis (Powered by Finnhub)")

# Search Bar for stock symbols (autocomplete)
selected_stock = st.selectbox(
    "🔍 Search for a stock symbol:", stock_symbols, index=None, placeholder="Type to search..."
)

# Categories selection
categories = {
    "Latest": "general",
    "Stock Market": "market",
    "Economies": "economy",
    "Earnings": "earnings",
    "Tech": "technology",
    "Crypto": "crypto",
    "Real Estate": "real_estate",
}

selected_category = st.selectbox("📂 Select a Category:", list(categories.keys()), index=0)

# Fetch News Button
if st.button("Fetch & Analyze News"):
    with st.spinner("Fetching news..."):
        if selected_stock:
            news_data = fetch_news(selected_stock)
        else:
            st.warning("Please select a stock symbol.")

        if news_data:
            df = pd.DataFrame(news_data)
            df["sentiment"] = df["headline"].apply(analyze_sentiment)

            # Display first 10 articles and allow expanding
            max_display = 10
            if len(df) > max_display:
                show_all = st.checkbox("Show all articles")

            st.write("### News Articles with Sentiment Scores")
            for index, row in df.iterrows():
                if index >= max_display and not show_all:
                    break
                st.markdown(f"- [{row['headline']}]({row['url']}) - **Sentiment Score:** {row['sentiment']:.2f}")

            # Sentiment Summary
            st.write("### Sentiment Analysis Summary")
            st.write(f"📊 **Average Sentiment Score:** {df['sentiment'].mean():.2f}")
            st.write(f"✅ **Positive Sentiment:** {(df['sentiment'] > 0).mean() * 100:.2f}%")
            st.write(f"❌ **Negative Sentiment:** {(df['sentiment'] < 0).mean() * 100:.2f}%")
            st.write(f"📰 **Total Articles:** {len(df)}")

            # Plot Sentiment Trend
            df["datetime"] = pd.to_datetime(df["datetime"], unit="s")
            df = df.sort_values("datetime")
            fig = px.line(df, x="datetime", y="sentiment", title="Sentiment Over Time", markers=True)
            st.plotly_chart(fig)

        else:
            st.warning("No news articles found for the selected stock or category.")

    st.success("News analysis completed!")
    