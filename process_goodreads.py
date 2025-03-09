import pandas as pd
import json
import requests
from bs4 import BeautifulSoup
import logging
import time
import os
import urllib.parse

CORRECT_IDS = {
    "Предел": "http://books.google.com/books/content?id=u5MwEAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api",
    "Порог": "http://books.google.com/books/content?id=TfqeDwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api",
    "Семь дней до Мегиддо": "http://books.google.com/books/content?id=e7M8EAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api",
    "КВАЗИ": "http://books.google.com/books/content?id=YHneDAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api",
    "Кайноzой": "http://books.google.com/books/content?id=XqF-DwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api",
    "Поиски утраченного завтра": "http://books.google.com/books/content?id=jysYEQAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api",
    "Ресторан 06:06:06": "https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1737024919i/223689131.jpg"
}

SERIES_MAPPING = {
    "Семь дней до Мегиддо": "Изменённые",
    "Три дня Индиго": "Изменённые",
    "Месяц за Рубиконом": "Изменённые",
    "Лето волонтёра": "Изменённые",
    "Прыжок": "Соглашение",
    "Порог": "Соглашение",
    "Предел": "Соглашение",
    "Голодные игры": "Голодные игры",
    "Сойка-пересмешница": "Голодные игры",
    "И вспыхнет пламя": "Голодные игры",
    "Кайноzой": "Кваzи",  # Added for the Кваzи series
    "КВАZИ": "Кваzи"    # Added for the Кваzи series
}

GENRE_TRANSLATION = {
    "Mystery": "Детектив",
    "Thriller": "Триллер",
    "Crime": "Криминал",
    "Detective": "Детектив",
    "Mystery Thriller": "Детективный триллер",
    "Novels": "Романы",
    "Fantasy": "Фэнтези",
    "Science Fiction": "Научная фантастика",
    "Romance": "Романтика",
    "Historical Fiction": "Историческая проза",
    "Horror": "Ужасы",
    "Adventure": "Приключения",
    "Dystopia": "Дистопия",
    "Biography": "Биография",
    "Comedy": "Комедия",
    "Classics": "Классика",
    "Magical Realism": "Магический реализм",
    "Young Adult": "Молодёжная литература",
    "Literary Collections": "Литературные сборники",
    "Fathers and daughters": "Отцы и дочери",
    "Colombian fiction": "Колумбийская художественная литература",
    "Psychology": "Психология",
    "Science Fiction Fantasy": "Научно-фантастическое фэнтези"
}

EXCLUDED_GENRES = {"Fiction", "Audiobook", "Rus", "Russia", "Foreign Language Study"}

# Mapping of English to Russian author names (moved to front-end)
AUTHOR_MAPPING = {
    "Sergei Lukyanenko": "Сергей Лукьяненко",
    "Daniel Keyes": "Дэниел Киз",
    "Gabriel García Márquez": "Габриэль Гарсиа Маркес",
    "Charlotte Brontë": "Шарлотта Бронте",
    "Pom Yu Jin": "Пом Ю Джин",
    "Chan Ho-Kei": "Чан Хо-Кей",
    "Abraham Verghese": "Абрахам Вергисе",
    "Gary Chapman": "Гэри Чепмен",
    "Veronika i Angelina Shen": "Вероника и Ангелина Шэн",
    "Jane Austen": "Джейн Остин",
    "Harper Lee": "Харпер Ли",
    "Suzanne Collins": "Сюзанна Коллинз"
    # Add more mappings as needed based on your CSV
}

logging.basicConfig(level=logging.INFO, format='%(message)s')
try:
    df = pd.read_csv('goodreads_library_export.csv', encoding='utf-8')
    logging.info(f"CSV loaded with {len(df)} rows")
    logging.info(f"Sample Author data: {df['Author'].head().to_string()}")  # Debug: Check initial author values
except Exception as e:
    logging.error(f"Failed to load CSV: {e}")
    raise

# Remove author mapping here to keep original names
# df['Author'] = df['Author'].apply(lambda x: AUTHOR_MAPPING.get(x.lower(), x) if pd.notna(x) else x)  # Commented out
logging.info(f"Processed Author data sample (original): {df['Author'].head().to_string()}")  # Debug original names

df['Number of Pages'] = pd.to_numeric(df['Number of Pages'], errors='coerce').fillna(0).astype(int)
df['Estimated Word Count'] = df['Number of Pages'] * 275
df['Date Read'] = pd.to_datetime(df['Date Read'], errors='coerce')
df['Date Added'] = pd.to_datetime(df['Date Added'], errors='coerce')
df['My Rating'] = df['My Rating'].fillna(0).astype(int)

