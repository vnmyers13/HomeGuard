import React from 'react'
/**
 * Notifications - Alert history and notification preferences
 * Sprint 4: Notification system UI
 */

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAlerts, updatePreferences, getPreferences } from '../lib/api';

export default function Notifications() {
    const queryClient = useQueryClient();
    const [preferences, setPreferences] = useState({
        email_enabled: true,
        in_app_enabled: true,
        digest_frequency: 'realtime',
        alert_types: { new_listing: true, removal: true, scan_complete: true, opt_out: true }
    });

    // Fetch alerts
    const { data: alertsData, isLoading: alertsLoading } = useQuery({
        queryKey: ['alerts'],
        queryFn: () => getAlerts(),
    });

    // Fetch preferences
    useEffect(() => {
        getPreferences().then(res => {
            if (res.data) setPreferences(res.data);
        }).catch(() => {});
    }, []);

    // Update preferences mutation
    const updateMutation = useMutation({
        mutationFn: (prefs) => updatePreferences(prefs),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['preferences'] });
        },
    });

    const handlePreferenceChange = (key, value) => {
        const updated = { ...preferences, [key]: value };
        setPreferences(updated);
        updateMutation.mutate(updated);
    };

    const handleAlertTypeChange = (type, value) => {
        const updated = { ...preferences, alert_types: { ...preferences.alert_types, [type]: value } };
        setPreferences(updated);
        updateMutation.mutate(updated);
    };

    const markAsRead = (alertId) => {
        // Would call API to mark as read
        queryClient.invalidateQueries({ queryKey: ['alerts'] });
    };

    const markAllAsRead = () => {
        queryClient.invalidateQueries({ queryKey: ['alerts'] });
    };

    const getAlertIcon = (type) => {
        switch (type) {
            case 'new_listing': return '🔍';
            case 'removal': return '✅';
            case 'scan_complete': return '📊';
            case 'opt_out': return '🛡️';
            default: return 'ℹ️';
        }
    };

    const getAlertColor = (type) => {
        switch (type) {
            case 'new_listing': return 'bg-red-50 border-red-200';
            case 'removal': return 'bg-green-50 border-green-200';
            case 'scan_complete': return 'bg-blue-50 border-blue-200';
            case 'opt_out': return 'bg-purple-50 border-purple-200';
            default: return 'bg-gray-50 border-gray-200';
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
                <p className="text-gray-600 mt-1">Manage your alert preferences and view notification history</p>
            </div>

            {/* Preferences Section */}
            <div className="card">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Notification Preferences</h2>

                <div className="space-y-4">
                    {/* Channels */}
                    <div className="flex gap-6">
                        <label className="flex items-center gap-2">
                            <input
                                type="checkbox"
                                checked={preferences.email_enabled}
                                onChange={(e) => handlePreferenceChange('email_enabled', e.target.checked)}
                                className="rounded border-gray-300"
                            />
                            <span className="text-sm text-gray-700">Email notifications</span>
                        </label>

                        <label className="flex items-center gap-2">
                            <input
                                type="checkbox"
                                checked={preferences.in_app_enabled}
                                onChange={(e) => handlePreferenceChange('in_app_enabled', e.target.checked)}
                                className="rounded border-gray-300"
                            />
                            <span className="text-sm text-gray-700">In-app notifications</span>
                        </label>
                    </div>

                    {/* Digest Frequency */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Digest Frequency
                        </label>
                        <select
                            value={preferences.digest_frequency}
                            onChange={(e) => handlePreferenceChange('digest_frequency', e.target.value)}
                            className="input"
                        >
                            <option value="realtime">Real-time</option>
                            <option value="daily">Daily digest</option>
                            <option value="weekly">Weekly digest</option>
                        </select>
                    </div>

                    {/* Alert Types */}
                    <div className="border-t pt-4">
                        <h3 className="text-sm font-medium text-gray-700 mb-3">Alert Types</h3>
                        <div className="space-y-2">
                            {[
                                { key: 'new_listing', label: 'New Listings Found' },
                                { key: 'removal', label: 'Successful Removals' },
                                { key: 'scan_complete', label: 'Scan Complete' },
                                { key: 'opt_out', label: 'Opt-out Results' }
                            ].map(({ key, label }) => (
                                <label key={key} className="flex items-center gap-2">
                                    <input
                                        type="checkbox"
                                        checked={preferences.alert_types[key] || false}
                                        onChange={(e) => handleAlertTypeChange(key, e.target.checked)}
                                        className="rounded border-gray-300"
                                    />
                                    <span className="text-sm text-gray-700">{label}</span>
                                </label>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Alert History */}
            <div className="card">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-gray-900">Recent Notifications</h2>
                    <button
                        onClick={markAllAsRead}
                        className="text-sm text-blue-600 hover:text-blue-700"
                    >
                        Mark all as read
                    </button>
                </div>

                {alertsLoading ? (
                    <div className="flex justify-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    </div>
                ) : (alertsData?.data?.alerts || []).length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                        No notifications yet
                    </div>
                ) : (
                    <div className="space-y-2">
                        {(alertsData?.data?.alerts || []).map((alert) => (
                            <div
                                key={alert.id}
                                className={`flex items-start gap-3 p-3 rounded-lg border ${getAlertColor(alert.type)} ${!alert.read ? 'font-medium' : 'opacity-60'}`}
                                onClick={() => !alert.read && markAsRead(alert.id)}
                            >
                                <span className="text-xl">{getAlertIcon(alert.type)}</span>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm text-gray-900">{alert.title}</p>
                                    <p className="text-xs text-gray-600 mt-1">{alert.message}</p>
                                    <p className="text-xs text-gray-500 mt-1">
                                        {new Date(alert.created_at).toLocaleString()}
                                    </p>
                                </div>
                                {!alert.read && (
                                    <div className="w-2 h-2 rounded-full bg-blue-600 mt-1"></div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}