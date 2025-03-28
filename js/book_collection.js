class BookCollection {
    constructor(books) {
        this.models = books ? books.map(book => new Book(book)) : [];
        this.allBooks = [...this.models];
        console.log(`BookCollection initialized with ${this.allBooks.length} books`);
        if (this.allBooks.length === 0) {
            console.error('No books loaded in BookCollection');
        }
    }

    // Existing methods (filterBySeries, sortBy, getSeriesWithAuthors, etc.) remain unchanged...

    async renderMostProlificAuthor() {
        const [mostProlificAuthor, authorBookCount] = await this.getMostProlificAuthor();
        const genreCounts = {};
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
        let mostReadGenre = 'Неизвестно';
        let maxCount = 0;
        for (const [genre, count] of Object.entries(genreCounts)) {
            if (count > maxCount) {
                mostReadGenre = genre;
                maxCount = count;
            }
        }
        const div = document.createElement('div');
        div.className = 'flex items-start space-x-4';
        const photoUrl = await this.getAuthorPhoto(mostProlificAuthor);
        div.innerHTML = `
            <img src="${photoUrl}" alt="${mostProlificAuthor} Photo" class="w-16 h-24 object-cover rounded mr-2">
            <div class="flex-1">
                <p class="text-gray-700 text-base font-bold mb-1">Автор: ${mostProlificAuthor}</p>
                <p class="text-gray-600 text-sm mb-2">${authorBookCount} книг</p>
                <hr class="my-2 border-gray-300">
                <p class="text-gray-700 text-base font-bold mb-1">Жанр: ${mostReadGenre}</p>
            </div>
        `;
        return div;
    }

    // New method: Render the rating distribution chart
    async renderRatingChart() {
        const ratingCounts = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
        for (const book of this.allBooks) {
            if (book['Exclusive Shelf'] === 'read' && book['My Rating'] > 0) {
                ratingCounts[book['My Rating']] = (ratingCounts[book['My Rating']] || 0) + 1;
            }
        }

        const seriesData = Object.values(ratingCounts);
        const labels = Object.keys(ratingCounts).map(rating => {
            const stars = '★'.repeat(rating) + '☆'.repeat(5 - rating);
            return `${stars} (${ratingCounts[rating]})`;
        });

        const options = {
            chart: {
                type: 'bar',
                height: 200,
                toolbar: { show: false }
            },
            series: [{
                name: 'Количество книг',
                data: seriesData
            }],
            xaxis: {
                categories: labels,
                labels: {
                    style: {
                        fontSize: '12px',
                        colors: Array(5).fill('#4B5563') // text-gray-600
                    }
                }
            },
            yaxis: {
                title: {
                    text: 'Количество книг',
                    style: {
                        fontSize: '14px',
                        fontWeight: 600,
                        color: '#374151' // text-gray-700
                    }
                },
                labels: {
                    style: {
                        fontSize: '12px',
                        colors: '#4B5563' // text-gray-600
                    }
                }
            },
            plotOptions: {
                bar: {
                    horizontal: false,
                    columnWidth: '55%',
                    endingShape: 'rounded'
                }
            },
            dataLabels: {
                enabled: true,
                formatter: val => val > 0 ? val : '',
                style: {
                    fontSize: '12px',
                    colors: ['#fff']
                }
            },
            colors: ['#4F46E5'], // Indigo-600
            tooltip: {
                y: {
                    formatter: val => `${val} книг`
                }
            }
        };

        const chart = new ApexCharts(document.querySelector("#ratingChart"), options);
        chart.render();
    }

    // New method: Render the most read genres chart
    async renderGenreChart() {
        const genreCounts = {};
        for (const book of this.allBooks) {
            if (book['Exclusive Shelf'] === 'read') {
                const genres = book.Genres || [];
                genres.forEach(genre => {
                    genreCounts[genre] = (genreCounts[genre] || 0) + 1;
                });
            }
        }

        // Filter out genres with 0 counts and sort by count (descending)
        const sortedGenres = Object.entries(genreCounts)
            .filter(([_, count]) => count > 0)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5); // Limit to top 5 genres for better visualization

        const labels = sortedGenres.map(([genre]) => genre);
        const seriesData = sortedGenres.map(([_, count]) => count);

        const options = {
            chart: {
                type: 'pie',
                height: 200,
                toolbar: { show: false }
            },
            series: seriesData,
            labels: labels,
            colors: ['#4F46E5', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'], // Indigo-600, Emerald-500, Amber-500, Red-500, Purple-500
            legend: {
                position: 'bottom',
                fontSize: '12px',
                labels: {
                    colors: '#4B5563' // text-gray-600
                }
            },
            dataLabels: {
                enabled: true,
                formatter: (val, opts) => {
                    const count = opts.w.config.series[opts.seriesIndex];
                    return `${count} книг`;
                },
                style: {
                    fontSize: '12px',
                    colors: ['#fff']
                }
            },
            tooltip: {
                y: {
                    formatter: val => `${val} книг`
                }
            }
        };

        const chart = new ApexCharts(document.querySelector("#genreChart"), options);
        chart.render();
    }
}