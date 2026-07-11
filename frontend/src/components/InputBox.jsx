import { useRef, useState } from 'react';
import AgentMenu from './AgentMenu.jsx';

export default function InputBox({
  onSend,
  disabled,
  placeholder,
  agents,
  selectedAgent,
  onSelectAgent,
  agentsLoading,
  agentsError,
}) {
  const [value, setValue] = useState('');
  const [files, setFiles] = useState([]);
  const inputRef = useRef(null);
  const fileRef = useRef(null);

  function send() {
    const trimmed = value.trim();
    if ((!trimmed && files.length === 0) || disabled) return;
    onSend(trimmed, files);
    setValue('');
    setFiles([]);
    inputRef.current?.focus();
  }

  function onKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  function onPickFiles(e) {
    const picked = Array.from(e.target.files || []);
    if (picked.length) setFiles((prev) => [...prev, ...picked]);
    e.target.value = '';
  }

  function removeFile(idx) {
    setFiles((prev) => prev.filter((_, i) => i !== idx));
  }

  return (
    <div className="composer">
      {files.length > 0 && (
        <div className="attachments">
          {files.map((f, i) => (
            <span className="chip" key={`${f.name}-${i}`}>
              <span className="chip-name">{f.name}</span>
              <button className="chip-x" onClick={() => removeFile(i)} aria-label={`Remove ${f.name}`}>
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      <div className="pill">
        {/* Attach (left) */}
        <input ref={fileRef} type="file" multiple hidden onChange={onPickFiles} />
        <button
          type="button"
          className="icon-btn"
          onClick={() => fileRef.current?.click()}
          aria-label="Attach files"
          title="Attach files"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M21.44 11.05l-9.19 9.19a5 5 0 0 1-7.07-7.07l9.19-9.19a3.5 3.5 0 0 1 4.95 4.95l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
          </svg>
        </button>

        <input
          ref={inputRef}
          className="pill-input"
          type="text"
          value={value}
          placeholder={placeholder}
          disabled={disabled}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKeyDown}
        />

        {/* Agent selector */}
        <AgentMenu
          agents={agents}
          value={selectedAgent}
          onChange={onSelectAgent}
          loading={agentsLoading}
          error={agentsError}
        />

        {/* Voice (decorative button, no logic per request) */}
        <button type="button" className="mic-btn" aria-label="Voice input" title="Voice input">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <rect x="9" y="3" width="6" height="11" rx="3" />
            <path d="M5 11a7 7 0 0 0 14 0" />
            <line x1="12" y1="18" x2="12" y2="21" />
          </svg>
        </button>

        {/* Send appears when there's something to send */}
        {(value.trim() || files.length > 0) && (
          <button type="button" className="send-btn" onClick={send} disabled={disabled} aria-label="Send message">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <line x1="12" y1="19" x2="12" y2="5" />
              <polyline points="5 12 12 5 19 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
