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
        return `${day}.${month}.${year} (${daysText})`;
    }
    getGoodreadsBookLink() {
        return this['Book Id'] ? `https://www.goodreads.com/book/show/${this['Book Id']}` : '#';
    }
    getDisplayAuthor() {
        // Use original author name, no transliteration
        return this.Author || (this['Additional Authors'] && this['Additional Authors'].split(',')[0].trim()) || 'No Author';
    }
    getDisplayGenres() {
        return this.Genres?.slice(0, 3) || []; // Use precomputed genres from JSON
    }
    render() {
        const div = document.createElement('div');
        div.className = 'book-card bg-gray-50 p-4 rounded-lg shadow flex';
        const imgSrc = this.getCoverUrl();
        const genres = this.getDisplayGenres();
        const author = this.getDisplayAuthor();
        div.innerHTML = `
            <img src="${imgSrc}" alt="${this.Title}" class="book-cover mr-4" 
                 onload="console.log('Loaded cover for ${this.Title}')"
                 onerror="console.error('Failed to load cover for ${this.Title}: ${imgSrc}'); this.src='https://placehold.co/100x150?text=Нет+обложки'; this.onerror=null;">
            <div>
                <h3 class="text-lg font-semibold text-gray-800 inline"><a href="${this.getGoodreadsBookLink()}" target="_blank" class="hover:underline">${this.Title}</a></h3>
                <p class="text-gray-600 text-sm">👤 ${author}</p>
                <p class="text-gray-500 text-sm">📖 ${this['Number of Pages']}</p>
                ${this.Series ? `<p class="text-gray-500 text-sm">📚 ${this.Series}</p>` : ''}
                ${genres.length > 0 ? `<p class="text-gray-500 text-xs">🎭 ${genres.join(', ')}</p>` : ''}
                ${this['Date Read'] ? `<p class="text-gray-500 text-sm">📅 ${this.formatDateRead()}</p>` : ''}
            </div>
            ${this['My Rating'] > 0 ? `<div class="rating" data-rating="${this['My Rating']}"></div>` : ''}
        `;
        return div;
    }
    renderCurrent() {
        const div = document.createElement('div');
        div.className = 'flex space-x-4'; // No items-center, no genres
        const imgSrc = this.getCoverUrl();
        const [readYear, readMonth, readDay] = this['Date Read'] ? this['Date Read'].split('-') : ['', '', ''];
        const author = this.getDisplayAuthor();
        div.innerHTML = `
            <img src="${imgSrc}" alt="${this.Title}" class="book-cover w-16 h-24 mr-2" 
                 onload="console.log('Loaded cover for ${this.Title}')"
                 onerror="console.error('Failed to load cover for ${this.Title}: ${imgSrc}'); this.src='https://placehold.co/100x150?text=Нет+обложки'; this.onerror=null;">
            <div>
                <h3 class="text-lg font-semibold text-gray-800 inline">${this.Title}</h3>
                <p class="text-gray-600 text-sm">Автор: ${author}</p>
                <p class="text-gray-500 text-sm">Страниц: ${this['Number of Pages']}</p>
                ${this.Series ? `<p class="text-gray-500 text-sm">Серия: ${this.Series}</p>` : ''}
                ${this['Date Read'] ? `<p class="text-gray-500 text-sm">Прочитано: ${readDay}.${readMonth}.${readYear}</p>` : ''}
                ${this['My Rating'] > 0 ? `<div class="rating" data-rating="${this['My Rating']}"></div>` : ''}
            </div>
        `;
        return div;
    }
}

