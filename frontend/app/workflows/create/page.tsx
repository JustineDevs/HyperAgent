'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { WorkflowForm } from '@/components/workflows/WorkflowForm';
import { createWorkflow, handleApiError } from '@/lib/api';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export default function CreateWorkflowPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: any) => {
    setLoading(true);
    setError(null);

    try {
      const response = await createWorkflow(data);
      router.push(`/workflows/${response.workflow_id}`);
    } catch (err: any) {
      setError(handleApiError(err));
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Create New Workflow</h1>
        <p className="mt-2 text-gray-600">
          Describe the smart contract you want to create and we'll generate it for you
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
          {error}
        </div>
      )}

      <WorkflowForm onSubmit={handleSubmit} loading={loading} />
    </div>
  );
}

