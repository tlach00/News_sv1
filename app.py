# 📌 Place this in `app.py`
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Load Finnhub API Key from Streamlit secrets
finnhub_api_key = st.secrets["finnhub"]["api_key"]

# Function to fetch news from Finnhub API
def fetch_finnhub_news(category="general"):
    url = f"https://finnhub.io/api/v1/news?category={category}&token={finnhub_api_key}"
    response = requests.get(url)
    
    if response.status_code == 200:
        news_data = response.json()
        if isinstance(news_data, list) and len(news_data) > 0:
            # Convert to DataFrame for easier processing
            news_df = pd.DataFrame(news_data)
            return news_df
    return pd.DataFrame()  # Return empty DataFrame if no news found

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

# News Category Selection
category_options = {
    "general": "📢 General",
    "forex": "💱 Forex",
    "crypto": "🪙 Crypto",
    "merger": "📈 Mergers & Acquisitions"
}
category = st.selectbox("Select News Category", list(category_options.keys()), format_func=lambda x: category_options[x])

# Fetch & Analyze Button
if st.button("Fetch & Analyze News"):
    with st.spinner("Fetching news articles..."):
        news_df = fetch_finnhub_news(category)
        
        if not news_df.empty:
            # Apply sentiment analysis
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
            st.warning("No news articles found for the selected category.")
