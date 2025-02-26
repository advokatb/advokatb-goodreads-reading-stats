class Book {
    constructor(attributes) {
        Object.assign(this, attributes);
    }
    getCoverUrl() {
        const url = this['Cover URL'] || 'https://placehold.co/100x150?text=Нет+обложки';
        console.log(`Cover URL for ${this.Title}: ${url}`);
        return url.startsWith('http://books.google.com') ? url.replace('http://', 'https://') : url;
    }
    formatDateRead() {
        if (!this['Date Read']) return '';
        const [year, month, day] = this['Date Read'].split('-');
        const days = this['Days Spent'];
        let daysText;
        if (days === 1) {
            daysText = '1 день';
        } else if (days >= 2 && days <= 4) {
            daysText = `${days} дня`;
        } else {
            daysText = `${days} дней`;
        }
        return `Прочитано: ${day}.${month}.${year} (${daysText})`;
    }
    getGoodreadsBookLink() {
        return this['Book Id'] ? `https://www.goodreads.com/book/show/${this['Book Id']}` : '#';
    }
    getDisplayAuthor() {
        if (this.Author === "Sergei Lukyanenko" && this['Additional Authors']) {
            return this['Additional Authors'].split(',')[0].trim();
        }
        return this.Author;
    }
    render() {
        const div = document.createElement('div');
        div.className = 'book-card bg-gray-50 p-4 rounded-lg shadow flex';
        const imgSrc = this.getCoverUrl();
        div.innerHTML = `
            <img src="${imgSrc}" alt="${this.Title}" class="book-cover mr-4" 
                 onload="console.log('Loaded cover for ${this.Title}')"
                 onerror="console.error('Failed to load cover for ${this.Title}: ${imgSrc}'); this.src='https://placehold.co/100x150?text=Нет+обложки'; this.onerror=null;">
            <div>
                <h3 class="text-lg font-semibold text-gray-800 inline">${this.Title}</h3>
                <a href="${this.getGoodreadsBookLink()}" target="_blank" class="ml-2">
                    <img src="https://www.goodreads.com/favicon.ico" alt="Goodreads" class="inline w-4 h-4">
                </a>
                <p class="text-gray-600">Автор: ${this.getDisplayAuthor()}</p>
                <p class="text-gray-500">Страниц: ${this['Number of Pages']}</p>
                ${this.Series ? `<p class="text-gray-500">Серия: ${this.Series}</p>` : ''}
                ${this['Date Read'] ? `<p class="text-gray-500">${this.formatDateRead()}</p>` : ''}
                ${this['My Rating'] > 0 ? `<p class="text-yellow-500">Оценка: ${'★'.repeat(this['My Rating'])}</p>` : ''}
            </div>
        `;
        return div;
    }
    renderCurrent() {
        const div = document.createElement('div');
        div.className = 'flex items-center space-x-4';
        const imgSrc = this.getCoverUrl();
        const [year, month, day] = this['Date Read'] ? this['Date Read'].split('-') : ['', '', ''];
        div.innerHTML = `
            <img src="${imgSrc}" alt="${this.Title}" class="book-cover w-16 h-24 mr-2" 
                 onload="console.log('Loaded cover for ${this.Title}')"
                 onerror="console.error('Failed to load cover for ${this.Title}: ${imgSrc}'); this.src='https://placehold.co/100x150?text=Нет+обложки'; this.onerror=null;">
            <div>
                <h3 class="text-lg font-semibold text-gray-800 inline">${this.Title}</h3>
                <a href="${this.getGoodreadsBookLink()}" target="_blank" class="ml-2">
                    <img src="https://www.goodreads.com/favicon.ico" alt="Goodreads" class="inline w-4 h-4">
                </a>
                <p class="text-gray-600 text-sm">Автор: ${this.getDisplayAuthor()}</p>
                <p class="text-gray-500 text-sm">Страниц: ${this['Number of Pages']}</p>
                ${this.Series ? `<p class="text-gray-500 text-sm">Серия: ${this.Series}</p>` : ''}
                ${this['Date Read'] ? `<p class="text-gray-500 text-sm">Прочитано: ${day}.${month}.${year}</p>` : ''}
            </div>
        `;
        return div;
    }
}

