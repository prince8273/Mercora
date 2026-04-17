import { useState } from 'react';
import styles from './ReviewCard.module.css';

export default function ReviewCard({ review }) {
  const [isHelpful, setIsHelpful] = useState(false);

  const getSentimentLabel = (sentiment) => {
    switch (sentiment) {
      case 'positive':
        return '😊 Positive';
      case 'negative':
        return '😞 Negative';
      default:
        return '😐 Neutral';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Invalid Date';
    const date = new Date(dateString);
    if (isNaN(date)) return 'Invalid Date';
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <div className={styles.rating}>
            {[...Array(5)].map((_, i) => (
              <span key={i} className={`${styles.star} ${i >= review.rating ? styles.empty : ''}`}>
                ★
              </span>
            ))}
          </div>
          {review.title && <h3 className={styles.title}>{review.title}</h3>}
          <div className={styles.meta}>
            <span>{review.author || 'Anonymous'}</span>
            <span>•</span>
            <span>{formatDate(review.date || review.created_at)}</span>
          </div>
        </div>
        <div className={`${styles.sentiment} ${styles[review.sentiment]}`}>
          {getSentimentLabel(review.sentiment)}
        </div>
      </div>

      <p className={styles.text}>{review.text}</p>

      <div className={styles.footer}>
        {review.verified && (
          <div className={styles.verified}>
            <span>✓</span>
            <span>Verified Purchase</span>
          </div>
        )}
        <div className={styles.helpful}>
          <span>{review.helpfulVotes || 0} people found this helpful</span>
          <button
            className={styles.helpfulButton}
            onClick={() => setIsHelpful(!isHelpful)}
          >
            {isHelpful ? '✓ Helpful' : 'Helpful?'}
          </button>
        </div>
      </div>
    </div>
  );
}
