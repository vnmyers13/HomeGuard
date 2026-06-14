import React from 'react'
/**
 * Reports - Exposure analytics and removal statistics.
 * Sprint 6: Reports page with charts and data exports.
 */

import { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import Card from '../components/Card';
import StatusBadge from '../components/StatusBadge';

const CHART_COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export default function Reports() {
  const [dateRange, setDateRange] = useState('30d');
  const [exposureTrends, setExposureTrends] = useState([]);
  const [brokerSummary, setBrokerSummary] = useState([]);
  const [removalStats, setRemovalStats] = useState([]);
  const [overallScore, setOverallScore] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadReportData();
  }, [dateRange]);

  const loadReportData = async () => {
    setLoading(true);
    try {
      const [trendsRes, brokersRes, statsRes] = await Promise.all([
        fetchReport('/api/reports/exposure-trends', { range: dateRange }).catch(() => ({ data: [] })),
        fetchReport('/api/reports/broker-summary').catch(() => ({ data: [] })),
        fetchReport('/api/reports/removal-stats').catch(() => ({ data: [] })),
      ]);

      setExposureTrends(Array.isArray(trendsRes) ? trendsRes : (trendsRes.data?.data || trendsRes.data || []));
      setBrokerSummary(Array.isArray(brokersRes) ? brokersRes : (brokersRes.data?.data || brokersRes.data || []));
      setRemovalStats(Array.isArray(statsRes) ? statsRes : (statsRes.data?.data || statsRes.data || []));

      // Calculate overall score from exposure trends (latest value)
      const latest = Array.isArray(trendsRes) ? trendsRes[trendsRes.length - 1] : (trendsRes.data?.data?.[trendsRes.data.data.length - 1] || {});
      setOverallScore(latest?.score || 0);
    } catch (err) {
      console.error('Failed to load report data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchReport = async (url, params = {}) => {
    const qs = new URLSearchParams(params).toString();
    const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}${url}${qs ? '?' + qs : ''}`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('accessToken') || ''}` },
    });
    return res.json();
  };

  const exportCSV = () => {
    const headers = ['Date', 'Exposure Score', 'New Exposures', 'Removals Completed'];
    const rows = exposureTrends.map(d => [d.date, d.score, d.new_exposures || 0, d.removals || 0]);
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `homeguard_report_${dateRange}.csv`;
    a.click();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Reports</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Analytics and exposure trends for your household</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
          >
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </select>
          <button
            onClick={exportCSV}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            Export CSV
          </button>
        </div>
      </div>

      {/* Score Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6 flex items-center gap-4">
          <div className={`flex-shrink-0 w-16 h-16 rounded-full flex items-center justify-center ${
            overallScore >= 80 ? 'bg-green-100 dark:bg-green-900/30 text-green-600' :
            overallScore >= 60 ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-600' :
            'bg-red-100 dark:bg-red-900/30 text-red-600'
          }`}>
            <span className="text-2xl font-bold">{overallScore}</span>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Privacy Score</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {overallScore >= 80 ? 'Good' : overallScore >= 60 ? 'Fair' : 'Needs Attention'}
            </p>
          </div>
        </Card>
        <Card className="p-6">
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Exposures</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
            {exposureTrends.reduce((sum, d) => sum + (d.new_exposures || 0), 0)}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Discovered brokers with PII</p>
        </Card>
        <Card className="p-6">
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Removal Success Rate</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
            {removalStats.length > 0 ? `${Math.round((removalStats.filter(s => s.status === 'confirmed_removed').length / removalStats.length) * 100)}%` : 'N/A'}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Of all removal requests</p>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Exposure Trends */}
        <Card className="p-6">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4">Exposure Trends</h3>
          {loading ? (
            <div className="flex items-center justify-center h-48">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
            </div>
          ) : exposureTrends.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">No exposure data available</p>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={exposureTrends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#9ca3af' }} />
                <YAxis tick={{ fontSize: 12, fill: '#9ca3af' }} />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', color: '#fff' }} />
                <Legend />
                <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2} name="Privacy Score" />
                <Line type="monotone" dataKey="new_exposures" stroke="#ef4444" strokeWidth={2} name="New Exposures" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </Card>

        {/* Broker Exposure Breakdown */}
        <Card className="p-6">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4">Broker Exposure</h3>
          {loading ? (
            <div className="flex items-center justify-center h-48">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
            </div>
          ) : brokerSummary.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">No broker data available</p>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={brokerSummary.slice(0, 10)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#9ca3af' }} />
                <YAxis tick={{ fontSize: 12, fill: '#9ca3af' }} />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', color: '#fff' }} />
                <Bar dataKey="exposed" fill="#6366f1" radius={[4, 4, 0, 0]} name="Exposed Profiles" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      {/* Removal Stats */}
      <Card className="p-6">
        <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4">Removal Statistics</h3>
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
          </div>
        ) : removalStats.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">No removal data available</p>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={removalStats}
                dataKey="count"
                nameKey="method"
                cx="50%"
                cy="50%"
                outerRadius={70}
                label={({ method, percent }) => `${method}: ${(percent * 100).toFixed(0)}%`}
              >
                {removalStats.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px', color: '#fff' }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )}
      </Card>
    </div>
  );
}
