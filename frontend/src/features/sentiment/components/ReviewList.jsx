import { useState, useMemo } from 'react';
import { SearchBar } from '../../../components/molecules/SearchBar/SearchBar';
import ReviewCard from './ReviewCard';
import styles from './ReviewList.module.css';

const ITEMS_PER_PAGE = 20;

export default function ReviewList({ data, isLoading }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [sentimentFilter, setSentimentFilter] = useState('all');
  const [ratingFilter, setRatingFilter] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [currentPage, setCurrentPage] = useState(1);

  const filteredReviews = useMemo(() => {
    if (!data?.reviews) return [];

    let filtered = [...data.reviews];

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(
        (review) =>
          review.text?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          review.title?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Sentiment filter
    if (sentimentFilter !== 'all') {
      filtered = filtered.filter((review) => review.sentiment === sentimentFilter);
    }

    // Rating filter
    if (ratingFilter !== 'all') {
      const rating = parseInt(ratingFilter);
      filtered = filtered.filter((review) => review.rating === rating);
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'date':
          return new Date(b.date) - new Date(a.date);
        case 'rating':
          return b.rating - a.rating;
        case 'helpfulness':
          return (b.helpfulVotes || 0) - (a.helpfulVotes || 0);
        default:
          return 0;
      }
    });

    return filtered;
  }, [data, searchQuery, sentimentFilter, ratingFilter, sortBy]);

  const totalPages = Math.ceil(filteredReviews.length / ITEMS_PER_PAGE);
  const paginatedReviews = filteredReviews.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const handlePageChange = (page) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (!data?.reviews || data.reviews.length === 0) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <h2 className={styles.title}>Customer Reviews</h2>
        </div>
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>💬</div>
          <p>No reviews available</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>
          Customer Reviews ({filteredReviews.length})
        </h2>
        <div className={styles.filters}>
          <div className={styles.searchBar}>
            <SearchBar
              placeholder="Search reviews..."
              onSearch={setSearchQuery}
              debounceMs={300}
            />
          </div>
          <select
            className={styles.filterSelect}
            value={sentimentFilter}
            onChange={(e) => {
              setSentimentFilter(e.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="all">All Sentiments</option>
            <option value="positive">Positive</option>
            <option value="neutral">Neutral</option>
            <option value="negative">Negative</option>
          </select>
          <select
            className={styles.filterSelect}
            value={ratingFilter}
            onChange={(e) => {
              setRatingFilter(e.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="all">All Ratings</option>
            <option value="5">5 Stars</option>
            <option value="4">4 Stars</option>
            <option value="3">3 Stars</option>
            <option value="2">2 Stars</option>
            <option value="1">1 Star</option>
          </select>
          <select
            className={styles.filterSelect}
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="date">Most Recent</option>
            <option value="rating">Highest Rating</option>
            <option value="helpfulness">Most Helpful</option>
          </select>
        </div>
      </div>

      <div className={styles.reviewsList}>
        {paginatedReviews.map((review) => (
          <ReviewCard key={review.id} review={review} />
        ))}
      </div>

      {totalPages > 1 && (
        <div className={styles.pagination}>
          <div className={styles.paginationInfo}>
            Showing {(currentPage - 1) * ITEMS_PER_PAGE + 1} -{' '}
            {Math.min(currentPage * ITEMS_PER_PAGE, filteredReviews.length)} of{' '}
            {filteredReviews.length} reviews
          </div>
          <div className={styles.paginationButtons}>
            <button
              className={styles.pageButton}
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              Previous
            </button>
            {[...Array(Math.min(5, totalPages))].map((_, i) => {
              const page = i + 1;
              return (
                <button
                  key={page}
                  className={`${styles.pageButton} ${
                    currentPage === page ? styles.active : ''
                  }`}
                  onClick={() => handlePageChange(page)}
                >
                  {page}
                </button>
              );
            })}
            {totalPages > 5 && <span>...</span>}
            <button
              className={styles.pageButton}
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
