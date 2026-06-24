import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

def extract_keywords_for_user(df: pd.DataFrame, top_n: int = 3) -> list[str]:
    """
    Extract top N keywords from the user's historical product interactions using TF-IDF.
    """
    if df.empty:
        return []

    # 1. Prepare the text corpus from the DataFrame
    # We combine category, brand, and title to form a document for each interaction.
    # Higher weight can be given to brand or category by repeating them.
    documents = []
    for _, row in df.iterrows():
        title = str(row['title']) if pd.notna(row['title']) else ""
        brand = str(row['brand']) if pd.notna(row['brand']) else ""
        category = str(row['category_name']) if pd.notna(row['category_name']) else ""
        
        # Clean text (remove special characters like >, HTML tags)
        title = re.sub(r'<[^>]*>', ' ', title)
        category = category.replace('>', ' ')
        
        # We repeat brand and category to give them higher weight in the TF-IDF
        doc = f"{title} {brand} {brand} {category} {category}"
        documents.append(doc)

    # 2. Treat the user's entire history as a single document to find their most distinct keywords
    # If a user has very few items, max_df=0.95 will remove words that appear in all their items.
    # We only want to use max_df if they have enough history.
    max_df_val = 0.95 if len(documents) >= 5 else 1.0
    
    vectorizer = TfidfVectorizer(
        max_df=max_df_val,
        min_df=1,
        stop_words=None, 
        token_pattern=r'(?u)\b\w+\b' 
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(documents)
    except ValueError:
        # Happens if vocabulary is empty
        return []
        
    feature_names = vectorizer.get_feature_names_out()
    
    # Sum the TF-IDF scores across all items the user interacted with
    sum_scores = tfidf_matrix.sum(axis=0)
    
    # Create a list of (word, score)
    scores = [(word, sum_scores[0, idx]) for word, idx in vectorizer.vocabulary_.items()]
    
    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)
    
    # Filter out pure numbers or very short words, and exclude generic words
    stopwords = {"쇼핑몰", "상품", "판매", "할인", "이벤트", "특가", "무료배송"}
    keywords = []
    for word, score in scores:
        if len(word) > 1 and not word.isnumeric() and word not in stopwords:
            keywords.append(word)
        if len(keywords) == top_n:
            break
            
    return keywords
