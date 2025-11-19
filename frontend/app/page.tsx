'use client';

import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { getHealth, getNetworks } from '@/lib/api';
import { useHealth } from '@/hooks/useHealth';
import Link from 'next/link';
import type { HealthStatus, Network } from '@/lib/types';

export default function Home() {
  const { health, loading: healthLoading } = useHealth();
  const [networks, setNetworks] = useState<Network[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getNetworks()
      .then(setNetworks)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">HyperAgent Dashboard</h1>
        <p className="mt-2 text-gray-600">
          AI Agent Platform for On-Chain Smart Contract Generation
        </p>
      </div>

      {/* System Health */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-gray-500">System Status</h3>
            {healthLoading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <div className="flex items-center gap-2">
                <div
                  className={`w-3 h-3 rounded-full ${
                    health?.status === 'healthy'
                      ? 'bg-green-500'
                      : health?.status === 'degraded'
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  }`}
                />
                <span className="text-lg font-semibold capitalize">
                  {health?.status || 'Unknown'}
                </span>
              </div>
            )}
          </div>
        </Card>

        <Card>
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-gray-500">Supported Networks</h3>
            {loading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <span className="text-lg font-semibold">{networks.length}</span>
            )}
          </div>
        </Card>

        <Card>
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-gray-500">Version</h3>
            <span className="text-lg font-semibold">{health?.version || 'N/A'}</span>
          </div>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link href="/workflows/create">
            <Button variant="primary" className="w-full">
              Create New Workflow
            </Button>
          </Link>
          <Link href="/templates">
            <Button variant="secondary" className="w-full">
              Browse Templates
            </Button>
          </Link>
          <Link href="/workflows">
            <Button variant="outline" className="w-full">
              View All Workflows
            </Button>
          </Link>
          <Link href="/monitoring">
            <Button variant="outline" className="w-full">
              View Monitoring
            </Button>
          </Link>
        </div>
      </Card>

      {/* Network Info */}
      {networks.length > 0 && (
        <Card>
          <h2 className="text-xl font-semibold mb-4">Supported Networks</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {networks.map((network) => (
              <div
                key={network.network}
                className="p-4 border border-gray-200 rounded-lg"
              >
                <h3 className="font-medium">{network.network}</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Chain ID: {network.chain_id || 'N/A'}
                </p>
                <p className="text-sm text-gray-600">
                  Currency: {network.currency || 'N/A'}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