class BookCollection {
    constructor(books) {
        this.models = books.map(book => new Book(book));
        this.allBooks = [...this.models];
    }
    filterBySeries(series) {
        this.models = series ? 
            this.allBooks.filter(book => book.Series === series) : 
            [...this.allBooks];
        return this;
    }
    sortBy(field) {
        const [key, direction] = field.split('-');
        this.models.sort((a, b) => {
            let valA = a[key === 'date' ? 'Date Read' : key === 'pages' ? 'Number of Pages' : key === 'rating' ? 'My Rating' : 'Title'];
            let valB = b[key === 'date' ? 'Date Read' : key === 'pages' ? 'Number of Pages' : key === 'rating' ? 'My Rating' : 'Title'];
            if (key === 'date') {
                valA = valA || '9999-12-31';
                valB = valB || '9999-12-31';
            }
            if (direction === 'asc') {
                return valA < valB ? -1 : valA > valB ? 1 : 0;
            } else {
                return valA > valB ? -1 : valA < valB ? 1 : 0;
            }
        });
        return this;
    }
    getSeriesWithAuthors() {
        const seriesAuthors = {};
        this.allBooks.forEach(book => {
            if (book.Series) {
                if (!seriesAuthors[book.Series]) {
                    seriesAuthors[book.Series] = new Set();
                }
                seriesAuthors[book.Series].add(book.getDisplayAuthor());
            }
        });
        return seriesAuthors;
    }
    getLongestBook() {
        return this.allBooks.reduce((max, book) => 
            book['Number of Pages'] > max['Number of Pages'] ? book : max, this.allBooks[0]);
    }
    getShortestBook() {
        return this.allBooks.reduce((min, book) => 
            book['Number of Pages'] < min['Number of Pages'] ? book : min, this.allBooks[0]);
    }
    getMostProlificAuthor() {
        const authorCounts = {};
        this.allBooks.forEach(book => {
            const displayAuthor = book.getDisplayAuthor();
            authorCounts[displayAuthor] = (authorCounts[displayAuthor] || 0) + 1;
        });
        return Object.entries(authorCounts).reduce((max, [author, count]) => 
            count > max[1] ? [author, count] : max, ['', 0]);
    }
    getLastReadBook() {
        return this.allBooks.reduce((latest, book) => 
            new Date(book['Date Read']) > new Date(latest['Date Read']) ? book : latest, this.allBooks[0]);
    }
    render(containerId) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';
        this.models.forEach(book => container.appendChild(book.render()));
    }
    renderSeriesShelf(containerId) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';
        const seriesBooks = {};
        this.allBooks.forEach(book => {
            if (book.Series) {
                if (!seriesBooks[book.Series]) {
                    seriesBooks[book.Series] = { books: [], author: book.getDisplayAuthor() };
                }
                seriesBooks[book.Series].books.push(book);
            }
        });

        for (const [series, data] of Object.entries(seriesBooks)) {
            const { books, author } = data;
            const seriesDiv = document.createElement('div');
            seriesDiv.className = 'series-box';
            seriesDiv.innerHTML = `<h3 class="text-lg font-semibold text-gray-700 mb-2">${series} (${books.length} книг${books.length > 1 ? 'и' : 'а'}, ${author})</h3>`;
            const rowDiv = document.createElement('div');
            rowDiv.className = 'series-row';
            
            books.forEach((book, index) => {
                const bookDiv = document.createElement('div');
                bookDiv.className = 'series-book';
                bookDiv.style.left = `${index * 60}px`;
                bookDiv.style.zIndex = `${books.length - index}`;
                const imgSrc = book.getCoverUrl();
                bookDiv.innerHTML = `
                    <a href="${book.getGoodreadsBookLink()}" target="_blank">
                        <img src="${imgSrc}" alt="${book.Title}" 
                             onload="console.log('Loaded cover for ${book.Title}')"
                             onerror="console.error('Failed to load cover for ${book.Title}: ${imgSrc}'); this.src='https://placehold.co/80x120?text=Нет+обложки'; this.onerror=null;">
                    </a>
                `;
                rowDiv.appendChild(bookDiv);
            });

            seriesDiv.appendChild(rowDiv);
            container.appendChild(seriesDiv);
        }
    }
}

