document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Fetch reading_stats.json
        const response = await fetch('reading_stats.json');
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const data = await response.json();

        // Fetch custom_dates.json
        let customDates = {};
        try {
            const customDatesResponse = await fetch('custom_dates.json');
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

        const allBooks = new BookCollection(data.book_list);
        const books = new BookCollection(data.book_list.filter(book => book['Exclusive Shelf'] === 'read'));
        const currentBooks = new BookCollection(data.book_list.filter(book => book['Exclusive Shelf'] === 'currently-reading'));
        const toReadBooks = new BookCollection(data.book_list.filter(book => book['Exclusive Shelf'] === 'to-read'));

        // Populate the series filter dropdown
        const seriesFilter = document.getElementById('series-filter');
        const uniqueSeries = [...new Set(books.allBooks
            .filter(book => book.Series && book.Series.trim())
            .map(book => book.Series))]
            .sort();
        uniqueSeries.forEach(series => {
            const option = document.createElement('option');
            option.value = series;
            option.textContent = series;
            seriesFilter.appendChild(option);
        });

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
        // 1. Total series read (Циклов прочитано всего)
        const totalSeries = uniqueSeries.length; // Already calculated for series filter

        // 2. Average books read per month (В среднем прочитано в месяц)
        let averageBooksPerMonth = 0;
        if (books.allBooks.length > 0) {
            // Collect all start and end dates for the books
            const dateRanges = books.allBooks
                .filter(book => book['Date Read']) // Ensure the book has a Date Read
                .map(book => {
                    const bookTitle = book.Title;
                    const customDateInfo = customDates.books[bookTitle] || {};
                    let startDate, endDate;

                    // End date: Use custom_end_date if provided, otherwise use Date Read
                    endDate = customDateInfo.custom_end_date
                        ? new Date(customDateInfo.custom_end_date)
                        : new Date(book['Date Read']);

                    // Start date: Use custom_start_date if provided, otherwise estimate
                    if (customDateInfo.custom_start_date) {
                        startDate = new Date(customDateInfo.custom_start_date);
                    } else {
                        // Estimate start date by subtracting reading duration
                        // Assume 100 pages per day as a rough estimate
                        const pages = book['Number of Pages'] || 300; // Default to 300 if pages not specified
                        const daysToRead = Math.ceil(pages / 100);
                        startDate = new Date(book['Date Read']);
                        startDate.setDate(startDate.getDate() - daysToRead);
                    }

                    return { startDate, endDate };
                })
                .filter(range => !isNaN(range.startDate) && !isNaN(range.endDate));

            if (dateRanges.length > 0) {
                // Find the earliest start date and latest end date
                const earliestStart = new Date(Math.min(...dateRanges.map(range => range.startDate)));
                const latestEnd = new Date(Math.max(...dateRanges.map(range => range.endDate)));

                // Calculate the number of months between the earliest start and latest end
                const monthsDiff = (latestEnd.getFullYear() - earliestStart.getFullYear()) * 12 +
                    (latestEnd.getMonth() - earliestStart.getMonth()) + 1; // +1 to include the start month

                if (monthsDiff > 0) {
                    averageBooksPerMonth = (books.allBooks.length / monthsDiff).toFixed(1);
                }
            }
        }

        // Populate the "Статистика чтения" block
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

        await books.render('book-list');
        
        const futureReadsBlock = document.getElementById('future-reads-block');
        if (toReadBooks && toReadBooks.models && toReadBooks.models.length > 0) {
            futureReadsBlock.style.display = 'block';
            await toReadBooks.renderFutureReads('future-reads');
        } else {
            futureReadsBlock.style.display = 'none';
            console.warn('No to-read books found or models is invalid');
        }
        
        document.getElementById('sort-by').value = 'date-desc';

        // Combine series and genre filters
        const applyFilters = async () => {
            let filteredBooks = books;
            const selectedSeries = seriesFilter.value;
            const selectedGenre = genreFilter.value;

            // Apply series filter
            filteredBooks = filteredBooks.filterBySeries(selectedSeries);

            // Apply genre filter
            filteredBooks = filteredBooks.filterByGenre(selectedGenre);

            // Apply sorting
            const sortValue = document.getElementById('sort-by').value;
            filteredBooks = filteredBooks.sortBy(sortValue);

            // Render the filtered and sorted list
            await filteredBooks.render('book-list');
        };

        seriesFilter.addEventListener('change', applyFilters);
        genreFilter.addEventListener('change', applyFilters);
        document.getElementById('sort-by').addEventListener('change', applyFilters);

        await allBooks.renderSeriesShelf('series-shelf');
    } catch (error) {
        console.error('Fetch error:', error);
    }
});