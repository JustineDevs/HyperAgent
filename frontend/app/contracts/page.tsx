'use client';

import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export default function ContractsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Contracts</h1>
        <p className="mt-2 text-gray-600">View all generated smart contracts</p>
      </div>

      <Card>
        <div className="text-center py-12">
          <p className="text-gray-600">Contract listing coming soon</p>
          <p className="text-sm text-gray-500 mt-2">
            Contracts are available in workflow details
          </p>
        </div>
      </Card>
    </div>
  );
}

