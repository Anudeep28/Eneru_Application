$(document).ready(function() {
    const chatMessages = $('.chat-messages-gemini');
    const chatForm = $('#chat-form');
    const chatInput = $('#chat-input-gemini');
    const sendButton = $('#send-button-gemini');
    const clearButton = $('#clear-chat');

    // Configure marked.js
    marked.setOptions({
        gfm: true,
        breaks: true,
        pedantic: false,
        sanitize: false,
        smartLists: true,
        smartypants: true,
        xhtml: false,
        highlight: function(code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                try {
                    return hljs.highlight(code, { language: lang }).value;
                } catch (e) {
                    console.error('Error highlighting code:', e);
                }
            }
            return hljs.highlightAuto(code).value;
        }
    });

    // Function to add a message to the chat
    function addMessage(message, isUser = false) {
        const messageDiv = $('<div>').addClass('message p-3 mb-3 rounded-lg ' + 
            (isUser ? 'ml-auto bg-indigo-500 text-white user-message' : 'mr-auto bg-gray-100'));
        messageDiv.css('max-width', '80%');
        
        if (isUser) {
            // For user messages, just show the text
            messageDiv.text(message);
        } else {
            // For bot messages, render markdown
            try {
                const formattedMessage = marked.parse(message);
                messageDiv.html(formattedMessage);
                
                // Apply syntax highlighting to code blocks
                messageDiv.find('pre code').each(function(i, block) {
                    hljs.highlightElement(block);
                });

                // Style code blocks
                messageDiv.find('pre').addClass('bg-gray-800 p-3 rounded-lg mt-2 mb-2 overflow-x-auto');
                messageDiv.find('code').addClass('text-sm');
                
                // Style other elements
                messageDiv.find('a').addClass('text-blue-600 hover:underline');
                messageDiv.find('ul, ol').addClass('pl-4 my-2');
                messageDiv.find('li').addClass('mb-1');
                messageDiv.find('p').addClass('mb-2');
                messageDiv.find('blockquote').addClass('border-l-4 border-gray-300 pl-3 my-2');
            } catch (e) {
                console.error('Markdown parsing error:', e);
                messageDiv.text(message);
            }
        }
        
        chatMessages.append(messageDiv);
        scrollToBottom();
    }

    // Handle form submission
    chatForm.on('submit', function(e) {
        e.preventDefault();
        
        const message = chatInput.val().trim();
        if (!message) return;

        // Add user message
        addMessage(message, true);
        
        // Clear input
        chatInput.val('');

        // Show loading message
        const loadingDiv = $('<div>')
            .addClass('message p-3 mb-3 rounded-lg mr-auto bg-gray-100')
            .css('max-width', '80%')
            .html('<div class="flex space-x-2"><div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div><div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div><div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div></div>');
        chatMessages.append(loadingDiv);
        scrollToBottom();

        // Send message to server
        $.ajax({
            type: 'POST',
            url: '/chatbot/geminiChat/',
            data: {
                'message': message,
                'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                loadingDiv.remove();
                if (response.status === 'success') {
                    addMessage(response.response);
                } else {
                    addMessage('Error: Failed to get response from the bot.');
                }
            },
            error: function() {
                loadingDiv.remove();
                addMessage('Error: Failed to send message.');
            }
        });
    });

    // Handle enter key
    chatInput.on('keypress', function(e) {
        if (e.which === 13 && !e.shiftKey) {
            chatForm.submit();
            return false;
        }
    });

    // Clear chat
    clearButton.on('click', function() {
        if (confirm('Are you sure you want to clear the chat history?')) {
            chatMessages.empty();
            addWelcomeMessage();
        }
    });

    // Smooth scroll to bottom
    function scrollToBottom() {
        chatMessages.stop().animate({
            scrollTop: chatMessages[0].scrollHeight
        }, 300);
    }

    // Add welcome message
    function addWelcomeMessage() {
        setTimeout(() => {
            addMessage(`👋 Hello! I'm Eneru, your AI assistant.

I can help you with:
- Answering questions
- Writing and reviewing code
- Explaining concepts
- Solving problems
- And much more!

Feel free to ask me anything! 😊`);
        }, 500); // Delay to show animation
    }

    // Add initial welcome message
    addWelcomeMessage();
});