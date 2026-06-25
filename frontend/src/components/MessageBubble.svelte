<script>
  export let message;

  function formatTime(date) {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }
</script>

<div class="message-wrapper" class:user={message.sender === 'user'}>
  <div class="message-bubble" class:user={message.sender === 'user'}>
    <p>{message.text}</p>
    <span class="timestamp">{formatTime(message.timestamp)}</span>
  </div>
</div>

<style>
  .message-wrapper {
    display: flex;
    justify-content: flex-start;
  }

  .message-wrapper.user {
    justify-content: flex-end;
  }

  .message-bubble {
    max-width: 70%;
    padding: 12px 16px;
    border-radius: 12px;
    background: white;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    border: 1px solid #e5e7eb;
  }

  .message-bubble.user {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }

  .message-bubble p {
    margin: 0;
    font-size: 14px;
    line-height: 1.5;
    word-wrap: break-word;
  }

  .timestamp {
    display: block;
    font-size: 11px;
    margin-top: 6px;
    opacity: 0.6;
  }

  .message-bubble.user .timestamp {
    opacity: 0.8;
  }
</style>
