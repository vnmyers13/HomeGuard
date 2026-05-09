/**
 * Scans page - view scan history and trigger new deletion requests.
 */

import { useState, useEffect } from 'react';
import { scansApi, profilesApi } from '../lib/api';

export default function Scans() {
  const [scans, setScans] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [selectedProfile, setSelectedProfile] = useState('');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [scansRes, profilesRes] = await Promise.all([
        scansApi.list({ limit: 50 }),
        profilesApi.list({ limit: 100 }),
      ]);

      setScans(scansRes.data?.items || []);
      const profileList = profilesRes.data?.items || [];
      setProfiles(profileList);

      if (profileList.length > 0 && !selectedProfile) {
        setSelectedProfile(profileList[0].id);
      }
    } catch (err) {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerScan = async () => {
    if (!selectedProfile) {
      setError('Select a profile to scan');
      return;
    }

    setScanning(true);
    setError(null);
    setSuccess(null);

    try {
      await scansApi.trigger({ profile_id: selectedProfile });
      setSuccess('Deletion scan triggered. Processing in background...');
      setTimeout(() => loadData(), 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to trigger scan');
    } finally {
      setScanning(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      case 'running':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
      default:
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
    }
  };

  const formatDateTime = (iso) => {
    if (!iso) return '—';
    const date = new Date(iso);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Deletion Scans
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Trigger and monitor data deletion requests across brokers.
        </p>
      </div>

      {/* Messages */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-800 dark:text-red-400">{error}</p>
        </div>
      )}

      {success && (
        <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <p className="text-sm text-green-800 dark:text-green-400">{success}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Scan History */}
        <div className="lg:col-span-2">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Scan History
              </h2>
            </div>

            {scans.length === 0 ? (
              <div className="p-12 text-center">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-12 h-12 mx-auto text-gray-400 mb-4">
                  <path d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.625c-.621 0-1.213.169-1.718.471l-.052.037a3.375 3.375 0 0 0-1.426 2.8v1.5c0 .621.169 1.213.471 1.718l.037.052a3.375 3.375 0 0 0 2.8 1.426h1.5c.621 0 1.213-.169 1.718-.471l.052-.037a3.375 3.375 0 0 0 1.426-2.8" />
                </svg>
                <h3 className="text-gray-900 dark:text-white font-medium mb-1">
                  No scans yet
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Trigger your first deletion scan to get started.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {scans.map((scan) => (
                  <div key={scan.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-750">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <span
                          className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
                            scan.status
                          )}`}
                        >
                          {scan.status?.toUpperCase()}
                        </span>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {scan.broker_count || 0} brokers
                        </span>
                      </div>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {formatDateTime(scan.created_at)}
                      </span>
                    </div>

                    <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                      <span>Requests: {scan.request_count || 0}</span>
                      <span>Success: {scan.success_count || 0}</span>
                      <span>Failed: {scan.failure_count || 0}</span>
                      {scan.error_message && (
                        <span className="text-red-500 dark:text-red-400 truncate">
                          {scan.error_message}
                        </span>
                      )}
                    </div>

                    {/* Progress bar for running scans */}
                    {scan.status === 'running' && (
                      <div className="mt-3 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                        <div
                          className="bg-blue-600 h-1.5 rounded-full animate-pulse"
                          style={{ width: `${Math.min(((scan.request_count || 0) / (scan.broker_count || 1)) * 100, 100)}%` }}
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Trigger Scan Panel */}
        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Trigger Scan
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Profile to Scan *
                </label>
                <select
                  value={selectedProfile}
                  onChange={(e) => setSelectedProfile(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                >
                  <option value="">Select a profile...</option>
                  {profiles.map((profile) => (
                    <option key={profile.id} value={profile.id}>
                      {profile.first_name} {profile.last_name}
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={handleTriggerScan}
                disabled={scanning || !selectedProfile}
                className="w-full px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {scanning ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                    Starting...
                  </>
                ) : (
                  'Start Deletion Scan'
                )}
              </button>

              <div className="p-4 bg-gray-50 dark:bg-gray-750 rounded-lg">
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  <strong>How it works:</strong> The scan will submit deletion requests to all active data brokers for the selected profile. Results are processed in the background and updated here.
                </p>
              </div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="mt-6 bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
              Quick Stats
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500 dark:text-gray-400">Total Scans</span>
                <span className="font-medium text-gray-900 dark:text-white">{scans.length}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500 dark:text-gray-400">Completed</span>
                <span className="font-medium text-green-600 dark:text-green-400">
                  {scans.filter((s) => s.status === 'completed').length}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500 dark:text-gray-400">Running</span>
                <span className="font-medium text-blue-600 dark:text-blue-400">
                  {scans.filter((s) => s.status === 'running').length}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500 dark:text-gray-400">Failed</span>
                <span className="font-medium text-red-600 dark:text-red-400">
                  {scans.filter((s) => s.status === 'failed').length}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}