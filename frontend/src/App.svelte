<script>
  import Chatbot from './components/Chatbot.svelte';
</script>

<main>
  <Chatbot />
</main>

<style>
  :global(* ) {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  :global(body) {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    height: 100vh;
    overflow: hidden;
  }

  main {
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
  }
</style>