# Enhanced Series extraction before title cleanup
df['Series'] = df['Title'].str.extract(r'\(([^,]+),\s*#?\d+\)', expand=False)
df.loc[df['Author'] == 'Sergei Lukyanenko', 'Series'] = df['Title'].map(SERIES_MAPPING)  # Uses original name
df.loc[df['Author'] == 'Suzanne Collins', 'Series'] = df['Title'].map(SERIES_MAPPING)  # Add series for Suzanne Collins
logging.info(f"Processed Series data sample before cleanup: {df[['Title', 'Author', 'Series']].head().to_string()}")  # Debug Series

df['Title'] = df['Title'].str.replace(r'\s*\([^)]+\)', '', regex=True).str.strip()
df['Bookshelves'] = df['Bookshelves'].fillna('')
df['Bookshelves with positions'] = df['Bookshelves with positions'].fillna('')
df['Exclusive Shelf'] = df['Exclusive Shelf'].fillna('')
df['ISBN'] = df['ISBN'].str.strip('="')
df['ISBN13'] = df['ISBN13'].str.strip('="')
df['Additional Authors'] = df['Additional Authors'].fillna('')

# Fetch genres and annotations from Google Books
def fetch_book_data(isbn, title, author, additional_authors):
    """Fetch genres and annotation from Google Books API."""
    genres = []
    annotation = None
    if isbn and isinstance(isbn, str) and len(isbn.replace('-', '')) in [10, 13]:
        api_key = os.environ.get('GOOGLE_BOOKS_API_KEY', 'YOUR_GOOGLE_BOOKS_API_KEY')
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn.replace('-', '')}&key={api_key}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('items') and data['items'][0].get('volumeInfo'):
                    volume_info = data['items'][0]['volumeInfo']
                    genres = volume_info.get('categories', [])[:3]
                    translated_genres = [GENRE_TRANSLATION.get(genre, genre) for genre in genres if genre not in EXCLUDED_GENRES]
                    genres = translated_genres if translated_genres else []
                    annotation = volume_info.get('description', None)
                    logging.info(f"Fetched genres from Google Books for ISBN {isbn}: {genres}")
                else:
                    logging.warning(f"No data found for ISBN {isbn} from Google Books, trying title/author")
                    # Fall back to title/author search if ISBN fails
                    title_encoded = urllib.parse.quote(title)
                    author_clean = urllib.parse.quote(author.strip())
                    url = f"https://www.googleapis.com/books/v1/volumes?q={title_encoded}+inauthor:{author_clean}"
                    try:
                        response = requests.get(url, timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            if data.get('totalItems', 0) > 0:
                                volume_info = data['items'][0]['volumeInfo']
                                genres = volume_info.get('categories', [])[:3]
                                translated_genres = [GENRE_TRANSLATION.get(genre, genre) for genre in genres if genre not in EXCLUDED_GENRES]
                                genres = translated_genres if translated_genres else []
                                annotation = volume_info.get('description', None)
                                logging.info(f"Fetched genres from Google Books for {title} by {author}: {genres}")
                    except requests.RequestException as e:
                        logging.error(f"Error fetching data for {title} by {author}: {e}")
            else:
                logging.error(f"Google Books API error for ISBN {isbn}: {response.status_code} - {response.text}")
        except requests.RequestException as e:
            logging.error(f"Error fetching data from Google Books for ISBN {isbn}: {e}")
    elif title and author:
        title_encoded = urllib.parse.quote(title)
        author_clean = urllib.parse.quote(author.strip())
        url = f"https://www.googleapis.com/books/v1/volumes?q={title_encoded}+inauthor:{author_clean}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('totalItems', 0) > 0:
                    volume_info = data['items'][0]['volumeInfo']
                    genres = volume_info.get('categories', [])[:3]
                    translated_genres = [GENRE_TRANSLATION.get(genre, genre) for genre in genres if genre not in EXCLUDED_GENRES]
                    genres = translated_genres if translated_genres else []
                    annotation = volume_info.get('description', None)
                    logging.info(f"Fetched genres from Google Books for {title} by {author}: {genres}")
        except requests.RequestException as e:
            logging.error(f"Error fetching data for {title} by {author}: {e}")
    return genres, annotation

# Fetch annotation from Goodreads
def fetch_goodreads_annotation(book_id):
    """Fetch annotation from Goodreads book page."""
    if not book_id or book_id == '':
        logging.warning(f"Invalid or empty Book ID: {book_id}, returning fallback")
        return None
    url = f"https://www.goodreads.com/book/show/{book_id}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            description_div = soup.find('div', {'data-testid': 'description'})
            if description_div:
                # Extract all text from nested elements, cleaning up whitespace
                annotation = ' '.join(description_div.get_text(separator=' ', strip=True).split())
                if annotation and len(annotation.strip()) > 0:
                    logging.info(f"Fetched annotation from Goodreads for Book ID {book_id}: {annotation[:50]}...")
                    return annotation
                logging.warning(f"No valid annotation found for Book ID {book_id}")
            else:
                logging.warning(f"No description div found for Book ID {book_id}")
        else:
            logging.error(f"Goodreads API error for Book ID {book_id}: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        logging.error(f"Error fetching annotation for Book ID {book_id}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error fetching annotation for Book ID {book_id}: {e}")
    return None

# Fetch genres from Goodreads as fallback
def fetch_goodreads_genres(book_id):
    """Fetch genres from Goodreads book page as a fallback with error handling."""
    if not book_id or book_id == '':
        logging.warning(f"Invalid or empty Book ID: {book_id}, returning fallback")
        return []  # Fallback for invalid ID
    url = f"https://www.goodreads.com/book/show/{book_id}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            genres_div = soup.find('div', {'data-testid': 'genresList'})
            if genres_div:
                genre_buttons = genres_div.find_all('a', class_='Button--tag')
                genres = [button.find('span', class_='Button__labelItem').text for button in genre_buttons if button.find('span', class_='Button__labelItem')]
                filtered_genres = [g for g in genres if g not in EXCLUDED_GENRES]
                translated_genres = [GENRE_TRANSLATION.get(genre, genre) for genre in filtered_genres[:3]]
                if translated_genres:
                    logging.info(f"Fetched genres from Goodreads for Book ID {book_id}: {translated_genres}")
                    return translated_genres
                logging.warning(f"No valid genres found for Book ID {book_id}")
            else:
                logging.warning(f"No genres div found for Book ID {book_id}, trying alternative parsing")
                # Alternative parsing for genres (e.g., from book details or tags)
                alternative_genres = soup.find_all('a', class_='BookPageTagButton')
                if alternative_genres:
                    genres = [tag.text.strip() for tag in alternative_genres if tag.text.strip()]
                    filtered_genres = [g for g in genres if g not in EXCLUDED_GENRES]
                    translated_genres = [GENRE_TRANSLATION.get(genre, genre) for genre in filtered_genres[:3]]
                    if translated_genres:
                        logging.info(f"Fetched alternative genres from Goodreads for Book ID {book_id}: {translated_genres}")
                        return translated_genres
                logging.warning(f"No alternative genres found for Book ID {book_id}")
        else:
            logging.error(f"Goodreads API error for Book ID {book_id}: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        logging.error(f"Error fetching genres for Book ID {book_id}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error fetching genres for Book ID {book_id}: {e}")
    logging.info(f"Fallback to empty genres list for Book ID {book_id}")
    return []  # Fallback to empty list if all else fails

# Apply annotations from Goodreads as primary source
df['Annotation'] = df.apply(
    lambda row: fetch_goodreads_annotation(row['Book Id']) if pd.notna(row['Book Id']) 
    else fetch_book_data(row['ISBN'] or row['ISBN13'], row['Title'], row['Author'], row['Additional Authors'])[1],
    axis=1
)
time.sleep(1)  # Rate limiting after Goodreads fetch

# Fallback to Google Books if Goodreads fails
df['Annotation'] = df.apply(
    lambda row: fetch_book_data(row['ISBN'] or row['ISBN13'], row['Title'], row['Author'], row['Additional Authors'])[1] 
    if pd.isna(row['Annotation']) and (row['ISBN'] or row['ISBN13'] or row['Title']) 
    else row['Annotation'],
    axis=1
)
time.sleep(1)  # Rate limiting after Google Books fallback

# Apply genres with Google Books as primary and Goodreads as fallback
df['Genres'] = df.apply(
    lambda row: fetch_book_data(row['ISBN'] or row['ISBN13'], row['Title'], row['Author'], row['Additional Authors'])[0] 
    if (row['ISBN'] or row['ISBN13'] or row['Title']) and len(fetch_book_data(row['ISBN'] or row['ISBN13'], row['Title'], row['Author'], row['Additional Authors'])[0]) > 0 
    else fetch_goodreads_genres(row['Book Id']),
    axis=1
)
time.sleep(1)  # Rate limiting

# Assign manual series for Sergei Lukyanenko and Suzanne Collins books
df.loc[df['Author'] == 'Sergei Lukyanenko', 'Series'] = df['Title'].map(SERIES_MAPPING)  # Uses original name
df.loc[df['Author'] == 'Suzanne Collins', 'Series'] = df['Title'].map(SERIES_MAPPING)  # Add series for Suzanne Collins
logging.info(f"Series data after mapping: {df[['Title', 'Author', 'Series']].head().to_string()}")  # Debug Series

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
                    else:
                        logging.info(f"No thumbnail for ISBN {identifier}: {json.dumps(book.get('imageLinks', {}))}")
                else:
                    logging.info(f"No results for ISBN {identifier}")
            else:
                logging.info(f"Failed ISBN request: {response.status_code}")
        except Exception as e:
            logging.error(f"Error with ISBN {identifier}: {e}")

    if title and author:
        title_clean = urllib.parse.quote(title)
        author_clean = urllib.parse.quote(author.strip())
        url = f"https://www.googleapis.com/books/v1/volumes?q={title_clean}+inauthor:{author_clean}"
        logging.info(f"Trying author: {url}")
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get('totalItems', 0) > 0:
                    book = data['items'][0]['volumeInfo']
                    cover = book.get('imageLinks', {}).get('thumbnail', None)
                    if cover:
                        logging.info(f"Found cover for {title} by {author}: {cover}")
                        return cover
                    else:
                        logging.info(f"No thumbnail for {title} by {author}: {json.dumps(book.get('imageLinks', {}))}")
                else:
                    logging.info(f"No results for {title} by {author}")
            else:
                logging.info(f"Failed author request: {response.status_code}")
        except Exception as e:
            logging.error(f"Error with author {author}: {e}")

    if title and additional_authors:
        title_clean = urllib.parse.quote(title)
        add_author = additional_authors.split(',')[0].strip()
        if add_author:
            add_author_clean = urllib.parse.quote(add_author)
            url = f"https://www.googleapis.com/books/v1/volumes?q={title_clean}+inauthor:{add_author_clean}"
            logging.info(f"Trying additional author: {url}")
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('totalItems', 0) > 0:
                        book = data['items'][0]['volumeInfo']
                        cover = book.get('imageLinks', {}).get('thumbnail', None)
                        if cover:
                            logging.info(f"Found cover for {title} by {add_author}: {cover}")
                            return cover
                    url_broad = f"https://www.googleapis.com/books/v1/volumes?q={title_clean}"
                    logging.info(f"Trying broad title: {url_broad}")
                    response_broad = requests.get(url_broad)
                    if response_broad.status_code == 200:
                        data_broad = response_broad.json()
                        if data_broad.get('totalItems', 0) > 0:
                            book_broad = data_broad['items'][0]['volumeInfo']
                            cover = book_broad.get('imageLinks', {}).get('thumbnail', None)
                            if cover:
                                logging.info(f"Found cover for ${title} (broad): ${cover}")
                                return cover
                    logging.info(f"No thumbnail for ${title} by ${add_author}: ${json.dumps(book.get('imageLinks', {}))}")
                else:
                    logging.info(f"Failed additional author request: ${response.status_code}")
            except Exception as e:
                logging.error(f"Error with additional author ${add_author}: ${e}")
    
    logging.info(f"No cover found for ${title}")
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
    'Exclusive Shelf', 'ISBN', 'ISBN13', 'Cover URL', 'Genres', 'Annotation'
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
book_list['Genres'] = book_list['Genres'].apply(lambda x: x if x is not None else [])
book_list['Annotation'] = book_list['Annotation'].apply(lambda x: x if x is not None else None)
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
    'timeline': timeline_data,
    'longest_book': books_read.loc[books_read['Number of Pages'].idxmax(), ['Title', 'Number of Pages']].to_dict() if not books_read.empty else {'Title': 'Нет данных', 'Number of Pages': 0},
    'shortest_book': books_read.loc[books_read['Number of Pages'].idxmin(), ['Title', 'Number of Pages']].to_dict() if not books_read.empty else {'Title': 'Нет данных', 'Number of Pages': 0}
}
with open('reading_stats.json', 'w', encoding='utf-8') as f:
    json.dump(stats, f, indent=2, ensure_ascii=False)

logging.info("Stats generated and saved to 'reading_stats.json'")