fetch('reading_stats.json')
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        document.getElementById('total-books').textContent = data.total_books;
        document.getElementById('total-pages').textContent = data.total_pages.toLocaleString();
        document.getElementById('books-2025').textContent = data.books_2025;

        const books = new BookCollection(data.book_list);
        const currentBooks = new BookCollection(data.current_list);
        
        if (currentBooks.models.length > 0) {
            document.getElementById('current-book').appendChild(currentBooks.models[0].renderCurrent());
        } else {
            document.getElementById('current-book').innerHTML = '<p class="text-gray-600">Ничего не читаю сейчас</p>';
        }

        const lastReadBook = books.getLastReadBook();
        if (lastReadBook) {
            document.getElementById('last-read-book').appendChild(lastReadBook.renderCurrent());
        } else {
            document.getElementById('last-read-book').innerHTML = '<p class="text-gray-600">Нет прочитанных книг</p>';
        }

        const longestBook = books.getLongestBook();
        const shortestBook = books.getShortestBook();
        const [mostProlificAuthor, authorBookCount] = books.getMostProlificAuthor();
        document.getElementById('longest-book').textContent = `${longestBook.Title} (${longestBook['Number of Pages']})`;
        document.getElementById('shortest-book').textContent = `${shortestBook.Title} (${shortestBook['Number of Pages']})`;
        document.getElementById('most-prolific-author').textContent = `${mostProlificAuthor} (${authorBookCount})`;

        // 2025 Reading Challenge
        const challengeGoal = 50;
        const booksRead = data.total_books; // Currently 13
        const startDate = new Date('2025-01-01');
        const endDate = new Date('2025-12-31');
        const today = new Date('2025-02-26'); // Current date
        const totalDays = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
        const daysPassed = Math.ceil((today - startDate) / (1000 * 60 * 60 * 24));
        const daysLeft = totalDays - daysPassed;
        const progressPercent = Math.min((booksRead / challengeGoal) * 100, 100).toFixed(0);

        document.getElementById('challenge-progress').innerHTML = `<strong>${booksRead} of ${challengeGoal} books read</strong>`;
        document.getElementById('challenge-days').textContent = `${daysLeft} days left`;
        document.getElementById('challenge-bar').style.width = `${progressPercent}%`;
        document.getElementById('challenge-percent').textContent = `${progressPercent}%`;

        books.renderSeriesShelf('series-shelf');

        const seriesFilter = document.getElementById('series-filter');
        Object.keys(data.series_counts).forEach(series => {
            const option = document.createElement('option');
            option.value = series;
            option.textContent = series;
            seriesFilter.appendChild(option);
        });

        books.sortBy('date-desc').render('book-list');
        document.getElementById('sort-by').value = 'date-desc';

        seriesFilter.addEventListener('change', () => {
            books.filterBySeries(seriesFilter.value).sortBy(document.getElementById('sort-by').value).render('book-list');
        });
        document.getElementById('sort-by').addEventListener('change', () => {
            books.filterBySeries(seriesFilter.value).sortBy(document.getElementById('sort-by').value).render('book-list');
        });

        const options = {
            series: [{ name: 'Книги', data: data.timeline.map(t => t.Books) }],
            chart: { type: 'bar', height: 200 },
            plotOptions: { bar: { horizontal: false, columnWidth: '70%' } },
            dataLabels: { enabled: false },
            xaxis: { categories: data.timeline.map(t => t.Date), title: { text: 'Месяц' } },
            yaxis: { title: { text: 'Книги' }, labels: { show: false } },
            colors: ['#2563eb'],
            tooltip: { y: { formatter: val => `${val} книг${val > 1 ? 'и' : 'а'}` } }
        };
        const chart = new ApexCharts(document.querySelector('#timelineChart'), options);
        chart.render();
    })
    .catch(error => console.error('Fetch error:', error));