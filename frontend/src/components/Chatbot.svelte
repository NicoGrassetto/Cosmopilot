<script>
  import MessageBubble from './MessageBubble.svelte';
  import InputBox from './InputBox.svelte';
  import { onMount } from 'svelte';

  let messages = [
    {
      id: 1,
      text: 'Hello! 👋 How can I help you today?',
      sender: 'bot',
      timestamp: new Date()
    }
  ];

  let isLoading = false;
  let messagesContainer;

  function scrollToBottom() {
    setTimeout(() => {
      if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }
    }, 0);
  }

  function handleSendMessage(event) {
    const userMessage = event.detail;

    messages = [
      ...messages,
      {
        id: messages.length + 1,
        text: userMessage,
        sender: 'user',
        timestamp: new Date()
      }
    ];

    scrollToBottom();
    isLoading = true;

    setTimeout(() => {
      messages = [
        ...messages,
        {
          id: messages.length + 1,
          text: 'I received your message: "' + userMessage + '". I\'m a demo chatbot waiting to connect to the backend!',
          sender: 'bot',
          timestamp: new Date()
        }
      ];
      isLoading = false;
      scrollToBottom();
    }, 800);
  }

  onMount(() => {
    scrollToBottom();
  });
</script>

<div class="chatbot-container">
  <div class="chatbot-header">
    <div class="header-content">
      <h1>Cosmopilot</h1>
      <p>Chat Assistant</p>
    </div>
    <div class="header-status">
      <div class="status-dot"></div>
      <span>Connected</span>
    </div>
  </div>

  <div class="messages-container" bind:this={messagesContainer}>
    {#each messages as message (message.id)}
      <MessageBubble {message} />
    {/each}
    {#if isLoading}
      <div class="bot-typing">
        <div class="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    {/if}
  </div>

  <InputBox on:sendMessage={handleSendMessage} disabled={isLoading} />
</div>

<style>
  .chatbot-container {
    display: flex;
    flex-direction: column;
    width: 100%;
    max-width: 600px;
    height: 90vh;
    max-height: 800px;
    background: white;
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    overflow: hidden;
  }

  .chatbot-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
  }

  .header-content h1 {
    font-size: 20px;
    font-weight: 700;
    margin: 0;
  }

  .header-content p {
    font-size: 12px;
    opacity: 0.9;
    margin: 4px 0 0 0;
  }

  .header-status {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
  }

  .status-dot {
    width: 8px;
    height: 8px;
    background: #10b981;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }

  .messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    background: #f8f9fa;
  }

  .messages-container::-webkit-scrollbar {
    width: 6px;
  }

  .messages-container::-webkit-scrollbar-track {
    background: transparent;
  }

  .messages-container::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
  }

  .messages-container::-webkit-scrollbar-thumb:hover {
    background: #94a3b8;
  }

  .bot-typing {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .typing-indicator {
    display: flex;
    gap: 4px;
  }

  .typing-indicator span {
    width: 8px;
    height: 8px;
    background: #9ca3af;
    border-radius: 50%;
    animation: typing 1.4s infinite;
  }

  .typing-indicator span:nth-child(2) {
    animation-delay: 0.2s;
  }

  .typing-indicator span:nth-child(3) {
    animation-delay: 0.4s;
  }

  @keyframes typing {
    0%, 60%, 100% {
      transform: translateY(0);
    }
    30% {
      transform: translateY(-10px);
    }
  }
</style>
