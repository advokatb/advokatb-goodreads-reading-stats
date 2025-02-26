import pandas as pd
import json
import requests
import logging

CORRECT_IDS = {
    "Предел": "http://books.google.com/books/content?id=u5MwEAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api",
    "Порог": "http://books.google.com/books/content?id=TfqeDwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api",
    "Семь дней до Мегиддо": "http://books.google.com/books/content?id=e7M8EAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api",
    "КВАЗИ": "http://books.google.com/books/content?id=YHneDAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api",
    "Кайноzой": "http://books.google.com/books/content?id=XqF-DwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api",
    "Ресторан 06:06:06": "https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1737024919i/223689131.jpg"
}

SERIES_MAPPING = {
    "Семь дней до Мегиддо": "Соглашение",
    "Три дня Индиго": "Соглашение",
    "Месяц за Рубиконом": "Соглашение",
    "Лето волонтёра": "Соглашение",
    "Прыжок": "Соглашение",
    "Порог": "Порог",
    "Предел": "Порог"
}

# Genre mapping for local tags and Open Library subjects
GENRE_MAPPING = {
    "fantasy": "Фэнтези",
    "sci-fi": "Научная фантастика",
    "science-fiction": "Научная фантастика",
    "mystery": "Детектив",
    "thriller": "Триллер",
    "romance": "Романтика",
    "historical": "Исторический",
    "fiction": "Художественная литература",
    "non-fiction": "Нехудожественная литература",
    "horror": "Ужасы",
    "adventure": "Приключения",
    "drama": "Драма",
    "dystopia": "Дистопия",
    "biography": "Биография",
    "comedy": "Комедия"
}

logging.basicConfig(level=logging.INFO, format='%(message)s')
try:
    df = pd.read_csv('goodreads_library_export.csv')
    logging.info(f"CSV loaded with {len(df)} rows")
except Exception as e:
    logging.error(f"Failed to load CSV: {e}")
    raise

df['Number of Pages'] = pd.to_numeric(df['Number of Pages'], errors='coerce').fillna(0).astype(int)
df['Estimated Word Count'] = df['Number of Pages'] * 275
df['Date Read'] = pd.to_datetime(df['Date Read'], errors='coerce')
df['Date Added'] = pd.to_datetime(df['Date Added'], errors='coerce')
df['My Rating'] = df['My Rating'].fillna(0).astype(int)
df['Series'] = df['Title'].str.extract(r'\(([^,]+), #\d+\)', expand=False)
df['Title'] = df['Title'].str.replace(r'\s*\([^)]+\)', '', regex=True).str.strip()
df['Bookshelves'] = df['Bookshelves'].fillna('')
df['Bookshelves with positions'] = df['Bookshelves with positions'].fillna('')
df['Exclusive Shelf'] = df['Exclusive Shelf'].fillna('')
df['ISBN'] = df['ISBN'].str.strip('="')
df['ISBN13'] = df['ISBN13'].str.strip('="')
df['Additional Authors'] = df['Additional Authors'].fillna('')

# Extract genres from Bookshelves column
def extract_genres(bookshelves):
    shelves = [s.strip() for s in bookshelves.split(',') if s.strip()]
    genres = set()
    for shelf in shelves:
        shelf_lower = shelf.lower()
        for tag, genre in GENRE_MAPPING.items():
            if tag in shelf_lower and len(genres) < 3:
                genres.add(genre)
    return list(genres) if genres else []

# Fetch genres from Open Library if local tags fail
def fetch_openlibrary_genres(isbn, isbn13):
    for identifier in [isbn13, isbn]:
        if not identifier or identifier == '':
            continue
        url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{identifier}&jscmd=data&format=json"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                book_key = f"ISBN:{identifier}"
                if book_key in data and 'subjects' in data[book_key]:
                    subjects = data[book_key]['subjects']
                    genres = set()
                    for subject in subjects:
                        subject_lower = subject.lower()
                        for tag, genre in GENRE_MAPPING.items():
                            if tag in subject_lower and len(genres) < 3:
                                genres.add(genre)
                    if genres:
                        logging.info(f"Fetched genres for ISBN {identifier}: {genres}")
                        return list(genres)
        except Exception as e:
            logging.error(f"Error fetching Open Library genres for ISBN {identifier}: {e}")
    return []

# Combine local and Open Library genres
def get_genres(row):
    local_genres = extract_genres(row['Bookshelves'])
    if local_genres:
        return local_genres[:3]
    return fetch_openlibrary_genres(row['ISBN'], row['ISBN13'])[:3] or None

df['Genres'] = df.apply(get_genres, axis=1)

# Assign manual series for Sergei Lukyanenko books
df.loc[df['Author'] == 'Sergei Lukyanenko', 'Series'] = df['Title'].map(SERIES_MAPPING)

