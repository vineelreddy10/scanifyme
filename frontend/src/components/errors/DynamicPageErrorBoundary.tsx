/**
 * DynamicPageErrorBoundary
 * 
 * Error boundary for dynamic list and detail pages.
 * Prevents the entire app from crashing when a dynamic page fails.
 * Shows a clean error UI with navigation options.
 */

import { Component, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: string
}

interface ErrorBoundaryProps {
  children: ReactNode
  doctype?: string
  pageType?: 'list' | 'detail'
}

class DynamicErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: ''
    }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error
    }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Dynamic page error:', error, errorInfo)
    this.setState({
      errorInfo: errorInfo.componentStack || ''
    })
  }

  render() {
    if (this.state.hasError) {
      return (
        <DynamicPageErrorUI
          error={this.state.error}
          doctype={this.props.doctype}
          pageType={this.props.pageType}
        />
      )
    }

    return this.props.children
  }
}

// Error UI component (must be inside Router for useNavigate)
function DynamicPageErrorUI({
  error,
  doctype,
  pageType
}: {
  error: Error | null
  doctype?: string
  pageType?: 'list' | 'detail'
}) {
  const navigate = useNavigate()

  const handleGoBack = () => {
    navigate(-1)
  }

  const handleGoHome = () => {
    navigate('/')
  }

  return (
    <div className="min-h-[400px] flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg border border-gray-200 p-6">
        <div className="flex items-center justify-center w-12 h-12 mx-auto mb-4 rounded-full bg-red-100">
          <svg
            className="w-6 h-6 text-red-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>

        <h2 className="text-xl font-bold text-gray-900 text-center mb-2">
          This page could not be rendered
        </h2>

        <div className="text-sm text-gray-600 text-center mb-4">
          {doctype && (
            <p>
              <span className="font-medium">DocType:</span> {doctype}
            </p>
          )}
          {pageType && (
            <p>
              <span className="font-medium">Page Type:</span> {pageType}
            </p>
          )}
        </div>

        {error && (
          <div className="mb-4 p-3 bg-gray-50 rounded border border-gray-200">
            <p className="text-xs text-gray-600 font-mono truncate">
              {error.message}
            </p>
          </div>
        )}

        <div className="flex flex-col gap-2">
          <button
            onClick={handleGoHome}
            className="w-full px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700"
          >
            Go to Dashboard
          </button>
          <button
            onClick={handleGoBack}
            className="w-full px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200"
          >
            Go Back
          </button>
        </div>

        <p className="mt-4 text-xs text-gray-400 text-center">
          If this problem persists, please contact your administrator.
        </p>
      </div>
    </div>
  )
}

export { DynamicErrorBoundary }
export default DynamicErrorBoundary
