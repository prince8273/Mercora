import { useState } from 'react';
import { PageHeader } from '../components/molecules/PageHeader/PageHeader';
import {
  PreferencesPanel,
  AmazonIntegration,
} from '../features/settings/components';
import styles from './SettingsPage.module.css';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('preferences');

  const tabs = [
    { id: 'preferences', label: 'Preferences', icon: '⚙️' },
    { id: 'integrations', label: 'Integrations', icon: '🔗' },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'preferences':
        return <PreferencesPanel />;
      case 'integrations':
        return <AmazonIntegration />;
      default:
        return <PreferencesPanel />;
    }
  };

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