class BookCollection {
    constructor(books) {
        this.models = books ? books.map(book => new Book(book)) : []; // Ensure models is always an array
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
        if (!this.allBooks.length) return { Title: 'Нет данных', 'Number of Pages': 0 };
        return this.allBooks.reduce((max, book) => 
            book['Number of Pages'] > max['Number of Pages'] ? book : max, this.allBooks[0]);
    }
    getShortestBook() {
        if (!this.allBooks.length) return { Title: 'Нет данных', 'Number of Pages': 0 };
        return this.allBooks.reduce((min, book) => 
            book['Number of Pages'] < min['Number of Pages'] ? book : min, this.allBooks[0]);
    }
    getMostProlificAuthor() {
        if (!this.allBooks.length) return ['Нет данных', 0];
        const authorCounts = {};
        this.allBooks.forEach(book => {
            if (book['Exclusive Shelf'] === 'read') {
                const displayAuthor = book.getDisplayAuthor();
                authorCounts[displayAuthor] = (authorCounts[displayAuthor] || 0) + 1;
            }
        });
        return Object.entries(authorCounts).reduce((max, [author, count]) => 
            count > max[1] ? [author, count] : max, ['', 0]);
    }
    getLastReadBook() {
        if (!this.allBooks.length) return null;
        return this.allBooks.reduce((latest, book) => 
            new Date(book['Date Read']) > new Date(latest['Date Read']) ? book : latest, this.allBooks[0]);
    }
    getRandomReadBook() {
        const readBooks = this.allBooks.filter(book => book['Exclusive Shelf'] === 'read');
        if (readBooks.length === 0) return null;
        const randomIndex = Math.floor(Math.random() * readBooks.length);
        return readBooks[randomIndex];
    }
    // Hardcoded author photos (extend as needed)
    getAuthorPhoto(authorName) {
        const authorPhotos = {
            'sergei lukyanenko': 'https://covers.openlibrary.org/a/id/14357752-M.jpg',
            'сергей лукьяненко': 'https://covers.openlibrary.org/a/id/14357752-M.jpg',
            // Add more authors in Russian, e.g., 'чан хо-кей': 'https://example.com/chan.jpg'
        };
        const normalizedAuthor = authorName.trim().toLowerCase(); // Normalize for consistency
        console.log(`Looking for photo for author: ${authorName}, normalized: ${normalizedAuthor}`); // Debug log
        const photoUrl = authorPhotos[normalizedAuthor] || authorPhotos[authorName] || `https://via.placeholder.com/64?text=${encodeURIComponent(authorName)}`;
        console.log(`Selected photo URL: ${photoUrl}`); // Debug log
        return photoUrl;
    }
    render(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }
        container.innerHTML = '';
        if (this.models) {
            this.sortBy('date-desc'); // Sort by read date latest to oldest by default
            const renderedBooks = this.models.map(book => book.render());
            renderedBooks.forEach(div => container.appendChild(div));
        } else {
            console.error('models is undefined in render');
        }
    }
    renderSeriesShelf(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }
        container.innerHTML = '';
        const seriesBooks = {};
        this.allBooks.forEach(book => {
            if (book.Series) { // Include all books with series
                if (!seriesBooks[book.Series]) {
                    seriesBooks[book.Series] = { books: [], author: book.getDisplayAuthor() };
                }
                seriesBooks[book.Series].books.push(book);
                console.log(`Added book to series ${book.Series}: ${book.Title} by ${book.getDisplayAuthor()}`); // Debug log
            }
        });

        for (const [series, data] of Object.entries(seriesBooks)) {
            const { books, author } = data;
            if (books.length === 0) {
                console.warn(`Series ${series} has no books`);
                continue;
            }
            const seriesDiv = document.createElement('div');
            seriesDiv.className = 'series-box';
            seriesDiv.innerHTML = `
                <p class="text-lg font-semibold text-gray-700">${series} (${books.length} книг${books.length > 1 ? 'и' : 'а'})</p>
                <p class="text-gray-600 text-sm mb-2">Автор: ${author}</p>
            `;
            const rowDiv = document.createElement('div');
            rowDiv.className = 'series-row';
            
            books.forEach((book, index) => {
                const bookDiv = document.createElement('div');
                bookDiv.className = 'series-book';
                bookDiv.style.left = `${index * 60}px`;
                bookDiv.style.zIndex = (books.length - index).toString();
                const imgSrc = book.getCoverUrl();
                bookDiv.innerHTML = `
                    <a href="${book.getGoodreadsBookLink()}" target="_blank">
                        <img src="${book.getCoverUrl()}" alt="${book.Title}" 
                             onload="console.log('Loaded cover for ${book.Title} by ${book.getDisplayAuthor()}')"
                             onerror="console.error('Failed to load cover for ${book.Title}: ${imgSrc}'); this.src='https://placehold.co/80x120?text=Нет+обложки'; this.onerror=null;">
                    </a>
                `;
                rowDiv.appendChild(bookDiv);
            });

            seriesDiv.appendChild(rowDiv);
            container.appendChild(seriesDiv);
        }
    }
    renderFutureReads(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }
        container.innerHTML = '';
        if (!this.models || !Array.isArray(this.models)) {
            console.error('models is not an array or is undefined in renderFutureReads');
            return;
        }
        const renderedBooks = this.models.map(book => book.render());
        renderedBooks.forEach(div => container.appendChild(div));
    }
    renderMostProlificAuthor() {
        const [mostProlificAuthor, authorBookCount] = this.getMostProlificAuthor();
        const div = document.createElement('div');
        div.className = 'flex items-center space-x-4';
        const photoUrl = this.getAuthorPhoto(mostProlificAuthor);
        div.innerHTML = `
            <img src="${photoUrl}" alt="${mostProlificAuthor} Photo" class="w-16 h-24 object-cover rounded mr-2">
            <div>
                <h3 class="text-lg font-semibold text-gray-800">${mostProlificAuthor}</h3>
                <p class="text-gray-600 text-sm">${authorBookCount} книг</p>
            </div>
        `;
        return div;
    }
}

