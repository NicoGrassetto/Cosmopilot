<script>
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();

  export let disabled = false;

  let inputValue = '';
  let inputElement;

  function handleSend() {
    const trimmedValue = inputValue.trim();
    if (trimmedValue) {
      dispatch('sendMessage', trimmedValue);
      inputValue = '';
      inputElement?.focus();
    }
  }

  function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  }

  function handleInputChange(event) {
    inputValue = event.target.value;
  }
</script>

<div class="input-container">
  <div class="input-wrapper">
    <input
      bind:this={inputElement}
      type="text"
      placeholder="Type your message..."
      value={inputValue}
      on:change={handleInputChange}
      on:input={handleInputChange}
      on:keypress={handleKeyPress}
      disabled={disabled}
      class:disabled
    />
    <button on:click={handleSend} disabled={disabled || !inputValue.trim()} class:disabled aria-label="Send message">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <line x1="22" y1="2" x2="11" y2="13"></line>
        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
      </svg>
    </button>
  </div>
</div>

<style>
  .input-container {
    padding: 16px 24px 24px 24px;
    background: white;
    border-top: 1px solid #e5e7eb;
  }

  .input-wrapper {
    display: flex;
    gap: 12px;
    align-items: flex-end;
  }

  input {
    flex: 1;
    padding: 12px 16px;
    border: 1px solid #e5e7eb;
    border-radius: 24px;
    font-size: 14px;
    font-family: inherit;
    outline: none;
    transition: all 0.2s ease;
    background: #f8f9fa;
  }

  input:focus {
    background: white;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }

  input:disabled,
  input.disabled {
    background: #f3f4f6;
    cursor: not-allowed;
    opacity: 0.6;
  }

  input::placeholder {
    color: #9ca3af;
  }

  button {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    padding: 0;
    border: none;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    cursor: pointer;
    transition: all 0.2s ease;
    flex-shrink: 0;
  }

  button:hover:not(:disabled) {
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  }

  button:active:not(:disabled) {
    transform: scale(0.95);
  }

  button:disabled,
  button.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
