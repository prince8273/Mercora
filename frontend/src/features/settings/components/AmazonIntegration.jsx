import { useState } from 'react';
import { StatusIndicator } from '../../../components/molecules/StatusIndicator/StatusIndicator';
import styles from './AmazonIntegration.module.css';

export default function AmazonIntegration({ initialConfig, onSave, onTest, onSync }) {
  const [config, setConfig] = useState({
    accessKeyId: '',
    secretAccessKey: '',
    marketplaceId: 'ATVPDKIKX0DER', // US marketplace
    sellerId: '',
    syncFrequency: 'hourly',
    autoSync: true,
    ...initialConfig,
  });

  const [connectionStatus, setConnectionStatus] = useState(
    initialConfig?.connected ? 'connected' : 'disconnected'
  );
  const [isTesting, setIsTesting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState(null);
  const [showSuccess, setShowSuccess] = useState(false);

  const handleInputChange = (field, value) => {
    setConfig({ ...config, [field]: value });
    setError(null);
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setError(null);
    setConnectionStatus('testing');

    try {
      const result = await onTest?.(config);
      if (result?.success) {
        setConnectionStatus('connected');
        setShowSuccess(true);
        setTimeout(() => setShowSuccess(false), 3000);
      } else {
        setConnectionStatus('disconnected');
        setError(result?.error || 'Connection test failed');
      }
    } catch (err) {
      setConnectionStatus('disconnected');
      setError(err.message || 'Connection test failed');
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);

    try {
      await onSave?.(config);
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    } catch (err) {
      setError(err.message || 'Failed to save configuration');
    } finally {
      setIsSaving(false);
    }
  };

  const handleManualSync = async () => {
    setIsSyncing(true);
    setError(null);

    try {
      await onSync?.();
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    } catch (err) {
      setError(err.message || 'Sync failed');
    } finally {
      setIsSyncing(false);
    }
  };

  const getStatusConfig = () => {
    switch (connectionStatus) {
      case 'connected':
        return {
          icon: '✓',
          title: 'Connected',
          subtitle: 'Amazon API is connected and working',
          class: 'connected',
        };
      case 'testing':
        return {
          icon: '⏳',
          title: 'Testing Connection',
          subtitle: 'Verifying API credentials...',
          class: 'testing',
        };
      default:
        return {
          icon: '✗',
          title: 'Disconnected',
          subtitle: 'Amazon API is not configured',
          class: 'disconnected',
        };
    }
  };

  const statusConfig = getStatusConfig();

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Amazon Integration</h2>
        <p className={styles.subtitle}>Configure Amazon Seller Central API connection</p>
      </div>

      {/* Connection Status */}
      <div className={`${styles.statusCard} ${styles[statusConfig.class]}`}>
        <div className={styles.statusHeader}>
          <div className={styles.statusIcon}>{statusConfig.icon}</div>
          <div className={styles.statusText}>
            <h3 className={styles.statusTitle}>{statusConfig.title}</h3>
            <p className={styles.statusSubtitle}>{statusConfig.subtitle}</p>
          </div>
          <div className={styles.statusActions}>
            {connectionStatus === 'connected' && (
              <button
                className={`${styles.statusButton} ${styles.primary}`}
                onClick={handleManualSync}
                disabled={isSyncing}
              >
                {isSyncing ? 'Syncing...' : 'Sync Now'}
              </button>
            )}
            <button
              className={styles.statusButton}
              onClick={handleTestConnection}
              disabled={isTesting || !config.accessKeyId || !config.secretAccessKey}
            >
              {isTesting ? 'Testing...' : 'Test Connection'}
            </button>
          </div>
        </div>
      </div>

      {/* Configuration Form */}
      <form className={styles.form} onSubmit={(e) => e.preventDefault()}>
        <div className={styles.formGroup}>
          <label className={styles.label} htmlFor="accessKeyId">
            Access Key ID <span className={styles.required}>*</span>
          </label>
          <input
            id="accessKeyId"
            type="text"
            className={styles.input}
            value={config.accessKeyId}
            onChange={(e) => handleInputChange('accessKeyId', e.target.value)}
            placeholder="AKIAIOSFODNN7EXAMPLE"
          />
          <p className={styles.description}>Your Amazon MWS Access Key ID</p>
        </div>

        <div className={styles.formGroup}>
          <label className={styles.label} htmlFor="secretAccessKey">
            Secret Access Key <span className={styles.required}>*</span>
          </label>
          <input
            id="secretAccessKey"
            type="password"
            className={`${styles.input} ${styles.password}`}
            value={config.secretAccessKey}
            onChange={(e) => handleInputChange('secretAccessKey', e.target.value)}
            placeholder="••••••••••••••••••••••••••••••••"
          />
          <p className={styles.description}>Your Amazon MWS Secret Access Key</p>
        </div>

        <div className={styles.formGroup}>
          <label className={styles.label} htmlFor="sellerId">
            Seller ID <span className={styles.required}>*</span>
          </label>
          <input
            id="sellerId"
            type="text"
            className={styles.input}
            value={config.sellerId}
            onChange={(e) => handleInputChange('sellerId', e.target.value)}
            placeholder="A1B2C3D4E5F6G7"
          />
          <p className={styles.description}>Your Amazon Seller ID</p>
        </div>

        <div className={styles.formGroup}>
          <label className={styles.label} htmlFor="marketplaceId">
            Marketplace
          </label>
          <select
            id="marketplaceId"
            className={styles.select}
            value={config.marketplaceId}
            onChange={(e) => handleInputChange('marketplaceId', e.target.value)}
          >
            <option value="ATVPDKIKX0DER">United States (amazon.com)</option>
            <option value="A2EUQ1WTGCTBG2">Canada (amazon.ca)</option>
            <option value="A1AM78C64UM0Y8">Mexico (amazon.com.mx)</option>
            <option value="A1PA6795UKMFR9">Germany (amazon.de)</option>
            <option value="A1RKKUPIHCS9HS">Spain (amazon.es)</option>
            <option value="A13V1IB3VIYZZH">France (amazon.fr)</option>
            <option value="A1F83G8C2ARO7P">United Kingdom (amazon.co.uk)</option>
            <option value="APJ6JRA9NG5V4">Italy (amazon.it)</option>
          </select>
          <p className={styles.description}>Select your primary marketplace</p>
        </div>

        {/* Sync Settings */}
        <div className={styles.syncSettings}>
          <h3 className={styles.syncTitle}>Sync Settings</h3>
          <div className={styles.syncOptions}>
            <div className={styles.syncOption}>
              <div className={styles.syncOptionLeft}>
                <span className={styles.syncOptionTitle}>Sync Frequency</span>
                <span className={styles.syncOptionDescription}>
                  How often to sync data from Amazon
                </span>
              </div>
              <select
                className={styles.select}
                value={config.syncFrequency}
                onChange={(e) => handleInputChange('syncFrequency', e.target.value)}
              >
                <option value="realtime">Real-time</option>
                <option value="hourly">Every hour</option>
                <option value="daily">Daily</option>
                <option value="manual">Manual only</option>
              </select>
            </div>

            <div className={styles.syncOption}>
              <div className={styles.syncOptionLeft}>
                <span className={styles.syncOptionTitle}>Auto Sync</span>
                <span className={styles.syncOptionDescription}>
                  Automatically sync data in the background
                </span>
              </div>
              <input
                type="checkbox"
                checked={config.autoSync}
                onChange={(e) => handleInputChange('autoSync', e.target.checked)}
              />
            </div>
          </div>

          {initialConfig?.lastSync && (
            <div className={styles.lastSync}>
              <span>🕐</span>
              <span>Last synced: {new Date(initialConfig.lastSync).toLocaleString()}</span>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && <div className={styles.errorMessage}>{error}</div>}

        {/* Success Message */}
        {showSuccess && (
          <div className={styles.successMessage}>
            <span>✓</span>
            <span>Configuration saved successfully!</span>
          </div>
        )}

        {/* Actions */}
        <div className={styles.actions}>
          <button
            type="button"
            className={`${styles.button} ${styles.primary}`}
            onClick={handleSave}
            disabled={isSaving || !config.accessKeyId || !config.secretAccessKey || !config.sellerId}
          >
            {isSaving ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      </form>
    </div>
  );
}
