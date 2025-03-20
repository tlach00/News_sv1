import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import Counter
import datetime

# Function to fetch news from Finnhub API
def fetch_news(category, query, api_key):
    if query:
        url = f"https://finnhub.io/api/v1/company-news?symbol={query}&from=2025-03-13&to=2025-03-20&token={api_key}"
    else:
        url = f"https://finnhub.io/api/v1/news?category={category}&token={api_key}"
    
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return []

# Function to perform sentiment analysis
def analyze_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    return analyzer.polarity_scores(text)['compound']

# Function to extract most mentioned companies/tickers
def extract_top_mentions(news_data):
    all_words = []
    for article in news_data:
        all_words.extend(article['headline'].split())
    return Counter(all_words).most_common(5)  # Top 5 most frequent words

# Function to format and filter news
def process_news(news_data):
    df = pd.DataFrame(news_data)
    if df.empty:
        return df
    df['sentiment'] = df['headline'].apply(lambda x: analyze_sentiment(x))
    df = df.drop_duplicates(subset=['headline'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='s')
    return df

# Streamlit UI Setup
st.set_page_config(layout="wide")
st.title('📈 Financial News Sentiment Analysis (Powered by Finnhub)')

# API Key Setup
api_key = st.secrets["FINNHUB_API_KEY"]

# Search Bar
query = st.text_input("🔍 Search for news (stocks, personalities, companies, events):", "")

# Categories Selection
categories = {
    "general": "General News",
    "forex": "Forex",
    "crypto": "Crypto",
    "mergers": "Mergers & Acquisitions"
}
selected_category = st.radio("Select a category:", list(categories.keys()), format_func=lambda x: categories[x])

# Fetch and analyze news button
if st.button("Fetch & Analyze News"):
    news_data = fetch_news(selected_category, query, api_key)
    if news_data:
        df = process_news(news_data)
        
        # Sentiment Overview
        avg_sentiment = df['sentiment'].mean()
        sentiment_counts = df['sentiment'].apply(lambda x: "Positive" if x > 0 else ("Negative" if x < 0 else "Neutral")).value_counts()
        st.subheader("📊 Sentiment Analysis")
        st.write(f"**Average Sentiment Score:** {avg_sentiment:.2f}")
        st.bar_chart(sentiment_counts)
        
        # Sentiment Trend Over Time
        st.subheader("📈 Sentiment Trend Over Time")
        fig = px.line(df, x='datetime', y='sentiment', title='Sentiment Trend')
        st.plotly_chart(fig)
        
        # News Volume & Impact
        st.subheader("📰 News Volume Over Time")
        df_count = df.groupby(df['datetime'].dt.date).size()
        st.bar_chart(df_count)
        
        # Most Mentioned Topics
        st.subheader("🔥 Most Mentioned Topics")
        top_mentions = extract_top_mentions(news_data)
        st.write(pd.DataFrame(top_mentions, columns=["Word", "Count"]))
        
        # Display News Articles (Show First 10, Expandable)
        st.subheader("🗞️ Top News Articles")
        for i, row in df.head(10).iterrows():
            st.markdown(f"- [{row['headline']}]({row['url']}) - **Sentiment Score:** {row['sentiment']:.2f}")
        with st.expander("🔽 See More Articles"):
            for i, row in df.iloc[10:].iterrows():
                st.markdown(f"- [{row['headline']}]({row['url']}) - **Sentiment Score:** {row['sentiment']:.2f}")
    else:
        st.warning("No news articles found for the selected category or search query.")

