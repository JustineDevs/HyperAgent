'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { getTemplates, searchTemplates } from '@/lib/api';
import type { Template } from '@/lib/types';

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const data = await getTemplates();
        setTemplates(data);
      } catch (error) {
        console.error('Failed to fetch templates:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTemplates();
  }, []);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      const data = await getTemplates();
      setTemplates(data);
      return;
    }

    setLoading(true);
    try {
      const data = await searchTemplates({ query: searchQuery });
      setTemplates(data);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Templates</h1>
        <p className="mt-2 text-gray-600">Browse and search contract templates</p>
      </div>

      <Card>
        <div className="flex gap-2">
          <Input
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            className="flex-1"
          />
          <Button onClick={handleSearch}>Search</Button>
        </div>
      </Card>

      {loading ? (
        <div className="flex items-center justify-center min-h-[400px]">
          <LoadingSpinner size="lg" />
        </div>
      ) : templates.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <p className="text-gray-600">No templates found</p>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {templates.map((template) => (
            <Card key={template.id}>
              <div className="space-y-3">
                <h3 className="font-semibold text-lg">{template.name}</h3>
                {template.description && (
                  <p className="text-sm text-gray-600">{template.description}</p>
                )}
                <div className="flex items-center gap-2">
                  {template.contract_type && (
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                      {template.contract_type}
                    </span>
                  )}
                  {template.tags.map((tag) => (
                    <span key={tag} className="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

