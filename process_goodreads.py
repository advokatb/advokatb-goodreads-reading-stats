import pandas as pd
import json
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Load CSV
df = pd.read_csv('goodreads_library_export.csv')

# Clean and process data
df['Number of Pages'] = pd.to_numeric(df['Number of Pages'], errors='coerce').fillna(0).astype(int)
df['Estimated Word Count'] = df['Number of Pages'] * 275
df['Date Read'] = pd.to_datetime(df['Date Read'], errors='coerce')
df['My Rating'] = df['My Rating'].fillna(0).astype(int)
df['Series'] = df['Title'].str.extract(r'\(([^,]+), #\d+\)', expand=False)
df['Title'] = df['Title'].str.replace(r'\s*\([^)]+\)', '', regex=True).str.strip()
df['Bookshelves'] = df['Bookshelves'].fillna('')
df['ISBN'] = df['ISBN'].str.strip('="')
df['ISBN13'] = df['ISBN13'].str.strip('="')
df['Additional Authors'] = df['Additional Authors'].fillna('')

# Filter for 'read' books
books_read = df[df['Exclusive Shelf'] == 'read'].copy()

# Fetch cover URLs from Google Books API
def get_cover_url(isbn, isbn13, title, author, additional_authors):
    # Step 1: Try ISBN13 and ISBN
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
                    logging.info(f"Found cover for ISBN {identifier}: {cover}")
                    return cover if cover else None
                else:
                    logging.info(f"No results for ISBN {identifier}")
            else:
                logging.info(f"Failed ISBN request: {response.status_code}")
        except Exception as e:
            logging.error(f"Error with ISBN {identifier}: {e}")

    # Step 2: Fallback to title + primary author (English)
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
                    logging.info(f"Found cover for {title} by {author}: {cover}")
                    return cover if cover else None
                else:
                    logging.info(f"No results for {title} by {author}")
            else:
                logging.info(f"Failed English author request: {response.status_code}")
        except Exception as e:
            logging.error(f"Error with English author {author}: {e}")

    # Step 3: Fallback to title + additional authors (Russian)
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
                        logging.info(f"Found cover for {title} by {add_author}: {cover}")
                        return cover if cover else None
                    else:
                        logging.info(f"No results for {title} by {add_author}")
                else:
                    logging.info(f"Failed Russian author request: {response.status_code}")
            except Exception as e:
                logging.error(f"Error with Russian author {add_author}: {e}")
    
    logging.info(f"No cover found for {title}")
    return None

# Apply cover URL fetch
books_read.loc[:, 'Cover URL'] = books_read.apply(
    lambda row: get_cover_url(row['ISBN'], row['ISBN13'], row['Title'], row['Author'], row['Additional Authors']), 
    axis=1
)

# Calculate stats
total_books = len(books_read)
total_pages = books_read['Number of Pages'].sum()
avg_pages = total_pages / total_books if total_books > 0 else 0
avg_rating = books_read['My Rating'][books_read['My Rating'] > 0].mean()
avg_rating = 0 if pd.isna(avg_rating) else avg_rating
series_counts = books_read[books_read['Series'].notna()].groupby('Series').size().to_dict()

# Prepare book list with cover URLs
book_list = books_read[['Title', 'Author', 'Number of Pages', 'Estimated Word Count', 'Date Read', 'My Rating', 'Series', 'Bookshelves', 'ISBN', 'ISBN13', 'Cover URL']].copy()
book_list['Date Read'] = book_list['Date Read'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else None)
book_list['Series'] = book_list['Series'].apply(lambda x: x if pd.notna(x) else None)
book_list['Bookshelves'] = book_list['Bookshelves'].apply(lambda x: x if pd.notna(x) else None)
book_list['ISBN'] = book_list['ISBN'].apply(lambda x: x if pd.notna(x) else None)
book_list['ISBN13'] = book_list['ISBN13'].apply(lambda x: x if pd.notna(x) else None)
book_list['Cover URL'] = book_list['Cover URL'].apply(lambda x: x if pd.notna(x) else None)
book_list = book_list.to_dict(orient='records')

# Reading timeline
timeline = books_read.groupby(books_read['Date Read'].dt.to_period('M')).size().reset_index(name='Books')
timeline['Date'] = timeline['Date Read'].apply(lambda x: x.strftime('%Y-%m') if pd.notna(x) else None)
timeline = timeline.dropna(subset=['Date'])
timeline_data = timeline[['Date', 'Books']].to_dict(orient='records')

# Save to JSON
stats = {
    'total_books': int(total_books),
    'total_pages': int(total_pages),
    'avg_pages': round(float(avg_pages), 1),
    'avg_rating': round(float(avg_rating), 2),
    'series_counts': {k: int(v) for k, v in series_counts.items()},
    'book_list': book_list,
    'timeline': timeline_data
}
with open('reading_stats.json', 'w') as f:
    json.dump(stats, f, indent=2)

print("Stats generated and saved to 'reading_stats.json'")