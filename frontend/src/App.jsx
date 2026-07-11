import { useEffect, useRef, useState } from 'react';
import Starfield from './components/Starfield.jsx';
import MessageBubble from './components/MessageBubble.jsx';
import InputBox from './components/InputBox.jsx';
import TypingIndicator from './components/TypingIndicator.jsx';
import { fetchAgents, sendChat } from './api.js';

export default function App() {
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState('');
  const [agentsError, setAgentsError] = useState('');
  const [agentsLoading, setAgentsLoading] = useState(true);

  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  // One response id per agent so each keeps its own threaded conversation.
  const [threads, setThreads] = useState({});

  const messagesRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const list = await fetchAgents();
        if (cancelled) return;
        setAgents(list);
        if (list.length > 0) setSelectedAgent(list[0].name);
      } catch (err) {
        if (!cancelled) setAgentsError(err.message);
      } finally {
        if (!cancelled) setAgentsLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const el = messagesRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, isLoading]);

  async function handleSend(text, files = []) {
    if (!selectedAgent) return;

    // The backend has no file channel, so fold attachment names into the prompt
    // to keep the attach button functional end-to-end.
    let outgoing = text;
    if (files.length > 0) {
      const names = files.map((f) => f.name).join(', ');
      outgoing = `${text}${text ? '\n\n' : ''}[Attached: ${names}]`;
    }

    const userMsg = {
      id: `u-${Date.now()}`,
      sender: 'user',
      text: outgoing,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const { reply, response_id } = await sendChat({
        agent: selectedAgent,
        message: outgoing,
        responseId: threads[selectedAgent],
      });
      if (response_id) {
        setThreads((prev) => ({ ...prev, [selectedAgent]: response_id }));
      }
      setMessages((prev) => [
        ...prev,
        { id: `b-${Date.now()}`, sender: 'bot', text: reply, timestamp: new Date() },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { id: `e-${Date.now()}`, sender: 'error', text: `⚠️ ${err.message}`, timestamp: new Date() },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  const hasConversation = messages.length > 0;

  const composer = (
    <InputBox
      onSend={handleSend}
      disabled={isLoading || !selectedAgent}
      placeholder={selectedAgent ? 'Ask anything' : 'Select an agent to begin…'}
      agents={agents}
      selectedAgent={selectedAgent}
      onSelectAgent={setSelectedAgent}
      agentsLoading={agentsLoading}
      agentsError={agentsError}
    />
  );

  return (
    <div className={`app ${hasConversation ? 'chatting' : 'landing'}`}>
      <Starfield />

      {hasConversation ? (
        <div className="chat-view">
          <div className="messages" ref={messagesRef}>
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} />
            ))}
            {isLoading && <TypingIndicator />}
          </div>
          <div className="composer-dock">{composer}</div>
        </div>
      ) : (
        <div className="hero">
          <div className="brand">
            <span className="brand-mark" aria-hidden="true" />
            <h1>Cosmopilot</h1>
          </div>
          {composer}
        </div>
      )}
    </div>
  );
}
