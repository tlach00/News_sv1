import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Function to fetch news from GNews API
def fetch_news(query, api_key, language='en', max_results=10):
    url = f'https://gnews.io/api/v4/search?q={query}&token={api_key}&lang={language}&max={max_results}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return pd.DataFrame(data.get('articles', []))
    else:
        return pd.DataFrame()  # Return empty DataFrame if request fails

# Function to perform sentiment analysis
def analyze_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(text)
    return sentiment['compound']

# Function to visualize sentiment over time
def plot_sentiment_over_time(df):
    if 'publishedAt' not in df or df.empty:
        st.warning("No news data available to plot.")
        return
    df['publishedAt'] = pd.to_datetime(df['publishedAt'])
    df = df.sort_values('publishedAt')
    fig = px.line(df, x='publishedAt', y='sentiment', title='Sentiment Over Time', markers=True)
    st.plotly_chart(fig)

# Streamlit UI
st.title('📊 Financial News Sentiment Analysis')

# User input for query and API key
query = st.text_input('Enter search term:', 'stock market')
api_key = st.text_input('Enter GNews API key:', type="password")

if st.button('Fetch and Analyze News'):
    with st.spinner('Fetching news articles...'):
        news_df = fetch_news(query, api_key)
        if not news_df.empty:
            news_df['sentiment'] = news_df['description'].apply(lambda x: analyze_sentiment(x) if isinstance(x, str) else 0)
            st.success('News articles fetched and analyzed successfully!')
            st.write("### News Articles with Sentiment Scores")
            st.dataframe(news_df[['title', 'description', 'sentiment', 'url']])

            # Show sentiment trend over time
            plot_sentiment_over_time(news_df)

            # Show links to articles
            st.write("### Read Full Articles:")
            for index, row in news_df.iterrows():
                st.markdown(f"- [{row['title']}]({row['url']}) - **Sentiment Score:** {row['sentiment']:.2f}")
        else:
            st.warning('No news articles found for the given query.')

    # Show sentiment analysis results
    if not news_df.empty:
        st.write("### Sentiment Analysis Results:")
        st.write(f"Average Sentiment Score: {news_df['sentiment'].mean():.2f}")
        st.write(f"Positive Sentiment Percentage: {(news_df['sentiment'] > 0).mean() * 100:.2f}%")§