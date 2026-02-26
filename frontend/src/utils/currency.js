/**
 * Currency formatting utilities
 * Centralized place to manage currency display across the application
 */

// Currency configuration
const CURRENCY_CONFIG = {
  code: 'INR',        // Change to 'USD' for dollars, 'INR' for rupees
  locale: 'en-IN',    // Change to 'en-US' for US format, 'en-IN' for Indian format
  symbol: '₹',        // Currency symbol (optional, auto-detected from code)
  exchangeRate: 83.5, // USD to INR exchange rate (update as needed)
  convertFromUSD: true, // Set to true to convert USD values to INR
};

/**
 * Convert USD to target currency if needed
 * @param {number} value - Value in USD
 * @returns {number} Converted value
 */
const convertCurrency = (value) => {
  if (!CURRENCY_CONFIG.convertFromUSD || CURRENCY_CONFIG.code === 'USD') {
    return value;
  }
  return value * CURRENCY_CONFIG.exchangeRate;
};

/**
 * Format a number as currency
 * @param {number} value - The value to format (in USD if convertFromUSD is true)
 * @param {object} options - Formatting options
 * @returns {string} Formatted currency string
 */
export const formatCurrency = (value, options = {}) => {
  const {
    minimumFractionDigits = 0,
    maximumFractionDigits = 0,
    locale = CURRENCY_CONFIG.locale,
    currency = CURRENCY_CONFIG.code,
  } = options;

  if (value === null || value === undefined || isNaN(value)) {
    return '—';
  }

  // Convert currency if needed
  const convertedValue = convertCurrency(value);

  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency,
    minimumFractionDigits,
    maximumFractionDigits,
  }).format(convertedValue);
};

/**
 * Format currency with 2 decimal places (for prices)
 */
export const formatPrice = (value) => {
  return formatCurrency(value, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
};

/**
 * Format currency with no decimal places (for large amounts)
 */
export const formatAmount = (value) => {
  return formatCurrency(value, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
};

/**
 * Get currency symbol
 */
export const getCurrencySymbol = () => {
  return CURRENCY_CONFIG.symbol;
};

/**
 * Get currency code
 */
export const getCurrencyCode = () => {
  return CURRENCY_CONFIG.code;
};

/**
 * Get exchange rate
 */
export const getExchangeRate = () => {
  return CURRENCY_CONFIG.exchangeRate;
};

export default {
  formatCurrency,
  formatPrice,
  formatAmount,
  getCurrencySymbol,
  getCurrencyCode,
  getExchangeRate,
};
