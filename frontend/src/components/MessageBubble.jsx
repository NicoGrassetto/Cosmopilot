function formatTime(ts) {
  const d = ts instanceof Date ? ts : new Date(ts);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function MessageBubble({ message }) {
  const { sender, text, timestamp } = message;
  return (
    <div className={`bubble-row bubble-row--${sender}`}>
      <div className={`bubble bubble--${sender}`}>
        <span className="bubble-text">{text}</span>
        <span className="bubble-time">{formatTime(timestamp)}</span>
      </div>
    </div>
  );
}
