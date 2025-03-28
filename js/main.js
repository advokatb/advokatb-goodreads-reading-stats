document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Fetch reading_stats.json
        const response = await fetch('reading_stats.json');
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const data = await response.json();

        // Fetch custom_dates.json
        let customDates = {};
        try {
            const customDatesResponse = await fetch('data/custom_dates.json');
            if (!customDatesResponse.ok) throw new Error(`HTTP error! Status: ${customDatesResponse.status}`);
            customDates = await customDatesResponse.json();
        } catch (error) {
            console.warn('Failed to load custom_dates.json, proceeding without custom dates:', error);
            customDates = { books: {} };
        }

        console.log('Fetched data:', data.book_list.length);

        // Update total-books, total-pages, books-2025 inside the "Всего" block
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
            totalBooksElement.textContent = getBookDeclension(data.total_books);
            totalPagesElement.textContent = `${data.total_pages.toLocaleString('ru-RU')} страниц`;
            books2025Element.textContent = data.books_2025;
        } else {
            console.error('One or more elements in "Всего" block not found:', {
                totalBooksElement,
                totalPagesElement,
                books2025Element
            });
        }

        // Ensure BookCollection is defined
        if (typeof BookCollection === 'undefined') {
            console.error('BookCollection class is not defined. Ensure book_collection.js is loaded correctly.');
            return;
        }

        // Pass customDates to BookCollection
        const allBooks = new BookCollection(data.book_list, customDates);
        const books = new BookCollection(data.book_list.filter(book => book['Exclusive Shelf'] === 'read'), customDates);
        const currentBooks = new BookCollection(data.book_list.filter(book => book['Exclusive Shelf'] === 'currently-reading'), customDates);
        const toReadBooks = new BookCollection(data.book_list.filter(book => book['Exclusive Shelf'] === 'to-read'), customDates);

        // Populate the genre filter dropdown
        const genreFilter = document.getElementById('genre-filter');
        const uniqueGenres = [...new Set(books.allBooks
            .flatMap(book => book.Genres || [])
            .filter(genre => genre && genre.trim()))]
            .sort();
        uniqueGenres.forEach(genre => {
            const option = document.createElement('option');
            option.value = genre;
            option.textContent = genre;
            genreFilter.appendChild(option);
        });

        if (currentBooks.models.length > 0) {
            const currentBookDiv = await currentBooks.models[0].renderCurrent();
            document.getElementById('current-book').appendChild(currentBookDiv);
        } else {
            document.getElementById('current-book').innerHTML = '<p class="text-gray-600">Ничего не читаю сейчас</p>';
        }

        const lastReadBook = books.getLastReadBook();
        if (lastReadBook) {
            const lastReadBookDiv = await lastReadBook.renderCurrent();
            document.getElementById('last-read-book').appendChild(lastReadBookDiv);
        } else {
            document.getElementById('last-read-book').innerHTML = '<p class="text-gray-600">Нет прочитанных книг</p>';
        }

        // Populate "Самый читаемый" with consistent layout
        if (document.getElementById('most-prolific-author')) {
            const mostProlificAuthorDiv = await books.renderMostProlificAuthor();
            document.getElementById('most-prolific-author').appendChild(mostProlificAuthorDiv);
        } else {
            console.error('most-prolific-author element not found');
        }

        // Render the timeline chart
        if (document.getElementById('timelineChart')) {
            await books.renderTimelineChart();
        }

        // Render the rating chart
        if (document.getElementById('ratingChart')) {
            await books.renderRatingChart();
        }

        // Render the genre chart
        if (document.getElementById('genreChart')) {
            await books.renderGenreChart();
        }

        // Populate one random read book cover in "Всего" (without hover tooltip)
        const randomReadBook = books.getRandomReadBook();
        if (randomReadBook) {
            const totalBookDiv = document.getElementById('total-book');
            const imgElement = document.getElementById('total-book-image');
            if (imgElement && totalBookDiv) {
                imgElement.src = randomReadBook.getCoverUrl() || 'https://placehold.co/100x150?text=Нет+обложки';
                imgElement.alt = randomReadBook.Title || 'No Title';
            } else {
                console.error('total-book-image or total-book element not found');
            }
        } else {
            document.getElementById('total-book').innerHTML = '<p class="text-gray-600">Нет прочитанных книг</p>';
        }

        // Populate the "Книжные рекорды" block
        const longestBookElement = document.getElementById('longest-book');
        const shortestBookElement = document.getElementById('shortest-book');
        if (longestBookElement && shortestBookElement) {
            longestBookElement.textContent = `${data.longest_book.Title} (${data.longest_book['Number of Pages']} страниц)`;
            shortestBookElement.textContent = `${data.shortest_book.Title} (${data.shortest_book['Number of Pages']} страниц)`;
        } else {
            console.error('longest-book or shortest-book element not found');
        }

        // Calculate statistics for the "Статистика чтения" block
        const uniqueSeries = [...new Set(books.allBooks
            .filter(book => book.Series && book.Series.trim())
            .map(book => book.Series))]
            .sort();
        const totalSeries = uniqueSeries.length;

        let averageBooksPerMonth = 0;
        if (books.allBooks.length > 0) {
            const dateRanges = books.allBooks
                .filter(book => book['Date Read'])
                .map(book => {
                    const bookTitle = book.Title;
                    const customDateInfo = customDates.books[bookTitle] || {};
                    let startDate, endDate;
        
                    // Normalize date formats
                    const endDateStr = (customDateInfo.custom_end_date || book['Date Read']).replace(/\//g, '-');
                    endDate = new Date(endDateStr);
                    endDate.setHours(0, 0, 0, 0);
        
                    if (customDateInfo.custom_start_date) {
                        const startDateStr = customDateInfo.custom_start_date.replace(/\//g, '-');
                        startDate = new Date(startDateStr);
                        startDate.setHours(0, 0, 0, 0);
                    } else if (book['Date Added']) {
                        const startDateStr = book['Date Added'].replace(/\//g, '-');
                        startDate = new Date(startDateStr);
                        startDate.setHours(0, 0, 0, 0);
                    } else {
                        // Fallback: Estimate start date based on pages (100 pages per day)
                        const pages = book['Number of Pages'] || 300;
                        const daysToRead = Math.ceil(pages / 100);
                        startDate = new Date(endDateStr);
                        startDate.setDate(startDate.getDate() - daysToRead);
                        startDate.setHours(0, 0, 0, 0);
                    }
        
                    return { startDate, endDate };
                })
                .filter(range => !isNaN(range.startDate) && !isNaN(range.endDate));
        
            if (dateRanges.length > 0) {
                const earliestStart = new Date(Math.min(...dateRanges.map(range => range.startDate)));
                const latestEnd = new Date(Math.max(...dateRanges.map(range => range.endDate)));
        
                const monthsDiff = (latestEnd.getFullYear() - earliestStart.getFullYear()) * 12 +
                    (latestEnd.getMonth() - earliestStart.getMonth()) + 1;
        
                if (monthsDiff > 0) {
                    averageBooksPerMonth = (books.allBooks.length / monthsDiff).toFixed(1);
                }
            }
        }

        const totalSeriesElement = document.getElementById('total-series');
        const averageBooksElement = document.getElementById('average-books-per-month');
        if (totalSeriesElement && averageBooksElement) {
            totalSeriesElement.textContent = totalSeries;
            averageBooksElement.textContent = `${averageBooksPerMonth} книг`;
        } else {
            console.error('total-series or average-books-per-month element not found');
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

        // Tab Switching Logic
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabPanes = document.querySelectorAll('.tab-pane');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabPanes.forEach(pane => pane.classList.remove('active'));

                button.classList.add('active');
                const tabId = button.getAttribute('data-tab');
                document.getElementById(tabId).classList.add('active');
            });
        });

        // Initialize books for pagination
        books.currentPage = 0;
        books.booksPerPage = 9;

        // Apply default sorting (date-desc) before rendering the first page
        books.sortBy('date-desc');
        await books.renderPage('book-list');

        // Add "Load More" button event listener
        const loadMoreButton = document.getElementById('load-more');
        loadMoreButton.addEventListener('click', async () => {
            books.currentPage += 1;
            await books.renderPage('book-list');
        });

        // Render future reads in the "Будущие книги" tab
        if (toReadBooks && toReadBooks.models && toReadBooks.models.length > 0) {
            await toReadBooks.renderFutureReads('future-reads');
        } else {
            document.getElementById('future-reads').innerHTML = '<p class="text-gray-600">Нет книг для чтения</p>';
            console.warn('No to-read books found or models is invalid');
        }

        // Set the default sort value in the dropdown
        document.getElementById('sort-by').value = 'date-desc';

        // Combine genre and sort filters for "Прочитанные книги"
        const applyFilters = async () => {
            let filteredBooks = books;
            const selectedGenre = genreFilter.value;

            // Apply genre filter
            filteredBooks = filteredBooks.filterByGenre(selectedGenre);

            // Apply sorting
            const sortValue = document.getElementById('sort-by').value;
            filteredBooks = filteredBooks.sortBy(sortValue);

            // Reset pagination and render
            filteredBooks.currentPage = 0;
            await filteredBooks.renderPage('book-list');
        };

        genreFilter.addEventListener('change', applyFilters);
        document.getElementById('sort-by').addEventListener('change', applyFilters);

        await allBooks.renderSeriesShelf('series-shelf');
    } catch (error) {
        console.error('Fetch error:', error);
    }
});