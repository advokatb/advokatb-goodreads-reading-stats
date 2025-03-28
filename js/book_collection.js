class BookCollection {
    constructor(books) {
        this.models = books ? books.map(book => new Book(book)) : [];
        this.allBooks = [...this.models];
        console.log(`BookCollection initialized with ${this.allBooks.length} books`);
        if (this.allBooks.length === 0) {
            console.error('No books loaded in BookCollection');
        }
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

    async getSeriesWithAuthors() {
        const seriesAuthors = {};
        for (const book of this.allBooks) {
            if (book.Series && book.Series.trim()) {
                const author = await book.getDisplayAuthor();
                if (!seriesAuthors[book.Series]) {
                    seriesAuthors[book.Series] = new Set();
                }
                seriesAuthors[book.Series].add(author);
            }
        }
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

    async getMostProlificAuthor() {
        if (!this.allBooks.length) return ['Нет данных', 0];
        const authorCounts = {};
        for (const book of this.allBooks) {
            if (book['Exclusive Shelf'] === 'read') {
                const displayAuthor = await book.getDisplayAuthor();
                authorCounts[displayAuthor] = (authorCounts[displayAuthor] || 0) + 1;
            }
        }
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

    async getAuthorPhoto(authorName) {
        const response = await fetch('data/author_photos.json');
        const authorPhotos = await response.json();
        const normalizedAuthor = authorName.trim().toLowerCase();
        console.log(`Looking for photo for author: ${authorName}, normalized: ${normalizedAuthor}`);
        const photoUrl = authorPhotos[normalizedAuthor] || authorPhotos[authorName] || `https://via.placeholder.com/64?text=${encodeURIComponent(authorName)}`;
        console.log(`Selected photo URL: ${photoUrl}`);
        return photoUrl;
    }

    async render(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }
        container.innerHTML = '';
        if (this.models) {
            this.sortBy('date-desc');
            const renderedBooks = await Promise.all(this.models.map(book => book.render()));
            renderedBooks.forEach(div => container.appendChild(div));
        } else {
            console.error('models is undefined in render');
        }
    }

    async renderSeriesShelf(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }
        container.innerHTML = '';
        console.log(`Rendering series shelf with ${this.allBooks.length} total books`);
        if (this.allBooks.length === 0) {
            container.innerHTML = '<p class="text-gray-600">Нет данных о сериях</p>';
            console.warn('No books available to render series');
            return;
        }
        const readBooks = this.allBooks.filter(book => book['Exclusive Shelf'] === 'read');
        if (readBooks.length === 0) {
            container.innerHTML = '<p class="text-gray-600">Нет прочитанных книг в сериях</p>';
            console.warn('No read books available to render series');
            return;
        }
        const seriesBooks = {};
        for (const book of readBooks) {
            console.log(`Processing book: ${book.Title}, Series: ${book.Series}`);
            if (book.Series && book.Series.trim()) {
                const author = await book.getDisplayAuthor();
                if (!seriesBooks[book.Series]) {
                    seriesBooks[book.Series] = { books: [], author };
                }
                seriesBooks[book.Series].books.push(book);
                console.log(`Added book to series ${book.Series}: ${book.Title} by ${author}`);
            } else {
                console.log(`Skipping book ${book.Title} due to empty or invalid Series: ${book.Series}`);
            }
        }

        if (Object.keys(seriesBooks).length === 0) {
            container.innerHTML = '<p class="text-gray-600">Нет серий для отображения</p>';
            console.warn('No series found in read books');
            return;
        }

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
                             onload="console.log('Loaded cover for ${book.Title} by ${author}')"
                             onerror="console.error('Failed to load cover for ${book.Title}: ${imgSrc}'); this.src='https://placehold.co/80x120?text=Нет+обложки'; this.onerror=null;">
                    </a>
                `;
                rowDiv.appendChild(bookDiv);
            });

            seriesDiv.appendChild(rowDiv);
            container.appendChild(seriesDiv);
        }
    }

    async renderFutureReads(containerId) {
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
        const renderedBooks = await Promise.all(this.models.map(book => book.render()));
        renderedBooks.forEach(div => container.appendChild(div));
    }

    async renderMostProlificAuthor() {
        const [mostProlificAuthor, authorBookCount] = await this.getMostProlificAuthor();
    
        // Calculate the most read genre for the most prolific author
        const booksByAuthor = this.allBooks.filter(book => book['Exclusive Shelf'] === 'read' && book.getDisplayAuthor().then(author => author === mostProlificAuthor));
        const genreCounts = {};
    
        // Since getDisplayAuthor is async, we need to await it for each book
        for (const book of this.allBooks) {
            if (book['Exclusive Shelf'] === 'read') {
                const displayAuthor = await book.getDisplayAuthor();
                if (displayAuthor === mostProlificAuthor) {
                    const genres = book.Genres || [];
                    genres.forEach(genre => {
                        genreCounts[genre] = (genreCounts[genre] || 0) + 1;
                    });
                }
            }
        }
    
        // Find the genre with the highest count
        let mostReadGenre = 'Неизвестно';
        let maxCount = 0;
        for (const [genre, count] of Object.entries(genreCounts)) {
            if (count > maxCount) {
                mostReadGenre = genre;
                maxCount = count;
            }
        }
    
        // Render the block
        const div = document.createElement('div');
        div.className = 'flex items-start space-x-4';
        const photoUrl = await this.getAuthorPhoto(mostProlificAuthor);
        div.innerHTML = `
            <img src="${photoUrl}" alt="${mostProlificAuthor} Photo" class="w-16 h-24 object-cover rounded mr-2">
            <div class="flex-1">
                <p class="text-gray-600 text-sm font-semibold">Автор</p>
                <p class="text-lg font-semibold text-gray-800">${mostProlificAuthor}</p>
                <p class="text-gray-600 text-sm">${authorBookCount} книг</p>
                <hr class="my-2 border-gray-300">
                <p class="text-gray-600 text-sm font-semibold">Жанр</p>
                <p class="text-gray-600 text-sm">${mostReadGenre}</p>
            </div>
        `;
        return div;
    }
}