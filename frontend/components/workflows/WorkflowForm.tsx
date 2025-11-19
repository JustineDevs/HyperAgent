'use client';

import { useState, FormEvent } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Select } from '@/components/ui/Select';
import { Card } from '@/components/ui/Card';
import { getNetworks } from '@/lib/api';
import type { Network } from '@/lib/types';
import { useEffect } from 'react';

interface WorkflowFormProps {
  onSubmit: (data: {
    nlp_input: string;
    network: string;
    contract_type?: string;
    name?: string;
    skip_audit?: boolean;
    skip_deployment?: boolean;
    optimize_for_metisvm?: boolean;
    enable_floating_point?: boolean;
    enable_ai_inference?: boolean;
  }) => void;
  loading?: boolean;
}

export function WorkflowForm({ onSubmit, loading = false }: WorkflowFormProps) {
  const [nlpInput, setNlpInput] = useState('');
  const [network, setNetwork] = useState('');
  const [contractType, setContractType] = useState('Custom');
  const [name, setName] = useState('');
  const [skipAudit, setSkipAudit] = useState(false);
  const [skipDeployment, setSkipDeployment] = useState(false);
  const [optimizeForMetisVM, setOptimizeForMetisVM] = useState(false);
  const [enableFloatingPoint, setEnableFloatingPoint] = useState(false);
  const [enableAIInference, setEnableAIInference] = useState(false);
  const [networks, setNetworks] = useState<Network[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getNetworks()
      .then(setNetworks)
      .catch((err) => setError(err.message));
  }, []);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!nlpInput.trim() || !network) {
      setError('Please fill in all required fields');
      return;
    }

    onSubmit({
      nlp_input: nlpInput,
      network,
      contract_type: contractType,
      name: name || undefined,
      skip_audit: skipAudit,
      skip_deployment: skipDeployment,
      optimize_for_metisvm: optimizeForMetisVM,
      enable_floating_point: enableFloatingPoint,
      enable_ai_inference: enableAIInference,
    });
  };

  const networkOptions = networks.map((n) => ({
    value: n.network,
    label: `${n.network} (${n.chain_id || 'N/A'})`,
  }));

  return (
    <Card>
      <form onSubmit={handleSubmit} className="space-y-6">
        <Textarea
          label="Contract Description *"
          placeholder="Describe the smart contract you want to create (e.g., 'Create an ERC20 token named TestToken with symbol TST and initial supply 1000000')"
          value={nlpInput}
          onChange={(e) => setNlpInput(e.target.value)}
          rows={4}
          required
        />

        <Select
          label="Network *"
          options={[
            { value: '', label: 'Select a network...' },
            ...networkOptions,
          ]}
          value={network}
          onChange={(e) => setNetwork(e.target.value)}
          required
        />

        <Input
          label="Contract Type"
          value={contractType}
          onChange={(e) => setContractType(e.target.value)}
          placeholder="Custom"
        />

        <Input
          label="Workflow Name (Optional)"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="My Workflow"
        />

        <div className="space-y-3">
          <label className="text-sm font-medium text-gray-700">Advanced Options</label>
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={skipAudit}
                onChange={(e) => setSkipAudit(e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">Skip Security Audit</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={skipDeployment}
                onChange={(e) => setSkipDeployment(e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">Skip Deployment (Generate Only)</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={optimizeForMetisVM}
                onChange={(e) => setOptimizeForMetisVM(e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">Optimize for MetisVM</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={enableFloatingPoint}
                onChange={(e) => setEnableFloatingPoint(e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">Enable Floating Point Operations</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={enableAIInference}
                onChange={(e) => setEnableAIInference(e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm">Enable AI Inference</span>
            </label>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
            {error}
          </div>
        )}

        <Button type="submit" disabled={loading} className="w-full">
          {loading ? 'Creating Workflow...' : 'Create Workflow'}
        </Button>
      </form>
    </Card>
  );
}

