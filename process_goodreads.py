import pandas as pd  # Add this import for pandas
import time
from utils.data_loader import load_and_preprocess_data, load_mappings
from utils.api_fetch import fetch_book_data, fetch_goodreads_annotation, fetch_goodreads_genres
from utils.cover_fetch import get_cover_url
from utils.stats_generator import generate_stats

# Load data and mappings
df = load_and_preprocess_data()
correct_ids, series_mapping, genre_translation, excluded_genres, author_mapping = load_mappings()

# Apply annotations from Goodreads as primary source
df['Annotation'] = df.apply(
    lambda row: fetch_goodreads_annotation(row['Book Id']) if pd.notna(row['Book Id'])
    else fetch_book_data(row['ISBN'] or row['ISBN13'], row['Title'], row['Author'], row['Additional Authors'], genre_translation, excluded_genres)[1],
    axis=1
)
time.sleep(1)  # Rate limiting after Goodreads fetch

# Fallback to Google Books if Goodreads fails
df['Annotation'] = df.apply(
    lambda row: fetch_book_data(row['ISBN'] or row['ISBN13'], row['Title'], row['Author'], row['Additional Authors'], genre_translation, excluded_genres)[1]
    if pd.isna(row['Annotation']) and (row['ISBN'] or row['ISBN13'] or row['Title'])
    else row['Annotation'],
    axis=1
)
time.sleep(1)  # Rate limiting after Google Books fallback

# Apply genres with Google Books as primary and Goodreads as fallback
df['Genres'] = df.apply(
    lambda row: fetch_book_data(row['ISBN'] or row['ISBN13'], row['Title'], row['Author'], row['Additional Authors'], genre_translation, excluded_genres)[0]
    if (row['ISBN'] or row['ISBN13'] or row['Title']) and len(fetch_book_data(row['ISBN'] or row['ISBN13'], row['Title'], row['Author'], row['Additional Authors'], genre_translation, excluded_genres)[0]) > 0
    else fetch_goodreads_genres(row['Book Id'], genre_translation, excluded_genres),
    axis=1
)
time.sleep(1)  # Rate limiting

# Assign manual series for Sergei Lukyanenko and Suzanne Collins books
df.loc[df['Author'] == 'Sergei Lukyanenko', 'Series'] = df['Title'].map(series_mapping)
df.loc[df['Author'] == 'Suzanne Collins', 'Series'] = df['Title'].map(series_mapping)

# Process all books for covers
df.loc[:, 'Cover URL'] = df.apply(
    lambda row: get_cover_url(row['ISBN'], row['ISBN13'], row['Title'], row['Author'], row['Additional Authors'], correct_ids),
    axis=1
)

# Generate stats and save to JSON
generate_stats(df)