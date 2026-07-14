import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  handleReload = () => {
    window.location.reload();
  };

  handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-neutral-50 flex items-center justify-center px-4">
          <div className="max-w-md w-full bg-white rounded-xl shadow-soft border border-neutral-200 p-6 text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
              <ExclamationTriangleIcon className="h-6 w-6 text-red-600" aria-hidden="true" />
            </div>
            
            <h3 className="text-lg font-medium text-neutral-900 mb-2">
              Something went wrong
            </h3>
            
            <p className="text-sm text-neutral-600 mb-6">
              We're sorry, but something unexpected happened. Please try refreshing the page or contact support if the problem persists.
            </p>

            {import.meta.env.DEV && this.state.error && (
              <details className="mb-6 text-left">
                <summary className="text-sm font-medium text-neutral-700 cursor-pointer mb-2">
                  Error Details (Development)
                </summary>
                <div className="bg-neutral-100 rounded-lg p-3 text-xs font-mono text-neutral-800 overflow-auto max-h-32">
                  <div className="mb-2">
                    <strong>Error:</strong> {this.state.error.message}
                  </div>
                  <div className="mb-2">
                    <strong>Stack:</strong>
                    <pre className="whitespace-pre-wrap">{this.state.error.stack}</pre>
                  </div>
                  {this.state.errorInfo && (
                    <div>
                      <strong>Component Stack:</strong>
                      <pre className="whitespace-pre-wrap">{this.state.errorInfo.componentStack}</pre>
                    </div>
                  )}
                </div>
              </details>
            )}

            <div className="flex space-x-3">
              <button
                onClick={this.handleReset}
                className="flex-1 btn-secondary"
              >
                Try Again
              </button>
              <button
                onClick={this.handleReload}
                className="flex-1 btn-primary flex items-center justify-center space-x-2"
              >
                <ArrowPathIcon className="h-4 w-4" />
                <span>Reload Page</span>
              </button>
            </div>

            <div className="mt-4 text-xs text-neutral-500">
              If this problem continues, please contact{' '}
              <a href="mailto:support@sconia.gov.ng" className="text-primary-600 hover:text-primary-700">
                support@sconia.gov.ng
              </a>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
