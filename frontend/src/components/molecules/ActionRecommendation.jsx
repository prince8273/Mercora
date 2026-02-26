import React, { useState } from 'react';
import { Button } from '../atoms/Button';
import { ConfidenceScore } from '../atoms/ConfidenceScore';
import styles from './ActionRecommendation.module.css';

export const ActionRecommendation = ({
  action = {},
  onAccept,
  onSnooze,
  onReject,
  className = '',
  ...props
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const {
    id,
    title,
    priority = 'medium',
    effort = 'medium',
    impact = 'medium',
    description,
    reasoning,
    steps = [],
    deadline,
    estimatedCost,
    expectedReturn,
    confidence,
  } = action;

  const getPriorityColor = (priority) => {
    const colors = {
      high: 'red',
      medium: 'yellow',
      low: 'green',
    };
    return colors[priority?.toLowerCase()] || 'gray';
  };

  const getEffortIcon = (effort) => {
    const effortLevel = effort?.toLowerCase();
    if (effortLevel === 'low') return '●';
    if (effortLevel === 'medium') return '●●';
    if (effortLevel === 'high') return '●●●';
    return '●';
  };

  const getImpactIcon = (impact) => {
    const impactLevel = impact?.toLowerCase();
    if (impactLevel === 'low') return '▲';
    if (impactLevel === 'medium') return '▲▲';
    if (impactLevel === 'high') return '▲▲▲';
    return '▲';
  };

  const handleAccept = async () => {
    if (!onAccept) return;
    setIsProcessing(true);
    try {
      await onAccept(action);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSnooze = async () => {
    if (!onSnooze) return;
    setIsProcessing(true);
    try {
      await onSnooze(action);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!onReject) return;
    setIsProcessing(true);
    try {
      await onReject(action);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      <div className={styles.header}>
        <div className={styles.headerTop}>
          <div className={styles.badges}>
            <span className={`${styles.priorityBadge} ${styles[`priority-${getPriorityColor(priority)}`]}`}>
              {priority} priority
            </span>
            <span className={styles.effortBadge} title={`${effort} effort`}>
              {getEffortIcon(effort)} {effort}
            </span>
            <span className={styles.impactBadge} title={`${impact} impact`}>
              {getImpactIcon(impact)} {impact}
            </span>
          </div>
          {confidence && (
            <ConfidenceScore score={confidence} size="sm" showLabel={false} />
          )}
        </div>
        <h4 className={styles.title}>{title}</h4>
        {description && <p className={styles.description}>{description}</p>}
      </div>

      {reasoning && (
        <div className={styles.reasoning}>
          <div className={styles.reasoningHeader}>
            <svg className={styles.reasoningIcon} viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <span className={styles.reasoningLabel}>Why this matters:</span>
          </div>
          <p className={styles.reasoningText}>{reasoning}</p>
        </div>
      )}

      {isExpanded && (
        <div className={styles.expandedContent}>
          {steps && steps.length > 0 && (
            <div className={styles.steps}>
              <h5 className={styles.stepsTitle}>Action Steps:</h5>
              <ol className={styles.stepsList}>
                {steps.map((step, index) => (
                  <li key={index} className={styles.stepItem}>
                    {step}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {(estimatedCost || expectedReturn || deadline) && (
            <div className={styles.details}>
              {estimatedCost && (
                <div className={styles.detailItem}>
                  <span className={styles.detailLabel}>Estimated Cost:</span>
                  <span className={styles.detailValue}>
                    ${estimatedCost.toLocaleString()}
                  </span>
                </div>
              )}
              {expectedReturn && (
                <div className={styles.detailItem}>
                  <span className={styles.detailLabel}>Expected Return:</span>
                  <span className={styles.detailValue}>
                    ${expectedReturn.toLocaleString()}
                  </span>
                </div>
              )}
              {deadline && (
                <div className={styles.detailItem}>
                  <span className={styles.detailLabel}>Deadline:</span>
                  <span className={styles.detailValue}>{deadline}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      <div className={styles.actions}>
        <button
          className={styles.expandButton}
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
        >
          {isExpanded ? 'Show Less' : 'Show More'}
          <svg
            className={`${styles.expandIcon} ${isExpanded ? styles.expanded : ''}`}
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>

        <div className={styles.actionButtons}>
          {onReject && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleReject}
              disabled={isProcessing}
              className={styles.rejectButton}
            >
              Reject
            </Button>
          )}
          {onSnooze && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleSnooze}
              disabled={isProcessing}
              className={styles.snoozeButton}
            >
              Snooze
            </Button>
          )}
          {onAccept && (
            <Button
              variant="primary"
              size="sm"
              onClick={handleAccept}
              disabled={isProcessing}
              className={styles.acceptButton}
            >
              {isProcessing ? 'Processing...' : 'Accept'}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
