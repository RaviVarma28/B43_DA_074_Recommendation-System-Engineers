from httpx import get
from selectolax.parser import HTMLParser
import pandas as pd
import spacy
from nltk.corpus import stopwords
import string
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
import matplotlib.pyplot as plt
import os

def get_news(link=None) -> pd.DataFrame:

    """
    This function takes takes as string and requests the data using httpx get method
    """
    if not link:
        raise Exception("URL is required to scrape.")

    resp = get(link)

    if resp.status_code != 200:
        raise Exception("Oops! Something went wrong with the request.")
    
    # Parsing the data using selectolax HTML Parser
    tree = HTMLParser(resp.text)

    headlines = [h.text() for h in tree.css("h2")]
    summaries = [s.text() for s in tree.css("p a")]
    dates = [d.text() for d in tree.css("figure + div > div")]
    links = [l.attributes['href'] for l in tree.css("p a")]


    # Creating a DataFrame for the news
    df = pd.DataFrame(
        {
            "Headline": headlines,
            "Summary": summaries,
            "Date": dates,
            "Link": links
        }
    )

    df['Date'] = pd.to_datetime(df['Date'])

    print("Scraping Complete!")
    print('Preprocesssing...')

    
    df['Preprocessed_Summary'] = df['Summary'].apply(preprocess)
    df['Sentiment'] = df['Preprocessed_Summary'].apply(get_sentiment)
    df['Sentiment_Label'] = df['Sentiment'].apply(lambda x: "Positive" if x>0 else "Negative" if x < 0 else "Neutral")

    tfidf = TfidfVectorizer(max_df=0.85, max_features=50)

    tfidf_matrix = tfidf.fit_transform(df['Preprocessed_Summary'])
    feature_names = tfidf.get_feature_names_out()

    df['Top_Keywords'] = get_top_keywords(tfidf_matrix, feature_names, 6)
    df['Entities']= df['Preprocessed_Summary'].apply(extract_entities)


    return df

def preprocess(text):

    stop_words = set(stopwords.words("english"))
    punctuations = string.punctuation

    doc = nlp(text)
    tokens = [token.lemma_.lower() for token in doc if token.text.lower() not in stop_words and token.text not in punctuations]

    return " ".join(tokens)

def get_sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment.polarity

def get_top_keywords(tfidf_matrix, feature_names, n):
    top_keywords = []
    
    for doc in tfidf_matrix:
        top_indices = doc.toarray().argsort()[0][-n:][::-1]
        top_keywords.append([feature_names[i] for i in top_indices])
    
    return top_keywords

def extract_entities(text):
    doc = nlp(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    
    return entities


if __name__ == "__main__":

    nlp = spacy.load("en_core_web_sm")

    urls = ["https://www.medicalnewstoday.com/news","https://www.healthline.com/health-news"]
    filename = 'data/medical_news.csv'

    for url in urls:
        df = get_news(url)

        if os.path.exists(filename):
            print("Appending to existing file...")
            existing_df = pd.read_csv(filename)

            print(f"Existing data: {len(existing_df)} articles")
            combined_df = pd.concat([existing_df, df]).drop_duplicates(subset=["Headline", "Link"], keep="last")

            print(f"Combined data: {len(combined_df)} articles")
            combined_df.to_csv(filename, index=False)

        else:
            print("Creating new file...")
            df.to_csv(filename.split("/")[-1], index=False)