'use client';

import { Card } from '@/components/ui/Card';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { Button } from '@/components/ui/Button';
import { formatRelativeTime } from '@/lib/utils';
import type { Workflow } from '@/lib/types';
import Link from 'next/link';

interface WorkflowCardProps {
  workflow: Workflow;
}

export function WorkflowCard({ workflow }: WorkflowCardProps) {
  return (
    <Card>
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {workflow.name || `Workflow ${workflow.workflow_id.slice(0, 8)}`}
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              {workflow.contract_type || 'Custom'} • {workflow.network}
            </p>
          </div>
          <StatusBadge status={workflow.status} />
        </div>

        <ProgressBar progress={workflow.progress_percentage} />

        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>Created {formatRelativeTime(workflow.created_at)}</span>
          {workflow.contracts && workflow.contracts.length > 0 && (
            <span>{workflow.contracts.length} contract(s)</span>
          )}
        </div>

        <div className="flex gap-2">
          <Link href={`/workflows/${workflow.workflow_id}`} className="flex-1">
            <Button variant="primary" className="w-full">
              View Details
            </Button>
          </Link>
        </div>
      </div>
    </Card>
  );
}

