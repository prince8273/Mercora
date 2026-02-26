import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { PageHeader } from '../components/molecules/PageHeader/PageHeader';
import {
  PreferencesPanel,
  AmazonIntegration,
} from '../features/settings/components';
import styles from './SettingsPage.module.css';

export default function SettingsPage() {
  const { t, i18n } = useTranslation();
  const [activeTab, setActiveTab] = useState('preferences');
  const [initialPreferences, setInitialPreferences] = useState(null);

  // Load preferences from localStorage on mount
  useEffect(() => {
    const loadPreferences = () => {
      try {
        const saved = localStorage.getItem('userPreferences');
        if (saved) {
          setInitialPreferences(JSON.parse(saved));
        } else {
          // Set default preferences
          const defaults = {
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
          };
          setInitialPreferences(defaults);
        }
      } catch (error) {
        console.error('Failed to load preferences:', error);
        setInitialPreferences({});
      }
    };

    loadPreferences();

    // Listen for storage changes from other tabs
    const handleStorageChange = (e) => {
      if (e.key === 'userPreferences') {
        loadPreferences();
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  // Save preferences to localStorage
  const handleSavePreferences = async (preferences) => {
    try {
      localStorage.setItem('userPreferences', JSON.stringify(preferences));
      console.log('Preferences saved:', preferences);
      // Update initialPreferences to reflect the saved state
      setInitialPreferences(preferences);
      // Change language if it was updated
      if (preferences.language !== i18n.language) {
        i18n.changeLanguage(preferences.language);
      }
      return Promise.resolve();
    } catch (error) {
      console.error('Failed to save preferences:', error);
      return Promise.reject(error);
    }
  };

  const tabs = [
    { id: 'preferences', label: 'Preferences', icon: '⚙️' },
    { id: 'integrations', label: 'Integrations', icon: '🔗' },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'preferences':
        return (
          <PreferencesPanel
            initialPreferences={initialPreferences}
            onSave={handleSavePreferences}
          />
        );
      case 'integrations':
        return <AmazonIntegration />;
      default:
        return (
          <PreferencesPanel
            initialPreferences={initialPreferences}
            onSave={handleSavePreferences}
          />
        );
    }
  };

  // Don't render until preferences are loaded
  if (initialPreferences === null) {
    return <div>Loading...</div>;
  }

  return (
    <div className={styles.page}>
      <PageHeader
        title="Settings"
        breadcrumbs={[
          { label: 'Home', path: '/' },
          { label: 'Settings', path: '/settings' },
        ]}
      />

      <div className={styles.container}>
        <div className={styles.tabs}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`${styles.tab} ${
                activeTab === tab.id ? styles.tabActive : ''
              }`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className={styles.tabIcon}>{tab.icon}</span>
              <span className={styles.tabLabel}>{tab.label}</span>
            </button>
          ))}
        </div>

        <div className={styles.content}>
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
}

