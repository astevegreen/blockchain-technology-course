import { Component } from 'react';

/**
 * Error boundary to catch and display React render errors.
 * Use to wrap components that may throw so users see a helpful message instead of a blank screen.
 */
export class ErrorBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo);
  }

  render() {
    if (this.state.error) {
      const { error } = this.state;
      const message = error?.message || String(error);
      const stack = error?.stack;
      return (
        <div style={{
          padding: '1.5rem 2rem',
          margin: '1rem',
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: '8px',
          color: '#fca5a5',
          maxWidth: '800px',
        }}>
          <h3 style={{ margin: '0 0 0.75rem', color: '#f87171' }}>
            Something went wrong
          </h3>
          <pre style={{
            margin: 0,
            fontSize: '0.85rem',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            fontFamily: 'monospace',
          }}>
            {message}
          </pre>
          {stack && (
            <details style={{ marginTop: '1rem', fontSize: '0.75rem', opacity: 0.8 }}>
              <summary style={{ cursor: 'pointer' }}>Stack trace</summary>
              <pre style={{ marginTop: '0.5rem', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                {stack}
              </pre>
            </details>
          )}
        </div>
      );
    }
    return this.props.children;
  }
}
