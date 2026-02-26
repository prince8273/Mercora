import React, { useState, useEffect } from 'react';
import { SearchBar } from '../SearchBar';
import { Badge } from '../../atoms/Badge';
import styles from './ProductSelector.module.css';

export const ProductSelector = ({
  products = [],
  selected = [],
  onChange,
  multiple = false,
  loading = false,
  placeholder = 'Search products...',
  className = '',
  ...props
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredProducts, setFilteredProducts] = useState(products);

  useEffect(() => {
    if (searchQuery) {
      const filtered = products.filter((product) =>
        product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        product.sku?.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredProducts(filtered);
    } else {
      setFilteredProducts(products);
    }
  }, [searchQuery, products]);

  const handleToggle = (productId) => {
    if (multiple) {
      const newSelected = selected.includes(productId)
        ? selected.filter((id) => id !== productId)
        : [...selected, productId];
      onChange?.(newSelected);
    } else {
      onChange?.([productId]);
      setIsOpen(false);
    }
  };

  const handleRemove = (productId) => {
    onChange?.(selected.filter((id) => id !== productId));
  };

  const getProductName = (productId) => {
    const product = products.find((p) => p.id === productId);
    return product?.name || productId;
  };

  const selectedProducts = products.filter((p) => selected.includes(p.id));

  return (
    <div className={`${styles.container} ${className}`} {...props}>
      <button
        type="button"
        className={styles.trigger}
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <span>
          {selected.length > 0
            ? multiple
              ? `${selected.length} product${selected.length > 1 ? 's' : ''} selected`
              : getProductName(selected[0])
            : 'Select product'}
        </span>
        <svg className={styles.chevron} viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>

      {isOpen && (
        <div className={styles.dropdown}>
          <div className={styles.searchContainer}>
            <SearchBar
              onSearch={setSearchQuery}
              placeholder={placeholder}
              loading={loading}
            />
          </div>
          <div className={styles.productList}>
            {filteredProducts.length > 0 ? (
              filteredProducts.map((product) => (
                <label
                  key={product.id}
                  className={`${styles.productItem} ${
                    selected.includes(product.id) ? styles.selected : ''
                  }`}
                >
                  <input
                    type={multiple ? 'checkbox' : 'radio'}
                    checked={selected.includes(product.id)}
                    onChange={() => handleToggle(product.id)}
                    className={styles.checkbox}
                  />
                  {product.image && (
                    <img
                      src={product.image}
                      alt={product.name}
                      className={styles.productImage}
                    />
                  )}
                  <div className={styles.productInfo}>
                    <div className={styles.productName}>{product.name}</div>
                    {product.sku && (
                      <div className={styles.productSku}>SKU: {product.sku}</div>
                    )}
                  </div>
                  {product.price && (
                    <div className={styles.productPrice}>${product.price}</div>
                  )}
                </label>
              ))
            ) : (
              <div className={styles.emptyState}>
                {loading ? 'Loading products...' : 'No products found'}
              </div>
            )}
          </div>
        </div>
      )}

      {selected.length > 0 && multiple && (
        <div className={styles.selectedProducts}>
          {selectedProducts.map((product) => (
            <Badge key={product.id} variant="primary" className={styles.badge}>
              {product.name}
              <button
                type="button"
                onClick={() => handleRemove(product.id)}
                className={styles.removeButton}
                aria-label={`Remove ${product.name}`}
              >
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
};
