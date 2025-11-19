'use client';

import { useState, useEffect } from 'react';
import { WorkflowCard } from '@/components/workflows/WorkflowCard';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import Link from 'next/link';
import type { Workflow } from '@/lib/types';

// Note: This would typically fetch from an API endpoint that lists workflows
// For now, this is a placeholder that shows the structure
export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: Implement API call to fetch workflows list
    // const fetchWorkflows = async () => {
    //   const data = await getWorkflows();
    //   setWorkflows(data);
    //   setLoading(false);
    // };
    // fetchWorkflows();
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Workflows</h1>
          <p className="mt-2 text-gray-600">View and manage your smart contract workflows</p>
        </div>
        <Link href="/workflows/create">
          <Button variant="primary">Create Workflow</Button>
        </Link>
      </div>

      {workflows.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <p className="text-gray-600 mb-4">No workflows found</p>
            <Link href="/workflows/create">
              <Button variant="primary">Create Your First Workflow</Button>
            </Link>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workflows.map((workflow) => (
            <WorkflowCard key={workflow.workflow_id} workflow={workflow} />
          ))}
        </div>
      )}
    </div>
  );
}

