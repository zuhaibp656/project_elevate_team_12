document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const chatHistory = document.getElementById('chatHistory');

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const text = userInput.value.trim();
        if (!text) return;

        // Add user message
        appendMessage('user-msg', text, '👤');
        userInput.value = '';

        // Add loading indicator
        const loadingId = appendLoading();

        try {
            // In a real integration, this connects to the ADK agent endpoint (e.g. FastAPI / Flask)
            // For now, we simulate a network call to the backend
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: text })
            });
            
            removeElement(loadingId);
            
            if (response.ok) {
                const data = await response.json();
                appendMessage('system-msg', data.reply, '🤖');
            } else {
                appendMessage('system-msg', 'Error connecting to the agent backend.', '⚠️');
            }
        } catch (error) {
            removeElement(loadingId);
            // Fallback mock response for UI demonstration purposes when backend is offline
            setTimeout(() => {
                appendMessage('system-msg', 'I am currently operating in offline UI demo mode. I received: "' + text + '"', '🤖');
            }, 800);
        }
    });

    function appendMessage(type, text, avatar) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${type}`;
        
        const content = `
            ${type === 'system-msg' ? `<div class="avatar">${avatar}</div>` : ''}
            <div class="bubble">${text}</div>
            ${type === 'user-msg' ? `<div class="avatar">${avatar}</div>` : ''}
        `;
        
        msgDiv.innerHTML = content;
        chatHistory.appendChild(msgDiv);
        scrollToBottom();
    }

    function appendLoading() {
        const id = 'loading-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message system-msg';
        msgDiv.id = id;
        
        msgDiv.innerHTML = `
            <div class="avatar">🤖</div>
            <div class="bubble">
                <div class="loading-dots">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        
        chatHistory.appendChild(msgDiv);
        scrollToBottom();
        return id;
    }

    function removeElement(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function scrollToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
});
