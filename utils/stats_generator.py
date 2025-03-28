import pandas as pd
import json
import logging

def generate_stats(df):
    """Generate reading statistics and save to JSON."""
    # Filter read books for stats
    books_read = df[df['Exclusive Shelf'] == 'read'].copy()
    logging.info(f"Filtered {len(books_read)} read books")

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