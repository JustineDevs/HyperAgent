'use client';

export function Footer() {
  return (
    <footer className="bg-gray-50 border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center text-sm text-gray-600">
          <p>HyperAgent - AI Agent Platform for On-Chain Smart Contract Generation</p>
          <p className="mt-2">
            <a href="https://hyperionkit.xyz" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
              HyperionKit
            </a>
            {' • '}
            <a href="https://github.com/HyperionKit/HyperAgent" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
              GitHub
            </a>
          </p>
        </div>
      </div>
    </footer>
  );
}

