import { useState, useEffect } from 'react';
import styles from './PreferencesPanel.module.css';

export default function PreferencesPanel({ initialPreferences, onSave }) {
  const [preferences, setPreferences] = useState({
    theme: 'system',
    language: 'en',
    dateFormat: 'MM/DD/YYYY',
    defaultDateRange: '30d',
    notifications: {
      email: true,
      push: false,
      alerts: true,
      reports: true,
    },
    ...initialPreferences,
  });

  const [isSaving, setIsSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    const hasChanged = JSON.stringify(preferences) !== JSON.stringify(initialPreferences);
    setHasChanges(hasChanged);
  }, [preferences, initialPreferences]);

  const handleThemeChange = (theme) => {
    setPreferences({ ...preferences, theme });
  };

  const handleInputChange = (field, value) => {
    setPreferences({ ...preferences, [field]: value });
  };

  const handleNotificationChange = (key, value) => {
    setPreferences({
      ...preferences,
      notifications: {
        ...preferences.notifications,
        [key]: value,
      },
    });
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSave?.(preferences);
      setShowSuccess(true);
      setHasChanges(false);
      setTimeout(() => setShowSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to save preferences:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setPreferences(initialPreferences);
    setHasChanges(false);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>User Preferences</h2>
        <p className={styles.subtitle}>Customize your experience</p>
      </div>

      <form className={styles.form} onSubmit={(e) => e.preventDefault()}>
        {/* Theme Selection */}
        <div className={styles.formGroup}>
          <label className={styles.label}>Theme</label>
          <div className={styles.themeOptions}>
            <div
              className={`${styles.themeOption} ${
                preferences.theme === 'light' ? styles.selected : ''
              }`}
              onClick={() => handleThemeChange('light')}
            >
              <div className={styles.themeIcon}>☀️</div>
              <div className={styles.themeName}>Light</div>
            </div>
            <div
              className={`${styles.themeOption} ${
                preferences.theme === 'dark' ? styles.selected : ''
              }`}
              onClick={() => handleThemeChange('dark')}
            >
              <div className={styles.themeIcon}>🌙</div>
              <div className={styles.themeName}>Dark</div>
            </div>
            <div
              className={`${styles.themeOption} ${
                preferences.theme === 'system' ? styles.selected : ''
              }`}
              onClick={() => handleThemeChange('system')}
            >
              <div className={styles.themeIcon}>💻</div>
              <div className={styles.themeName}>System</div>
            </div>
          </div>
          <p className={styles.description}>Choose your preferred color scheme</p>
        </div>

        {/* Language */}
        <div className={styles.formGroup}>
          <label className={styles.label} htmlFor="language">
            Language
          </label>
          <select
            id="language"
            className={styles.select}
            value={preferences.language}
            onChange={(e) => handleInputChange('language', e.target.value)}
          >
            <option value="en">English</option>
            <option value="es">Español</option>
            <option value="fr">Français</option>
            <option value="de">Deutsch</option>
            <option value="zh">中文</option>
          </select>
          <p className={styles.description}>Select your preferred language</p>
        </div>

        {/* Date Format */}
        <div className={styles.formGroup}>
          <label className={styles.label} htmlFor="dateFormat">
            Date Format
          </label>
          <select
            id="dateFormat"
            className={styles.select}
            value={preferences.dateFormat}
            onChange={(e) => handleInputChange('dateFormat', e.target.value)}
          >
            <option value="MM/DD/YYYY">MM/DD/YYYY (US)</option>
            <option value="DD/MM/YYYY">DD/MM/YYYY (EU)</option>
            <option value="YYYY-MM-DD">YYYY-MM-DD (ISO)</option>
          </select>
          <p className={styles.description}>Choose how dates are displayed</p>
        </div>

        {/* Default Date Range */}
        <div className={styles.formGroup}>
          <label className={styles.label} htmlFor="defaultDateRange">
            Default Date Range
          </label>
          <select
            id="defaultDateRange"
            className={styles.select}
            value={preferences.defaultDateRange}
            onChange={(e) => handleInputChange('defaultDateRange', e.target.value)}
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
            <option value="1y">Last year</option>
          </select>
          <p className={styles.description}>Default time range for charts and reports</p>
        </div>

        {/* Notifications */}
        <div className={styles.formGroup}>
          <label className={styles.label}>Notifications</label>
          <div className={styles.checkboxGroup}>
            <label className={styles.checkboxItem}>
              <input
                type="checkbox"
                className={styles.checkbox}
                checked={preferences.notifications.email}
                onChange={(e) => handleNotificationChange('email', e.target.checked)}
              />
              <div className={styles.checkboxLabel}>
                <span className={styles.checkboxTitle}>Email Notifications</span>
                <span className={styles.checkboxDescription}>
                  Receive updates and alerts via email
                </span>
              </div>
            </label>

            <label className={styles.checkboxItem}>
              <input
                type="checkbox"
                className={styles.checkbox}
                checked={preferences.notifications.push}
                onChange={(e) => handleNotificationChange('push', e.target.checked)}
              />
              <div className={styles.checkboxLabel}>
                <span className={styles.checkboxTitle}>Push Notifications</span>
                <span className={styles.checkboxDescription}>
                  Get real-time browser notifications
                </span>
              </div>
            </label>

            <label className={styles.checkboxItem}>
              <input
                type="checkbox"
                className={styles.checkbox}
                checked={preferences.notifications.alerts}
                onChange={(e) => handleNotificationChange('alerts', e.target.checked)}
              />
              <div className={styles.checkboxLabel}>
                <span className={styles.checkboxTitle}>Critical Alerts</span>
                <span className={styles.checkboxDescription}>
                  Notify me about critical inventory and pricing issues
                </span>
              </div>
            </label>

            <label className={styles.checkboxItem}>
              <input
                type="checkbox"
                className={styles.checkbox}
                checked={preferences.notifications.reports}
                onChange={(e) => handleNotificationChange('reports', e.target.checked)}
              />
              <div className={styles.checkboxLabel}>
                <span className={styles.checkboxTitle}>Weekly Reports</span>
                <span className={styles.checkboxDescription}>
                  Receive weekly performance summaries
                </span>
              </div>
            </label>
          </div>
        </div>

        {/* Success Message */}
        {showSuccess && (
          <div className={styles.successMessage}>
            <span>✓</span>
            <span>Preferences saved successfully!</span>
          </div>
        )}

        {/* Actions */}
        <div className={styles.actions}>
          <button
            type="button"
            className={styles.button}
            onClick={handleReset}
            disabled={!hasChanges || isSaving}
          >
            Reset
          </button>
          <button
            type="button"
            className={`${styles.button} ${styles.primary}`}
            onClick={handleSave}
            disabled={!hasChanges || isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </div>
  );
}