# Filter read books for stats
books_read = df[df['Exclusive Shelf'] == 'read'].copy()
logging.info(f"Filtered {len(books_read)} read books")

def get_cover_url(isbn, isbn13, title, author, additional_authors):
    if title in CORRECT_IDS:
        logging.info(f"Using manual ID for {title}: {CORRECT_IDS[title]}")
        return CORRECT_IDS[title]
    for identifier in [isbn13, isbn]:
        if not identifier or identifier == '':
            continue
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{identifier}"
        logging.info(f"Trying ISBN: {url}")
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get('totalItems', 0) > 0:
                    book = data['items'][0]['volumeInfo']
                    cover = book.get('imageLinks', {}).get('thumbnail', None)
                    if cover:
                        logging.info(f"Found cover for ISBN {identifier}: {cover}")
                        return cover
        except Exception as e:
            logging.error(f"Error with ISBN {identifier}: {e}")
    logging.info(f"No cover found for {title}")
    return None

# Process all books for covers
df.loc[:, 'Cover URL'] = df.apply(
    lambda row: get_cover_url(row['ISBN'], row['ISBN13'], row['Title'], row['Author'], row['Additional Authors']), 
    axis=1
)

# Calculate Days Spent only for read books
books_read.loc[:, 'Days Spent'] = (books_read['Date Read'] - books_read['Date Added']).dt.days

total_books = len(books_read)
total_pages = books_read['Number of Pages'].sum()
avg_pages = total_books > 0 and total_pages / total_books or 0
avg_rating = books_read['My Rating'][books_read['My Rating'] > 0].mean() or 0
series_counts = books_read[books_read['Series'].notna()].groupby('Series').size().to_dict()
books_2025 = len(books_read[books_read['Date Read'].dt.year == 2025])

# Define columns for all books
columns = [
    'Title', 'Author', 'Additional Authors', 'Number of Pages', 'Estimated Word Count', 'Date Read', 
    'Date Added', 'My Rating', 'Series', 'Bookshelves', 'Bookshelves with positions', 
    'Exclusive Shelf', 'ISBN', 'ISBN13', 'Cover URL', 'Genres'
]

for col in ['Book Id', 'Author Id']:
    if col in df.columns:
        columns.append(col)

# Prepare full book list
book_list = df[columns].copy()
book_list['Date Read'] = book_list['Date Read'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else None)
book_list['Date Added'] = book_list['Date Added'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else None)
book_list['Series'] = book_list['Series'].apply(lambda x: x if pd.notna(x) else None)
book_list['Bookshelves'] = book_list['Bookshelves'].apply(lambda x: x if pd.notna(x) else None)
book_list['Bookshelves with positions'] = book_list['Bookshelves with positions'].apply(lambda x: x if pd.notna(x) else None)
book_list['Exclusive Shelf'] = book_list['Exclusive Shelf'].apply(lambda x: x if pd.notna(x) else None)
book_list['ISBN'] = book_list['ISBN'].apply(lambda x: x if pd.notna(x) else None)
book_list['ISBN13'] = book_list['ISBN13'].apply(lambda x: x if pd.notna(x) else None)
book_list['Cover URL'] = book_list['Cover URL'].apply(lambda x: x if pd.notna(x) and x != 'None' else None)
book_list['Genres'] = book_list['Genres'].apply(lambda x: x if x is not None else None)
book_list['Days Spent'] = book_list.apply(
    lambda row: int((pd.to_datetime(row['Date Read']) - pd.to_datetime(row['Date Added'])).days) 
    if pd.notna(row['Date Read']) and pd.notna(row['Date Added']) else None, 
    axis=1
)
for col in ['Book Id', 'Author Id']:
    if col in book_list.columns:
        book_list[col] = book_list[col].apply(lambda x: str(x) if pd.notna(x) else None)
book_list = book_list.replace({pd.NA: None, float('nan'): None}).to_dict(orient='records')

timeline = books_read.groupby(books_read['Date Read'].dt.to_period('M')).size().reset_index(name='Books')
timeline['Date'] = timeline['Date Read'].apply(lambda x: x.strftime('%Y-%m') if pd.notna(x) else None)
timeline = timeline.dropna(subset=['Date'])
timeline_data = timeline[['Date', 'Books']].to_dict(orient='records')

stats = {
    'total_books': int(total_books),
    'total_pages': int(total_pages),
    'avg_pages': round(float(avg_pages), 1),
    'avg_rating': round(float(avg_rating), 2),
    'series_counts': {k: int(v) for k, v in series_counts.items()},
    'books_2025': int(books_2025),
    'book_list': book_list,
    'timeline': timeline_data
}
with open('reading_stats.json', 'w') as f:
    json.dump(stats, f, indent=2)

logging.info("Stats generated and saved to 'reading_stats.json'")