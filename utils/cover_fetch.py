import requests
import urllib.parse
import logging

def get_cover_url(isbn, isbn13, title, author, additional_authors, correct_ids):
    """Fetch book cover URL using ISBN, title, and author."""
    if title in correct_ids:
        logging.info(f"Using manual ID for {title}: {correct_ids[title]}")
        return correct_ids[title]

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
                        logging.info(f"No thumbnail for ISBN {identifier}: {data.get('imageLinks', {})}")
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
                        logging.info(f"No thumbnail for {title} by {author}: {data.get('imageLinks', {})}")
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
                                logging.info(f"Found cover for {title} (broad): {cover}")
                                return cover
                    logging.info(f"No thumbnail for {title} by {add_author}: {data.get('imageLinks', {})}")
                else:
                    logging.info(f"Failed additional author request: {response.status_code}")
            except Exception as e:
                logging.error(f"Error with additional author {add_author}: {e}")

    logging.info(f"No cover found for {title}")
    return None