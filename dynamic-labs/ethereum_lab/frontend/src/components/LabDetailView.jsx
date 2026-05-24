import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/**
 * Renders the full lab instructions from the markdown file.
 * Content matches the lab markdown under docs/ (same files as in the repo). GUI or open the .md directly.
 */
const INSTRUCTOR_ONLY_REGEX = /<!--\s*INSTRUCTOR_ONLY\s*-->[\s\S]*?<!--\s*\/INSTRUCTOR_ONLY\s*-->/gi;

export default function LabDetailView({ lab, onBack, basePath = '', studentOnly = false }) {
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const docUrl = `${basePath}/docs/${lab.doc}.md`;

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(docUrl)
      .then((r) => {
        if (!r.ok) throw new Error(`Failed to load ${lab.doc}.md`);
        return r.text();
      })
      .then(setContent)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [lab.doc, docUrl]);

  const displayContent = content && studentOnly
    ? content.replace(INSTRUCTOR_ONLY_REGEX, '').trim()
    : content;

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', padding: '2rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
        <button
          onClick={onBack}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.5rem 1rem',
            background: 'transparent',
            border: '1px solid #475569',
            borderRadius: '0.5rem',
            color: '#94a3b8',
            cursor: 'pointer',
            fontSize: '0.9rem',
          }}
        >
          ← Back to Lab List
        </button>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
          {studentOnly && (
            <span
              style={{
                background: 'rgba(34, 197, 94, 0.2)',
                border: '1px solid rgba(34, 197, 94, 0.5)',
                borderRadius: '0.35rem',
                padding: '0.25rem 0.5rem',
                fontSize: '0.8rem',
                color: '#86efac',
                fontWeight: 600,
              }}
            >
              Student view
            </span>
          )}
          <span style={{ color: '#64748b', fontSize: '0.85rem' }}>Same content as</span>
          <a
            href={docUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: '#93c5fd',
              fontSize: '0.85rem',
              textDecoration: 'underline',
            }}
          >
            docs/{lab.doc}.md
          </a>
          <span style={{ color: '#64748b', fontSize: '0.8rem' }}>— use either</span>
        </div>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
          Loading lab instructions…
        </div>
      )}

      {error && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            borderRadius: '0.5rem',
            padding: '1rem',
            color: '#fca5a5',
          }}
        >
          <strong>Could not load lab:</strong> {error}
          <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.9rem' }}>
            Open <a href={docUrl} target="_blank" rel="noopener noreferrer" style={{ color: '#93c5fd' }}>docs/{lab.doc}.md</a> directly.
          </p>
        </div>
      )}

      {displayContent && !error && (
        <article
          className="lab-markdown"
          style={{
            background: '#1e293b',
            borderRadius: '1rem',
            padding: '1.5rem 2rem',
            border: '1px solid #334155',
          }}
        >
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({ children }) => (
                <h1 style={{ color: '#f8fafc', fontSize: '1.75rem', margin: '0 0 1rem 0', borderBottom: '1px solid #334155', paddingBottom: '0.5rem' }}>
                  {children}
                </h1>
              ),
              h2: ({ children }) => (
                <h2 style={{ color: '#93c5fd', fontSize: '1.25rem', margin: '1.5rem 0 0.75rem 0' }}>
                  {children}
                </h2>
              ),
              h3: ({ children }) => (
                <h3 style={{ color: '#c4b5fd', fontSize: '1.1rem', margin: '1.25rem 0 0.5rem 0' }}>
                  {children}
                </h3>
              ),
              h4: ({ children }) => (
                <h4 style={{ color: '#e2e8f0', fontSize: '1rem', margin: '1rem 0 0.5rem 0' }}>
                  {children}
                </h4>
              ),
              p: ({ children }) => (
                <p style={{ color: '#cbd5e1', margin: '0 0 0.75rem 0', lineHeight: 1.6 }}>
                  {children}
                </p>
              ),
              ul: ({ children }) => (
                <ul style={{ color: '#cbd5e1', margin: '0 0 0.75rem 0', paddingLeft: '1.5rem', lineHeight: 1.6 }}>
                  {children}
                </ul>
              ),
              ol: ({ children }) => (
                <ol style={{ color: '#cbd5e1', margin: '0 0 0.75rem 0', paddingLeft: '1.5rem', lineHeight: 1.6 }}>
                  {children}
                </ol>
              ),
              li: ({ children }) => (
                <li style={{ marginBottom: '0.25rem' }}>{children}</li>
              ),
              code: ({ children, className }) => {
                const isBlock = className?.includes('language-');
                if (isBlock) {
                  return (
                    <pre
                      style={{
                        background: '#0f172a',
                        border: '1px solid #334155',
                        borderRadius: '0.5rem',
                        padding: '1rem',
                        overflow: 'auto',
                        margin: '0.75rem 0',
                        fontSize: '0.9rem',
                        color: '#fbbf24',
                        fontFamily: "'Fira Code', 'Monaco', 'Consolas', monospace",
                      }}
                    >
                      <code>{children}</code>
                    </pre>
                  );
                }
                return (
                  <code
                    style={{
                      background: '#0f172a',
                      padding: '0.15rem 0.4rem',
                      borderRadius: '0.25rem',
                      fontSize: '0.9em',
                      color: '#fbbf24',
                      fontFamily: "'Fira Code', monospace",
                    }}
                  >
                    {children}
                  </code>
                );
              },
              blockquote: ({ children }) => (
                <blockquote
                  style={{
                    borderLeft: '4px solid #3b82f6',
                    margin: '0.75rem 0',
                    padding: '0.5rem 1rem',
                    background: 'rgba(59, 130, 246, 0.1)',
                    borderRadius: '0 0.5rem 0.5rem 0',
                    color: '#93c5fd',
                  }}
                >
                  {children}
                </blockquote>
              ),
              table: ({ children }) => (
                <div style={{ overflowX: 'auto', margin: '0.75rem 0' }}>
                  <table
                    style={{
                      width: '100%',
                      borderCollapse: 'collapse',
                      fontSize: '0.9rem',
                    }}
                  >
                    {children}
                  </table>
                </div>
              ),
              thead: ({ children }) => (
                <thead>
                  <tr style={{ borderBottom: '2px solid #475569' }}>{children}</tr>
                </thead>
              ),
              th: ({ children }) => (
                <th
                  style={{
                    textAlign: 'left',
                    padding: '0.5rem 0.75rem',
                    color: '#93c5fd',
                    fontWeight: 600,
                  }}
                >
                  {children}
                </th>
              ),
              td: ({ children }) => (
                <td
                  style={{
                    padding: '0.5rem 0.75rem',
                    color: '#cbd5e1',
                    borderBottom: '1px solid #334155',
                  }}
                >
                  {children}
                </td>
              ),
              tr: ({ children }) => <tr>{children}</tr>,
              tbody: ({ children }) => <tbody>{children}</tbody>,
              a: ({ href, children }) => (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: '#93c5fd', textDecoration: 'underline' }}
                >
                  {children}
                </a>
              ),
              hr: () => (
                <hr style={{ border: 'none', borderTop: '1px solid #334155', margin: '1.5rem 0' }} />
              ),
              pre: ({ children }) => children,
            }}
          >
            {displayContent}
          </ReactMarkdown>
        </article>
      )}
    </div>
  );
}
