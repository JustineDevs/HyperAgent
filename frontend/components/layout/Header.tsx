'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/Button';

export function Header() {
  return (
    <header className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="text-xl font-bold text-blue-600">
              HyperAgent
            </Link>
            <nav className="ml-8 space-x-4">
              <Link href="/workflows" className="text-gray-700 hover:text-blue-600">
                Workflows
              </Link>
              <Link href="/contracts" className="text-gray-700 hover:text-blue-600">
                Contracts
              </Link>
              <Link href="/deployments" className="text-gray-700 hover:text-blue-600">
                Deployments
              </Link>
              <Link href="/templates" className="text-gray-700 hover:text-blue-600">
                Templates
              </Link>
              <Link href="/monitoring" className="text-gray-700 hover:text-blue-600">
                Monitoring
              </Link>
            </nav>
          </div>
          <Link href="/workflows/create">
            <Button variant="primary">Create Workflow</Button>
          </Link>
        </div>
      </div>
    </header>
  );
}

