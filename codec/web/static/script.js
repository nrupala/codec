const terminalBody = document.getElementById('terminal-body');
const input = document.getElementById('terminal-input');
const sendBtn = document.getElementById('send-btn');
let processing = false;

function addMessage(content, role) {
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  div.innerHTML = content.replace(/\n/g, '<br>');
  terminalBody.appendChild(div);
  terminalBody.scrollTop = terminalBody.scrollHeight;
}

function formatResponse(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text || processing) return;

  input.value = '';
  addMessage(formatResponse(text), 'user');
  processing = true;
  sendBtn.disabled = true;
  input.disabled = true;

  const loadingDiv = document.createElement('div');
  loadingDiv.className = 'msg assistant';
  loadingDiv.textContent = 'Thinking...';
  terminalBody.appendChild(loadingDiv);

  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });
    const data = await resp.json();
    terminalBody.removeChild(loadingDiv);

    if (data.error) {
      addMessage(formatResponse(data.error), 'error');
    } else {
      addMessage(formatResponse(data.response), 'assistant');
    }
  } catch (err) {
    terminalBody.removeChild(loadingDiv);
    addMessage(`Connection error: ${err.message}`, 'error');
  } finally {
    processing = false;
    sendBtn.disabled = false;
    input.disabled = false;
    input.focus();
  }
}

sendBtn.addEventListener('click', sendMessage);
input.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendMessage(); });
input.focus();
