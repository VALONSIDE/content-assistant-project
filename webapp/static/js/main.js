// webapp/static/js/main.js
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('message-form');
    const input = document.getElementById('message-input');
    const chatWindow = document.getElementById('chat-window');

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const userMessage = input.value.trim();
        if (!userMessage) return;

        // 1. 在界面上显示用户自己的消息
        addMessageToChat('user', userMessage);
        input.value = '';
        
        // 2. 显示“思考中”的提示
        const thinkingMessage = addMessageToChat('agent', '思考中...');

        try {
            // 3. 异步调用后端 API
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: userMessage }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // 4. 用 Agent 的真实回复更新“思考中”的消息
            thinkingMessage.querySelector('.content').textContent = data.response || "抱歉，我遇到了一些问题。";

        } catch (error) {
            console.error('Fetch error:', error);
            thinkingMessage.querySelector('.content').textContent = `出错了: ${error.message}`;
        }
    });

    function addMessageToChat(role, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        
        const avatar = role === 'user' ? '👤' : '🤖';
        const content = text.replace(/\n/g, '<br>'); // 支持换行

        messageDiv.innerHTML = `
            <div class="avatar">${avatar}</div>
            <div class="content">${content}</div>
        `;
        chatWindow.appendChild(messageDiv);
        
        // 自动滚动到底部
        chatWindow.scrollTop = chatWindow.scrollHeight;
        
        // 如果是“思考中”消息，返回该元素以便后续更新
        if (text === '思考中...') {
            return messageDiv;
        }
    }
});