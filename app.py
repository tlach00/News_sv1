# 📌 Place this in `app.py`
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta

# Load Finnhub API Key from Streamlit secrets
finnhub_api_key = st.secrets["finnhub"]["api_key"]

# Function to fetch news from Finnhub API
def fetch_finnhub_news(category=None, query=None):
    today = datetime.today()
    last_week = today - timedelta(days=7)
    from_date = last_week.strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")

    if query:
        url = f"https://finnhub.io/api/v1/company-news?symbol={query.upper()}&from={from_date}&to={to_date}&token={finnhub_api_key}"
    else:
        url = f"https://finnhub.io/api/v1/news?category={category}&token={finnhub_api_key}"
    
    response = requests.get(url)
    st.write(f"🔎 **Finnhub API URL:** {url}")  # Debugging output
    st.write(f"📡 **API Response Status Code:** {response.status_code}")  # Debugging output
    
    if response.status_code == 200:
        news_data = response.json()
        st.write(f"📄 **API Response:** {news_data[:3]}")  # Show first 3 news articles for debugging
        
        if isinstance(news_data, list) and len(news_data) > 0:
            news_df = pd.DataFrame(news_data)
            return news_df
    return pd.DataFrame()

# Function to perform sentiment analysis
def analyze_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(text)
    return sentiment['compound']

# Function to visualize sentiment over time
def plot_sentiment_over_time(df):
    if 'datetime' not in df or df.empty:
        st.warning("No news data available to plot.")
        return
    
    df['datetime'] = pd.to_datetime(df['datetime'], unit='s')
    df = df.sort_values('datetime')
    
    fig = px.line(df, x='datetime', y='sentiment', title='Sentiment Over Time', markers=True)
    st.plotly_chart(fig)

# 📌 Streamlit UI
st.title('📊 Financial News Sentiment Analysis (Powered by Finnhub)')

# 🚀 Add Search Bar for Custom Query
query = st.text_input("🔍 Search for news (stocks, personalities, companies, events):")

# 🔹 Category Buttons (Avoid Double Clicking Issues)
st.write("### Choose a Category:")
categories = {
    "general": "📢 General News",
    "forex": "💱 Forex",
    "crypto": "🪙 Crypto",
    "merger": "📈 Mergers & Acquisitions"
}

selected_category = st.radio("Select a category:", list(categories.keys()), format_func=lambda x: categories[x])

# 🚀 Fetch & Analyze Button
if st.button("Fetch & Analyze News"):
    with st.spinner("Fetching news articles..."):
        if query:
            news_df = fetch_finnhub_news(query=query)
        else:
            news_df = fetch_finnhub_news(category=selected_category)

        if not news_df.empty:
            news_df['sentiment'] = news_df['headline'].apply(lambda x: analyze_sentiment(x) if isinstance(x, str) else 0)

            st.success('News articles fetched and analyzed successfully!')
            st.write("### News Articles with Sentiment Scores")
            st.dataframe(news_df[['headline', 'summary', 'sentiment', 'source']])

            # Sentiment Trend
            plot_sentiment_over_time(news_df)

            # Show links to full articles
            st.write("### Read Full Articles:")
            for index, row in news_df.iterrows():
                st.markdown(f"- [{row['headline']}]({row['url']}) - **Sentiment Score:** {row['sentiment']:.2f}")

            # Sentiment Summary
            st.write("### Sentiment Analysis Results:")
            st.write(f"Average Sentiment Score: {news_df['sentiment'].mean():.2f}")
            st.write(f"Positive Sentiment Percentage: {(news_df['sentiment'] > 0).mean() * 100:.2f}%")
        else:
            st.warning("No news articles found for the selected category or search query.")
