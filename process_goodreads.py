import pandas as pd
import json
from datetime import datetime

# Load CSV (assuming it's saved as 'goodreads_library_export.csv')
df = pd.read_csv('goodreads_library_export.csv')

# Clean and process data
df['Number of Pages'] = pd.to_numeric(df['Number of Pages'], errors='coerce').fillna(0).astype(int)
df['Estimated Word Count'] = df['Number of Pages'] * 275  # Rough avg words/page
df['Date Read'] = pd.to_datetime(df['Date Read'], errors='coerce')
df['My Rating'] = df['My Rating'].fillna(0).astype(int)

# Extract series from titles (e.g., "Book Title (Series, #1)")
df['Series'] = df['Title'].str.extract(r'\(([^,]+), #\d+\)', expand=False)
df['Title'] = df['Title'].str.replace(r'\s*\([^)]+\)', '', regex=True).str.strip()

# Calculate stats
total_books = len(df)
total_pages = df['Number of Pages'].sum()
total_words = df['Estimated Word Count'].sum()
books_read = df[df['Bookshelves'].str.contains('read', na=False)]
total_read = len(books_read)
avg_rating = books_read['My Rating'][books_read['My Rating'] > 0].mean() or 0
series_counts = df[df['Series'].notna()].groupby('Series').size().to_dict()

# Prepare book list with relevant details, converting Timestamp to string
book_list = df[['Title', 'Author', 'Number of Pages', 'Estimated Word Count', 'Date Read', 'My Rating', 'Series', 'Bookshelves']].copy()
book_list['Date Read'] = book_list['Date Read'].dt.strftime('%Y-%m-%d').replace('NaT', None)  # Convert to string or None
book_list = book_list.to_dict(orient='records')

# Reading timeline for chart, converting Period to string
timeline = books_read.groupby(df['Date Read'].dt.to_period('M')).size().reset_index(name='Books')
timeline['Date'] = timeline['Date Read'].dt.strftime('%Y-%m')  # Already a string from previous step
timeline_data = timeline[['Date', 'Books']].to_dict(orient='records')

# Save to JSON
stats = {
    'total_books': total_books,
    'total_pages': int(total_pages),
    'total_words': int(total_words),
    'total_read': total_read,
    'avg_rating': round(avg_rating, 2),
    'series_counts': series_counts,
    'book_list': book_list,
    'timeline': timeline_data
}
with open('reading_stats.json', 'w') as f:
    json.dump(stats, f, indent=2)

print("Stats generated and saved to 'reading_stats.json'")