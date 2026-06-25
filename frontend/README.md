# Cosmopilot Frontend

A modern, high-performance chatbot UI built with **Svelte**, the fastest frontend framework.

## 🚀 Performance Comparison: Svelte vs React vs Vue

Based on 2024-2025 benchmarks, here's how they compare:

### Performance Metrics

| Framework | Bundle Size | FCP | TTI | Memory | Render Speed |
|-----------|------------|-----|-----|--------|--------------|
| **Svelte 5** | 3-12 KB | 800ms | 1.2s | 35 MB | ⚡ Fastest |
| **Vue 4** | 22 KB | 1000ms | 1.5s | 45 MB | 🟢 Very Good |
| **React 19** | 42-45 KB | 1200ms | 1.8s | 65 MB | 🟡 Good |

### Why Svelte is Fastest?
- **Compile-time magic**: Svelte compiles components at build time and ships **zero runtime framework**
- **No Virtual DOM**: Generates highly optimized vanilla JavaScript
- **Minimal overhead**: Only includes the code you actually use
- **Reactive by default**: Built-in reactivity without extra libraries

## 📦 Project Structure

```
frontend/
├── src/
│   ├── App.svelte                 # Main app component
│   ├── components/
│   │   ├── Chatbot.svelte        # Chat interface
│   │   ├── MessageBubble.svelte   # Message display
│   │   └── InputBox.svelte        # Input field
│   ├── main.js
│   └── app.css
├── public/
├── index.html
├── vite.config.js
└── package.json
```

## 🛠️ Development

### Installation

```bash
npm install
```

### Run Dev Server

```bash
npm run dev
```

Then open [http://localhost:5173](http://localhost:5173)

### Build for Production

```bash
npm run build
```

Output: `dist/` folder ready for deployment

### Preview Production Build

```bash
npm run preview
```

## 🎨 Features

- ✨ **Modern UI** - Gradient header, smooth animations
- 💬 **Message Bubbles** - Distinct styling for user/bot messages
- ⌨️ **Input Handling** - Send with button or Enter key
- 🔄 **Typing Indicator** - Animated dots while bot "types"
- 📱 **Responsive Design** - Works on all screen sizes
- 🎯 **Ready for Backend** - Easily connect to Azure Cosmos DB when ready

## 📝 Dependencies

```json
{
  "svelte": "^4.0.0",
  "vite": "^5.0.0"
}
```

Pure HTML, CSS, and Svelte - no external UI libraries!

## 🔗 Connecting to Backend

When ready to connect to Azure Cosmos DB, update the `handleSendMessage()` function in `src/components/Chatbot.svelte` to:

```javascript
async function handleSendMessage(event) {
  const userMessage = event.detail;
  
  messages = [...messages, {
    id: messages.length + 1,
    text: userMessage,
    sender: 'user',
    timestamp: new Date()
  }];
  
  scrollToBottom();
  isLoading = true;
  
  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userMessage })
    });
    
    const data = await response.json();
    messages = [...messages, {
      id: messages.length + 1,
      text: data.reply,
      sender: 'bot',
      timestamp: new Date()
    }];
  } catch (error) {
    console.error('Error:', error);
  } finally {
    isLoading = false;
    scrollToBottom();
  }
}
```

## 📊 Bundle Size

- **Development**: ~43 KB (with all source maps)
- **Production**: 16.97 KB gzipped (includes all dependencies)
- **CSS**: 2.46 KB gzipped

Compare to React/Vue which typically ship 40-45 KB just for the framework.

## 🎯 Next Steps

1. ✅ Frontend UI complete - currently using demo responses
2. ⏳ Connect to backend API
3. ⏳ Integrate Azure Cosmos DB for message persistence
4. ⏳ Add authentication
5. ⏳ Deploy to Azure

## 📖 Resources

- [Svelte Documentation](https://svelte.dev)
- [Vite Documentation](https://vitejs.dev)
- [Performance Benchmarks](https://usama.codes/blog/svelte-5-vs-react-19-vs-vue-4-comparison)

---

Built with ⚡ Svelte for maximum performance
