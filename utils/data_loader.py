import pandas as pd
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

def load_mappings():
    """Load all mappings from JSON files."""
    with open('data/correct_ids.json', 'r', encoding='utf-8') as f:
        correct_ids = json.load(f)
    with open('data/series_mapping.json', 'r', encoding='utf-8') as f:
        series_mapping = json.load(f)
    with open('data/genre_translation.json', 'r', encoding='utf-8') as f:
        genre_translation = json.load(f)
    with open('data/excluded_genres.json', 'r', encoding='utf-8') as f:
        excluded_genres = set(json.load(f))
    with open('data/author_mapping.json', 'r', encoding='utf-8') as f:
        author_mapping = json.load(f)
    with open('data/custom_genres.json', 'r', encoding='utf-8') as f:
        custom_genres = json.load(f)
    return correct_ids, series_mapping, genre_translation, excluded_genres, author_mapping, custom_genres

def load_and_preprocess_data():
    """Load and preprocess the Goodreads CSV data."""
    try:
        df = pd.read_csv('goodreads_library_export.csv', encoding='utf-8')
        logging.info(f"CSV loaded with {len(df)} rows")
        logging.info(f"Sample Author data: {df['Author'].head().to_string()}")
    except Exception as e:
        logging.error(f"Failed to load CSV: {e}")
        raise

    # Load mappings
    _, series_mapping, _, _, _, _ = load_mappings()  # Updated to unpack all six values

    # Preprocess data
    df['Number of Pages'] = pd.to_numeric(df['Number of Pages'], errors='coerce').fillna(0).astype(int)
    df['Estimated Word Count'] = df['Number of Pages'] * 275
    df['Date Read'] = pd.to_datetime(df['Date Read'], errors='coerce')
    df['Date Added'] = pd.to_datetime(df['Date Added'], errors='coerce')
    df['My Rating'] = df['My Rating'].fillna(0).astype(int)

    # Enhanced Series extraction before title cleanup
    df['Series'] = df['Title'].str.extract(r'\(([^,]+),\s*#?\d+\)', expand=False)
    df.loc[df['Author'] == 'Sergei Lukyanenko', 'Series'] = df['Title'].map(series_mapping)
    df.loc[df['Author'] == 'Suzanne Collins', 'Series'] = df['Title'].map(series_mapping)
    logging.info(f"Processed Series data sample before cleanup: {df[['Title', 'Author', 'Series']].head().to_string()}")

    # Clean up titles and other fields
    df['Title'] = df['Title'].str.replace(r'\s*\([^)]+\)', '', regex=True).str.strip()
    df['Bookshelves'] = df['Bookshelves'].fillna('')
    df['Bookshelves with positions'] = df['Bookshelves with positions'].fillna('')
    df['Exclusive Shelf'] = df['Exclusive Shelf'].fillna('')
    df['ISBN'] = df['ISBN'].str.strip('="')
    df['ISBN13'] = df['ISBN13'].str.strip('="')
    df['Additional Authors'] = df['Additional Authors'].fillna('')

    return df