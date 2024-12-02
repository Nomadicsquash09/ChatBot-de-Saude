let isWaitingForResponse = false;

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function submitQuestion() {
    const question = document.getElementById("question").value.trim();
    if (!question) return;

    fetch('/ask/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ question: question })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erro na resposta da rede');
        }
        return response.json();
    })
    .then(data => {
        document.getElementById("responseTextarea").value = data.response || "Sem resposta.";
    })
    .catch(error => console.error('Erro:', error));
}

function toggleInput(isEnabled) {
    const userInput = document.getElementById("user-input");
    userInput.disabled = !isEnabled;
}

function sendMessage() {
    const userInput = document.getElementById("user-input").value;
    const chatBox = document.getElementById("chat-box");  

    if (userInput.trim() !== "") {
        chatBox.innerHTML += `
            <div class="message user">
                <div class="message-avatar">👤</div>
                <div class="message-content">${userInput}</div>
            </div>
        `;

        document.getElementById("user-input").value = "";

        toggleInput(false);

        fetch('/ask/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ question: userInput })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error in network response');
            }
            return response.json();
        })
        .then(data => {
            chatBox.innerHTML += `
                <div class="message bot">
                    <div class="message-avatar">🤖</div>
                    <div class="message-content">${data.response}</div>
                </div>
            `;
            chatBox.scrollTop = chatBox.scrollHeight;
        })
        .catch(error => {
            console.error('Error fetching response:', error);
            alert('Error communicating with the server: ' + error.message);
        })
        .finally(() => {
            toggleInput(true);
        });
    }
}

function addMessage(type, avatar, content) {
    const chatBox = document.getElementById("chat-box");

    const message = document.createElement("div");
    message.classList.add("message", type);

    message.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">${content}</div>
    `;

    chatBox.appendChild(message);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function typeMessage(type, avatar, fullText) {
    const chatBox = document.getElementById("chat-box");

    const message = document.createElement("div");
    message.classList.add("message", type);
    message.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content"></div>
    `;

    const messageContent = message.querySelector(".message-content");
    chatBox.appendChild(message);

    let index = 0;

    function typeCharacter() {
        if (index < fullText.length) {
            messageContent.textContent += fullText[index];
            index++;
            setTimeout(typeCharacter, 15);
        } else {
            isWaitingForResponse = false;
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    }

    typeCharacter();
}

function highlightButton() {
    const sendButton = document.getElementById("send-button");
    sendButton.classList.replace("btn-primary", "btn-success");
}

function resetButton() {
    const sendButton = document.getElementById("send-button");
    sendButton.classList.replace("btn-success", "btn-primary");
}

document.addEventListener("DOMContentLoaded", () => {
    const userInput = document.getElementById("user-input");
    const sendButton = document.getElementById("send-button");

    userInput.addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            sendMessage();
        }
    });

    sendButton.addEventListener("click", sendMessage);

    sendButton.addEventListener("mouseover", highlightButton);
    sendButton.addEventListener("mouseout", resetButton);
});
