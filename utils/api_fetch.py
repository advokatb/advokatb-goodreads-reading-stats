import requests
from bs4 import BeautifulSoup
import logging
import time
import os
import urllib.parse

def fetch_book_data(isbn, title, author, additional_authors, genre_translation, excluded_genres):
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
                    translated_genres = [genre_translation.get(genre, genre) for genre in genres if genre not in excluded_genres]
                    genres = translated_genres if translated_genres else []
                    annotation = volume_info.get('description', None)
                    logging.info(f"Fetched genres from Google Books for ISBN {isbn}: {genres}")
                else:
                    logging.warning(f"No data found for ISBN {isbn} from Google Books, trying title/author")
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
                                translated_genres = [genre_translation.get(genre, genre) for genre in genres if genre not in excluded_genres]
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
                    translated_genres = [genre_translation.get(genre, genre) for genre in genres if genre not in excluded_genres]
                    genres = translated_genres if translated_genres else []
                    annotation = volume_info.get('description', None)
                    logging.info(f"Fetched genres from Google Books for {title} by {author}: {genres}")
        except requests.RequestException as e:
            logging.error(f"Error fetching data for {title} by {author}: {e}")
    return genres, annotation

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

def fetch_goodreads_genres(book_id, genre_translation, excluded_genres):
    """Fetch genres from Goodreads book page as a fallback."""
    if not book_id or book_id == '':
        logging.warning(f"Invalid or empty Book ID: {book_id}, returning fallback")
        return []
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
                filtered_genres = [g for g in genres if g not in excluded_genres]
                translated_genres = [genre_translation.get(genre, genre) for genre in filtered_genres[:3]]
                if translated_genres:
                    logging.info(f"Fetched genres from Goodreads for Book ID {book_id}: {translated_genres}")
                    return translated_genres
                logging.warning(f"No valid genres found for Book ID {book_id}")
            else:
                logging.warning(f"No genres div found for Book ID {book_id}, trying alternative parsing")
                alternative_genres = soup.find_all('a', class_='BookPageTagButton')
                if alternative_genres:
                    genres = [tag.text.strip() for tag in alternative_genres if tag.text.strip()]
                    filtered_genres = [g for g in genres if g not in excluded_genres]
                    translated_genres = [genre_translation.get(genre, genre) for genre in filtered_genres[:3]]
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
    return []