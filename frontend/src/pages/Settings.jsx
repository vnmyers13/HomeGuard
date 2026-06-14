/**
 * Settings - User preferences and account settings.
 * Sprint 6: Account, notification, and data retention settings.
 */

import { useState } from 'react';
import { useAuthStore } from '../stores/authStore';
import Card from '../components/Card';
import { getPreferences, savePreferences } from '../lib/api';

export default function Settings() {
  const { user, logout } = useAuthStore();
  const [activeTab, setActiveTab] = useState('notifications');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [prefs, setPrefs] = useState({
    email_alerts: true,
    scan_notifications: true,
    removal_updates: true,
    screenshot_retention_days: 30,
    scan_data_retention_days: 90,
    display_name: user?.display_name || user?.full_name || '',
    change_password: { current: '', new: '', confirm: '' },
  });

  useState(() => {
    const stored = getPreferences();
    if (stored) setPrefs(p => ({ ...p, ...stored }));
  });

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      savePreferences(prefs);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error('Failed to save settings:', err);
    } finally {
      setSaving(false);
    }
  };

  const handlePasswordChange = async () => {
    const { current, new: newPassword, confirm } = prefs.change_password;
    if (!current || !newPassword || !confirm) {
      alert('Please fill in all password fields');
      return;
    }
    if (newPassword !== confirm) {
      alert('New passwords do not match');
      return;
    }
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}${import.meta.env.VITE_API_URL ? '' : '/api'}/auth/change-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_password: current, new_password: newPassword }),
      });
      if (!res.ok) throw new Error('Password change failed');
      alert('Password updated successfully');
      setPrefs(p => ({ ...p, change_password: { current: '', new: '', confirm: '' } }));
    } catch (err) {
      alert('Failed to change password');
    }
  };

  const tabs = [
    { id: 'notifications', label: 'Notifications' },
    { id: 'account', label: 'Account' },
    { id: 'privacy', label: 'Data Retention' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Manage your preferences and account settings</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200 dark:border-gray-700">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Saved indicator */}
      {saved && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg px-4 py-2 text-sm text-green-700 dark:text-green-400">
          Settings saved successfully
        </div>
      )}

      {/* Notifications Tab */}
      {activeTab === 'notifications' && (
        <Card className="p-6 space-y-6">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white">Notification Preferences</h3>
          <div className="space-y-4">
            <label className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">Email Alerts</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Receive email notifications for new exposures</p>
              </div>
              <input
                type="checkbox"
                checked={prefs.email_alerts}
                onChange={(e) => setPrefs(p => ({ ...p, email_alerts: e.target.checked }))}
                className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
              />
            </label>
            <label className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">Scan Notifications</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Get notified when scans complete</p>
              </div>
              <input
                type="checkbox"
                checked={prefs.scan_notifications}
                onChange={(e) => setPrefs(p => ({ ...p, scan_notifications: e.target.checked }))}
                className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
              />
            </label>
            <label className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">Removal Updates</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Updates on removal request status changes</p>
              </div>
              <input
                type="checkbox"
                checked={prefs.removal_updates}
                onChange={(e) => setPrefs(p => ({ ...p, removal_updates: e.target.checked }))}
                className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
              />
            </label>
          </div>
        </Card>
      )}

      {/* Account Tab */}
      {activeTab === 'account' && (
        <Card className="p-6 space-y-6">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white">Account Settings</h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Display Name</label>
            <input
              type="text"
              value={prefs.display_name}
              onChange={(e) => setPrefs(p => ({ ...p, display_name: e.target.value }))}
              className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>

          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-4">Change Password</h4>
            <div className="space-y-3">
              <input
                type="password"
                placeholder="Current password"
                value={prefs.change_password.current}
                onChange={(e) => setPrefs(p => ({ ...p, change_password: { ...p.change_password, current: e.target.value } }))}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
              <input
                type="password"
                placeholder="New password"
                value={prefs.change_password.new}
                onChange={(e) => setPrefs(p => ({ ...p, change_password: { ...p.change_password, new: e.target.value } }))}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
              <input
                type="password"
                placeholder="Confirm new password"
                value={prefs.change_password.confirm}
                onChange={(e) => setPrefs(p => ({ ...p, change_password: { ...p.change_password, confirm: e.target.value } }))}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
              <button
                onClick={handlePasswordChange}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Update Password
              </button>
            </div>
          </div>

          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={logout}
              className="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 dark:bg-red-900/20 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors"
            >
              Sign Out
            </button>
          </div>
        </Card>
      )}

      {/* Data Retention Tab */}
      {activeTab === 'privacy' && (
        <Card className="p-6 space-y-6">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white">Data Retention</h3>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Screenshot Retention (days)</label>
            <input
              type="number"
              value={prefs.screenshot_retention_days}
              onChange={(e) => setPrefs(p => ({ ...p, screenshot_retention_days: Number(e.target.value) }))}
              className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Screenshots older than this will be automatically purged</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Scan Data Retention (days)</label>
            <input
              type="number"
              value={prefs.scan_data_retention_days}
              onChange={(e) => setPrefs(p => ({ ...p, scan_data_retention_days: Number(e.target.value) }))}
              className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Scan results and exposure data older than this will be archived</p>
          </div>
        </Card>
      )}

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  );
}
