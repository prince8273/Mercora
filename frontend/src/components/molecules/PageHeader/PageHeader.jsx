import React from 'react';
import styles from './PageHeader.module.css';

export const PageHeader = ({
  title,
  breadcrumbs = [],
  actions,
  subtitle,
  className = '',
  ...props
}) => {
  return (
    <div className={`${styles.header} ${className}`} {...props}>
      <div className={styles.content}>
        {breadcrumbs.length > 0 && (
          <nav className={styles.breadcrumbs} aria-label="Breadcrumb">
            <ol className={styles.breadcrumbList}>
              {breadcrumbs.map((crumb, index) => (
                <li key={index} className={styles.breadcrumbItem}>
                  {crumb.href ? (
                    <a href={crumb.href} className={styles.breadcrumbLink}>
                      {crumb.label}
                    </a>
                  ) : (
                    <span className={styles.breadcrumbCurrent}>{crumb.label}</span>
                  )}
                  {index < breadcrumbs.length - 1 && (
                    <svg
                      className={styles.breadcrumbSeparator}
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path
                        fillRule="evenodd"
                        d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </li>
              ))}
            </ol>
          </nav>
        )}
        <div className={styles.titleRow}>
          <div className={styles.titleContainer}>
            <h1 className={styles.title}>{title}</h1>
            {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
          </div>
          {actions && <div className={styles.actions}>{actions}</div>}
        </div>
      </div>
    </div>
  );
};
