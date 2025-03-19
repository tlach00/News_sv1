import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import tweepy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Function to fetch news from GNews API
def fetch_news(query, api_key, language='en', max_results=10):
    url = f'https://gnews.io/api/v4/search?q={query}&token={api_key}&lang={language}&max={max_results}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        articles = pd.DataFrame(data.get('articles', []))
        
        # Remove duplicates based only on description (keeping articles with unique content)
        if not articles.empty:
            articles = articles.drop_duplicates(subset=['description'])

        return articles
    else:
        return pd.DataFrame()  # Return empty DataFrame if request fails

# Function to fetch tweets from Twitter API
def fetch_tweets(query, api_key, max_tweets=10):
    client = tweepy.Client(bearer_token=api_key)

    try:
        tweets = client.search_recent_tweets(query=query, tweet_fields=["created_at", "text"], max_results=max_tweets)
        if tweets.data:
            return pd.DataFrame([{"date": tweet.created_at, "text": tweet.text} for tweet in tweets.data])
        else:
            return pd.DataFrame()  # Return empty DataFrame if no tweets found
    except Exception as e:
        st.error(f"Error fetching tweets: {e}")
        return pd.DataFrame()

# Function to perform sentiment analysis
def analyze_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(text)
    return sentiment['compound']

# Function to visualize sentiment over time
def plot_sentiment_over_time(df, date_column, title):
    if date_column not in df or df.empty:
        st.warning(f"No data available to plot for {title}.")
        return
    df[date_column] = pd.to_datetime(df[date_column])
    df = df.sort_values(date_column)
    fig = px.line(df, x=date_column, y='sentiment', title=title, markers=True)
    st.plotly_chart(fig)

# Streamlit UI
st.title('📊 Financial News & Twitter Sentiment Analysis')

# Retrieve API keys from Streamlit secrets
news_api_key = st.secrets["GNEWS_API_KEY"]
twitter_api_key = st.secrets["TWITTER_BEARER_TOKEN"]

# User input for query
query = st.text_input('Enter search term:', 'stock market')

### FETCH & ANALYZE NEWS ###
if st.button('Fetch and Analyze News'):
    with st.spinner('Fetching news articles...'):
        news_df = fetch_news(query, news_api_key)
        if not news_df.empty:
            news_df['sentiment'] = news_df['description'].apply(lambda x: analyze_sentiment(x) if isinstance(x, str) else 0)
            st.success('News articles fetched and analyzed successfully!')
            st.write("### News Articles with Sentiment Scores")
            st.dataframe(news_df[['title', 'description', 'sentiment', 'url']])

            # Show sentiment trend over time
            plot_sentiment_over_time(news_df, 'publishedAt', 'Sentiment Over Time (News)')

            # Show links to articles
            st.write("### Read Full Articles:")
            for index, row in news_df.iterrows():
                st.markdown(f"- [{row['title']}]({row['url']}) - **Sentiment Score:** {row['sentiment']:.2f}")

            # Show sentiment analysis summary
            st.write("### Sentiment Analysis Results (News):")
            st.write(f"Average Sentiment Score: {news_df['sentiment'].mean():.2f}")
            st.write(f"Positive Sentiment Percentage: {(news_df['sentiment'] > 0).mean() * 100:.2f}%")

        else:
            st.warning('No news articles found for the given query.')

### FETCH & ANALYZE TWEETS ###
if st.button('Fetch and Analyze Tweets'):
    with st.spinner('Fetching tweets...'):
        tweets_df = fetch_tweets(query, twitter_api_key)
        
        if not tweets_df.empty:
            tweets_df['sentiment'] = tweets_df['text'].apply(lambda x: analyze_sentiment(x))
            st.success('Tweets fetched and analyzed successfully!')
            st.write("### Recent Tweets with Sentiment Scores")
            st.dataframe(tweets_df)

            # Show sentiment trend over time
            plot_sentiment_over_time(tweets_df, 'date', 'Sentiment Over Time (Twitter)')

            # Show sentiment analysis summary
            st.write("### Sentiment Analysis Results (Twitter):")
            st.write(f"Average Sentiment Score: {tweets_df['sentiment'].mean():.2f}")
            st.write(f"Positive Sentiment Percentage: {(tweets_df['sentiment'] > 0).mean() * 100:.2f}%")
        else:
            st.warning('No tweets found for the given query.')
