import pandas as pd
import json
import requests
from bs4 import BeautifulSoup
import logging
import time

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
    "Young Adult": "Молодёжная литература"
}

EXCLUDED_GENRES = {"Fiction", "Audiobook", "Rus"}

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

# Fetch genres from Goodreads book page
def fetch_goodreads_genres(book_id):
    if not book_id or book_id == '':
        return None
    url = f"https://www.goodreads.com/book/show/{book_id}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            genres_div = soup.find('div', {'data-testid': 'genresList'})
            if genres_div:
                genre_buttons = genres_div.find_all('a', class_='Button--tag')
                genres = [button.find('span', class_='Button__labelItem').text for button in genre_buttons]
                filtered_genres = [g for g in genres if g not in EXCLUDED_GENRES]
                translated_genres = [GENRE_TRANSLATION.get(genre, genre) for genre in filtered_genres[:3]]
                logging.info(f"Fetched genres for Book ID {book_id}: {translated_genres}")
                return translated_genres if translated_genres else None
        logging.warning(f"No genres found or failed request for Book ID {book_id}: {response.status_code}")
        return None
    except Exception as e:
        logging.error(f"Error fetching genres for Book ID {book_id}: {e}")
        return None

df['Genres'] = df['Book Id'].apply(fetch_goodreads_genres)
time.sleep(1)

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
                    else:
                        logging.info(f"No thumbnail for ISBN {identifier}: {json.dumps(book.get('imageLinks', {}))}")
                else:
                    logging.info(f"No results for ISBN {identifier}")
            else:
                logging.info(f"Failed ISBN request: {response.status_code}")
        except Exception as e:
            logging.error(f"Error with ISBN {identifier}: {e}")

    if title and author:
        title_clean = title.split(':')[0].strip().replace(' ', '+')
        author_clean = author.split(',')[0].strip().replace(' ', '+')
        url = f"https://www.googleapis.com/books/v1/volumes?q={title_clean}+inauthor:{author_clean}"
        logging.info(f"Trying English author: {url}")
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
                logging.info(f"Failed English author request: {response.status_code}")
        except Exception as e:
            logging.error(f"Error with English author {author}: {e}")

    if title and additional_authors:
        title_clean = title.split(':')[0].strip().replace(' ', '+')
        add_author = additional_authors.split(',')[0].strip()
        if add_author:
            add_author_clean = add_author.replace(' ', '+')
            url = f"https://www.googleapis.com/books/v1/volumes?q={title_clean}+inauthor:{add_author_clean}"
            logging.info(f"Trying Russian author: {url}")
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
                                logging.info(f"Found cover for {title} (broad): {cover}")
                                return cover
                    logging.info(f"No thumbnail for {title} by {add_author}: {json.dumps(book.get('imageLinks', {}))}")
                else:
                    logging.info(f"Failed Russian author request: {response.status_code}")
            except Exception as e:
                logging.error(f"Error with Russian author {add_author}: {e}")
    
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