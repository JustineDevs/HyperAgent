'use client';

import { Card } from '@/components/ui/Card';

export default function DeploymentsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Deployments</h1>
        <p className="mt-2 text-gray-600">View all contract deployments</p>
      </div>

      <Card>
        <div className="text-center py-12">
          <p className="text-gray-600">Deployment listing coming soon</p>
          <p className="text-sm text-gray-500 mt-2">
            Deployments are available in workflow details
          </p>
        </div>
      </Card>
    </div>
  );
}

