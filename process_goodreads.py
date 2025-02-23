import pandas as pd
import json

# Load CSV
df = pd.read_csv('goodreads_library_export.csv')

# Clean and process data
df['Number of Pages'] = pd.to_numeric(df['Number of Pages'], errors='coerce').fillna(0).astype(int)
df['Estimated Word Count'] = df['Number of Pages'] * 275
df['Date Read'] = pd.to_datetime(df['Date Read'], errors='coerce')
df['My Rating'] = df['My Rating'].fillna(0).astype(int)
df['Series'] = df['Title'].str.extract(r'\(([^,]+), #\d+\)', expand=False)
df['Title'] = df['Title'].str.replace(r'\s*\([^)]+\)', '', regex=True).str.strip()
df['Bookshelves'] = df['Bookshelves'].fillna('')  # Replace NaN with empty string as fallback

# Filter for books marked as 'read' on Exclusive Shelf
books_read = df[df['Exclusive Shelf'] == 'read']

# Calculate stats for 'read' books only
total_books = len(books_read)
total_pages = books_read['Number of Pages'].sum()
total_words = books_read['Estimated Word Count'].sum()
total_read = len(books_read)
avg_rating = books_read['My Rating'][books_read['My Rating'] > 0].mean()
avg_rating = 0 if pd.isna(avg_rating) else avg_rating
series_counts = books_read[books_read['Series'].notna()].groupby('Series').size().to_dict()

# Prepare book list for 'read' books, ensuring no NaN
book_list = books_read[['Title', 'Author', 'Number of Pages', 'Estimated Word Count', 'Date Read', 'My Rating', 'Series', 'Bookshelves']].copy()
book_list['Date Read'] = book_list['Date Read'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else None)
book_list['Series'] = book_list['Series'].apply(lambda x: x if pd.notna(x) else None)
book_list['Bookshelves'] = book_list['Bookshelves'].apply(lambda x: x if pd.notna(x) else None)  # Convert NaN to None
book_list = book_list.to_dict(orient='records')

# Reading timeline for 'read' books
timeline = books_read.groupby(books_read['Date Read'].dt.to_period('M')).size().reset_index(name='Books')
timeline['Date'] = timeline['Date Read'].apply(lambda x: x.strftime('%Y-%m') if pd.notna(x) else None)
timeline = timeline.dropna(subset=['Date'])
timeline_data = timeline[['Date', 'Books']].to_dict(orient='records')

# Save to JSON, ensuring all values are JSON-safe
stats = {
    'total_books': int(total_books),
    'total_pages': int(total_pages),
    'total_words': int(total_words),
    'total_read': int(total_read),
    'avg_rating': round(float(avg_rating), 2) if not pd.isna(avg_rating) else 0.0,
    'series_counts': {k: int(v) for k, v in series_counts.items()},
    'book_list': book_list,
    'timeline': timeline_data
}
with open('reading_stats.json', 'w') as f:
    json.dump(stats, f, indent=2)

print("Stats generated and saved to 'reading_stats.json'")