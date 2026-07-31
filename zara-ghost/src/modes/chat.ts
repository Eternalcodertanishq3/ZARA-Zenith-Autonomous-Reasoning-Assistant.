export function initChatMode(
  dom: { input: HTMLInputElement | null; messages: HTMLElement | null },
  siriState: any
) {
  async function send(): Promise<void> {
    if (!dom.input) return;
    const text = dom.input.value.trim();
    if (!text) return;
    dom.input.value = '';
    dom.input.blur();

    addMessage(text, 'user');
    siriState.select('thinking');

    try {
      const response = await fetch('http://127.0.0.1:11434/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: 'gemma3:4b', prompt: text, stream: false }),
      });

      const burstDelay = siriState.conclude();
      await new Promise((r) => setTimeout(r, burstDelay));
      siriState.select('answer');

      if (response.ok) {
        const data = await response.json();
        addMessage(data.response || 'No response.', 'bot');
      } else {
        addMessage('Error: Could not reach local Ollama model.', 'bot');
      }
    } catch {
      const burstDelay = siriState.conclude();
      await new Promise((r) => setTimeout(r, burstDelay));
      siriState.select('answer');
      addMessage('Error: Local AI backend offline.', 'bot');
    }
  }

  function addMessage(textMsg: string, sender: 'user' | 'bot'): void {
    if (!dom.messages) return;
    const div = document.createElement('div');
    div.className = `msg ${sender} reveal`;
    div.textContent = textMsg;
    dom.messages.appendChild(div);
    dom.messages.scrollTop = dom.messages.scrollHeight;
  }

  return { send, addMessage };
}
