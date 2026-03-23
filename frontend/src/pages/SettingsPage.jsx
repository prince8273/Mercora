import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { PageHeader } from '../components/molecules/PageHeader/PageHeader';
import {
  PreferencesPanel,
  AmazonIntegration,
} from '../features/settings/components';
import ContactSupportModal from '../components/modals/ContactSupportModal';
import styles from './SettingsPage.module.css';

export default function SettingsPage() {
  const { t, i18n } = useTranslation();
  const [activeTab, setActiveTab] = useState('preferences');
  const [initialPreferences, setInitialPreferences] = useState(null);
  const [isContactModalOpen, setIsContactModalOpen] = useState(false);

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
      const oldPreferences = initialPreferences;
      localStorage.setItem('userPreferences', JSON.stringify(preferences));
      console.log('Preferences saved:', preferences);
      
      // Update initialPreferences to reflect the saved state
      setInitialPreferences(preferences);
      
      // Dispatch custom event for same-tab notification AFTER updating state
      // Check if defaultDateRange or theme changed
      if (oldPreferences?.defaultDateRange !== preferences.defaultDateRange || 
          oldPreferences?.theme !== preferences.theme) {
        // Small delay to ensure state is updated
        setTimeout(() => {
          window.dispatchEvent(new CustomEvent('preferencesChanged', {
            detail: { preferences, oldPreferences }
          }));
        }, 100);
      }
      
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

  const handleContactSupport = () => {
    setIsContactModalOpen(true);
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

      {/* Contact Support Button */}
      <button
        onClick={handleContactSupport}
        className="fixed bottom-6 right-6 bg-stone-900 text-white px-6 py-3 rounded-full shadow-lg hover:bg-stone-800 transition-all duration-300 flex items-center gap-2 z-40"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        Contact Support
      </button>

      {/* Contact Support Modal */}
      <ContactSupportModal
        isOpen={isContactModalOpen}
        onClose={() => setIsContactModalOpen(false)}
      />
    </div>
  );
}