fetch('reading_stats.json')
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        // Safely update total-books, total-pages, books-2025 inside the "Всего" block
        const totalBookDiv = document.getElementById('total-book')?.closest('div.w-full');
        if (!totalBookDiv) {
            console.error('Total book container not found');
            return;
        }
        const totalContainer = totalBookDiv.querySelector('.text-left');
        if (!totalContainer) {
            console.error('Text container in "Всего" block not found');
            return;
        }
        const totalBooksElement = totalContainer.querySelector('p:nth-child(1)');
        const totalPagesElement = totalContainer.querySelector('p:nth-child(2)');
        const books2025Element = totalContainer.querySelector('p:nth-child(3) span');

        if (totalBooksElement && totalPagesElement && books2025Element) {
            totalBooksElement.textContent = '14 книг';
            totalPagesElement.textContent = '5 742 страниц';
            books2025Element.textContent = data.books_2025;
        } else {
            console.error('One or more elements in "Всего" block not found:', {
                totalBooksElement,
                totalPagesElement,
                books2025Element
            });
        }

        const allBooks = new BookCollection(data.book_list);
        const books = new BookCollection(data.book_list.filter(book => book['Exclusive Shelf'] === 'read'));
        const currentBooks = new BookCollection(data.book_list.filter(book => book['Exclusive Shelf'] === 'currently-reading'));
        const toReadBooks = new BookCollection(data.book_list.filter(book => book['Exclusive Shelf'] === 'to-read'));
        
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

        // Populate "Любимый автор" with consistent layout
        if (document.getElementById('most-prolific-author')) {
            document.getElementById('most-prolific-author').appendChild(books.renderMostProlificAuthor());
        } else {
            console.error('most-prolific-author element not found');
        }

        // Populate one random read book cover in "Всего"
        const randomReadBook = books.getRandomReadBook();
        if (randomReadBook) {
            const imgElement = document.getElementById('total-book-image');
            if (imgElement) {
                imgElement.src = randomReadBook.getCoverUrl() || 'https://placehold.co/100x150?text=Нет+обложки';
                imgElement.alt = randomReadBook.Title || 'No Title';
            } else {
                console.error('total-book-image element not found');
            }
        } else {
            document.getElementById('total-book').innerHTML = '<p class="text-gray-600">Нет прочитанных книг</p>';
        }

        const challengeGoal = 50;
        const booksRead2025 = data.books_2025;
        const startDate = new Date('2025-01-01');
        const endDate = new Date('2025-12-31');
        const today = new Date('2025-02-26');
        const totalDays = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
        const daysPassed = Math.ceil((today - startDate) / (1000 * 60 * 60 * 24));
        const daysLeft = totalDays - daysPassed;
        const progressPercent = Math.min((booksRead2025 / challengeGoal) * 100, 100).toFixed(0);

        document.getElementById('challenge-progress').innerHTML = `<strong>${booksRead2025} из ${challengeGoal} книг прочитано</strong>`;
        document.getElementById('challenge-days').textContent = `Осталось ${daysLeft} дней`;
        document.getElementById('challenge-bar').style.width = `${progressPercent}%`;
        document.getElementById('challenge-percent').textContent = `${progressPercent}%`;

        books.render('book-list');
        
        const futureReadsBlock = document.getElementById('future-reads-block');
        if (toReadBooks && toReadBooks.models && toReadBooks.models.length > 0) {
            futureReadsBlock.style.display = 'block';
            toReadBooks.renderFutureReads('future-reads');
        } else {
            futureReadsBlock.style.display = 'none';
            console.warn('No to-read books found or models is invalid');
        }
        
        document.getElementById('sort-by').value = 'date-desc';

        const seriesFilter = document.getElementById('series-filter');
        seriesFilter.addEventListener('change', () => {
            books.filterBySeries(seriesFilter.value).render('book-list');
        });
        document.getElementById('sort-by').addEventListener('change', () => {
            books.sortBy(document.getElementById('sort-by').value).render('book-list');
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