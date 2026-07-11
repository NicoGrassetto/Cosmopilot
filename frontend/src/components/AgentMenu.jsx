import { useEffect, useRef, useState } from 'react';

// A compact button that opens a popover to pick which Foundry agent to talk to.
export default function AgentMenu({ agents, value, onChange, loading, error }) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);

  useEffect(() => {
    function onDocClick(e) {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  const label = error ? 'Agents unavailable' : loading ? 'Loading…' : value || 'Select agent';

  return (
    <div className="agent-menu" ref={wrapRef}>
      <button
        type="button"
        className="pill-btn agent-trigger"
        onClick={() => setOpen((o) => !o)}
        disabled={loading || !!error || agents.length === 0}
        title={error || 'Choose an agent'}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <rect x="4" y="8" width="16" height="12" rx="2" />
          <path d="M12 8V4" />
          <circle cx="12" cy="3" r="1" />
          <path d="M9 13h.01M15 13h.01" />
        </svg>
        <span className="agent-trigger-label">{label}</span>
        <svg className={`chev ${open ? 'up' : ''}`} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {open && (
        <div className="agent-popover" role="listbox">
          {agents.map((a) => (
            <button
              key={a.name}
              type="button"
              role="option"
              aria-selected={a.name === value}
              className={`agent-option ${a.name === value ? 'active' : ''}`}
              onClick={() => {
                onChange(a.name);
                setOpen(false);
              }}
            >
              <span className="agent-option-name">{a.name}</span>
              {a.description && <span className="agent-option-desc">{a.description}</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
