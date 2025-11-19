'use client';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useHealth } from '@/hooks/useHealth';
import { ExternalLink } from 'lucide-react';

const GRAFANA_URL = process.env.NEXT_PUBLIC_GRAFANA_URL || 'http://localhost:3001';

export default function MonitoringPage() {
  const { health, loading } = useHealth();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Monitoring</h1>
          <p className="mt-2 text-gray-600">System health and performance metrics</p>
        </div>
        <a href={GRAFANA_URL} target="_blank" rel="noopener noreferrer">
          <Button variant="primary">
            Open Grafana
            <ExternalLink className="w-4 h-4 ml-2" />
          </Button>
        </a>
      </div>

      <Card>
        <h2 className="text-xl font-semibold mb-4">System Health</h2>
        {loading ? (
          <p className="text-gray-600">Loading health status...</p>
        ) : (
          <div className="space-y-4">
            <div>
              <span className="text-sm text-gray-500">Status:</span>
              <span className={`ml-2 font-medium capitalize ${
                health?.status === 'healthy' ? 'text-green-600' :
                health?.status === 'degraded' ? 'text-yellow-600' :
                'text-red-600'
              }`}>
                {health?.status || 'Unknown'}
              </span>
            </div>
            {health?.services && (
              <div className="space-y-2">
                <h3 className="font-medium">Services</h3>
                {health.services.database && (
                  <div className="text-sm">
                    <span className="text-gray-500">Database:</span>
                    <span className={`ml-2 ${
                      health.services.database.status === 'healthy' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {health.services.database.status}
                    </span>
                  </div>
                )}
                {health.services.redis && (
                  <div className="text-sm">
                    <span className="text-gray-500">Redis:</span>
                    <span className={`ml-2 ${
                      health.services.redis.status === 'healthy' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {health.services.redis.status}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </Card>

      <Card>
        <h2 className="text-xl font-semibold mb-4">Grafana Dashboards</h2>
        <p className="text-gray-600 mb-4">
          Access detailed metrics and visualizations in Grafana:
        </p>
        <div className="space-y-2">
          <a
            href={`${GRAFANA_URL}/d/system-health`}
            target="_blank"
            rel="noopener noreferrer"
            className="block text-blue-600 hover:underline"
          >
            System Health Dashboard
          </a>
          <a
            href={`${GRAFANA_URL}/d/workflow-metrics`}
            target="_blank"
            rel="noopener noreferrer"
            className="block text-blue-600 hover:underline"
          >
            Workflow Metrics Dashboard
          </a>
          <a
            href={`${GRAFANA_URL}/d/agent-performance`}
            target="_blank"
            rel="noopener noreferrer"
            className="block text-blue-600 hover:underline"
          >
            Agent Performance Dashboard
          </a>
        </div>
      </Card>

      <Card>
        <h2 className="text-xl font-semibold mb-4">Embedded Grafana</h2>
        <div className="aspect-video border border-gray-200 rounded-lg overflow-hidden">
          <iframe
            src={`${GRAFANA_URL}/d/system-health?orgId=1&kiosk=tv`}
            className="w-full h-full"
            title="Grafana Dashboard"
          />
        </div>
      </Card>
    </div>
  );
}

