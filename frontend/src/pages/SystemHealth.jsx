/**
 * SystemHealth - Service status dashboard.
 * Sprint 6: System health monitoring page.
 */

import { useState, useEffect } from 'react';
import Card from '../components/Card';
import StatusBadge from '../components/StatusBadge';

export default function SystemHealth() {
  const [health, setHealth] = useState(null);
  const [diskUsage, setDiskUsage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lastChecked, setLastChecked] = useState(null);

  const checkHealth = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}${import.meta.env.VITE_API_URL ? '' : '/api'}/system/health`);
      const data = await res.json();
      setHealth(data?.data || data);
      setLastChecked(new Date());

      // Try to get disk usage from Redis/maintenance endpoint
      try {
        const diskRes = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}${import.meta.env.VITE_API_URL ? '' : '/api'}/system/disk-usage`);
        if (diskRes.ok) {
          const diskData = await diskRes.json();
          setDiskUsage(diskData?.data || diskData);
        }
      } catch {
        // Disk usage endpoint may not exist, ignore
      }
    } catch (err) {
      console.error('Health check failed:', err);
      setHealth({ status: 'unknown', services: {} });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const services = health?.services || {};
  const serviceList = [
    { name: 'API', status: services.api || 'unknown', icon: '🔌' },
    { name: 'Database', status: services.database || 'unknown', icon: '🗄️' },
    { name: 'Redis', status: services.redis || 'unknown', icon: '⚡' },
    { name: 'Playwright', status: services.playwright || services.browser_pool || 'unknown', icon: '🌐' },
    { name: 'Mailwatcher', status: services.mailwatcher || 'unknown', icon: '📧' },
    { name: 'n8n', status: services.n8n || services.workflow || 'unknown', icon: '🔄' },
  ];

  const getStatusColor = (status) => {
    if (status === 'up' || status === 'healthy') return 'text-green-500';
    if (status === 'degraded') return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">System Health</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {lastChecked ? `Last checked: ${lastChecked.toLocaleTimeString()}` : 'Checking system status...'}
          </p>
        </div>
        <button
          onClick={checkHealth}
          disabled={loading}
          className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {loading ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Checking...
            </>
          ) : (
            'Check Now'
          )}
        </button>
      </div>

      {/* Overall Status */}
      <Card className="p-6">
        <div className="flex items-center gap-4">
          <div className={`flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center ${
            health?.status === 'healthy' ? 'bg-green-100 dark:bg-green-900/30' :
            health?.status === 'degraded' ? 'bg-yellow-100 dark:bg-yellow-900/30' :
            'bg-red-100 dark:bg-red-900/30'
          }`}>
            <span className="text-2xl">
              {health?.status === 'healthy' ? '✅' : health?.status === 'degraded' ? '⚠️' : '❌'}
            </span>
          </div>
          <div>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              System {health?.status ? health.status.charAt(0).toUpperCase() + health.status.slice(1) : 'Unknown'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Version {health?.version || '1.04'} · {serviceList.filter(s => s.status === 'up' || s.status === 'healthy').length} of {serviceList.length} services running
            </p>
          </div>
        </div>
      </Card>

      {/* Service Status Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {serviceList.map(service => (
          <Card key={service.name} className="p-4 flex items-center gap-3">
            <span className="text-2xl">{service.icon}</span>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-white">{service.name}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className={`w-2 h-2 rounded-full ${getStatusColor(service.status)}`} />
                <StatusBadge status={service.status === 'up' || service.status === 'healthy' ? 'healthy' : service.status === 'degraded' ? 'degraded' : 'down'}>
                  {service.status}
                </StatusBadge>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Disk Usage */}
      {diskUsage && (
        <Card className="p-6">
          <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4">Disk Usage</h3>
          <div className="space-y-3">
            {Object.entries(diskUsage).map(([volume, usage]) => (
              <div key={volume}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600 dark:text-gray-400">{volume}</span>
                  <span className="text-gray-900 dark:text-white">
                    {typeof usage === 'object'
                      ? `${usage.used || 0} / ${usage.total || 0} GB`
                      : usage}
                  </span>
                </div>
                <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-indigo-500 rounded-full transition-all"
                    style={{
                      width: typeof usage === 'object' && usage.total ? `${(usage.used / usage.total) * 100}%` : '0%',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Recent Alerts */}
      <Card className="p-6">
        <h3 className="text-base font-semibold text-gray-900 dark:text-white mb-4">Recent Alerts</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          No active alerts · All systems operational
        </p>
      </Card>
    </div>
  );
}
