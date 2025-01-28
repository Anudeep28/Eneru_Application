$(document).ready(function() {
    const chatMessages = $('.chat-messages-gemini');
    const chatForm = $('#chat-form');
    const chatInput = $('#chat-input-gemini');
    const sendButton = $('#send-button-gemini');
    const clearButton = $('#clear-chat');
    let isFirstLoad = true;

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

    // Function to format timestamp
    function formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        if (date.toDateString() === today.toDateString()) {
            return 'Today';
        } else if (date.toDateString() === yesterday.toDateString()) {
            return 'Yesterday';
        } else {
            return date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
        }
    }

    // Function to add a message to the chat
    function addMessage(message, isUser = false, timestamp = new Date()) {
        const messageDiv = $('<div>').addClass('message p-3 mb-3 rounded-lg ' + 
            (isUser ? 'ml-auto bg-indigo-500 text-white user-message' : 'mr-auto bg-gray-100'));
        messageDiv.css('max-width', '80%');
        
        // Add timestamp
        const timestampDiv = $('<div>').addClass('text-xs text-gray-500 mt-1')
            .text(new Date(timestamp).toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit'
            }));
        
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

        // Add timestamp to message
        messageDiv.append(timestampDiv);
        
        // Check if we need to add a date separator
        const lastDateSeparator = chatMessages.find('.conversation-date:last');
        const lastDate = lastDateSeparator.length ? lastDateSeparator.data('date') : null;
        const currentDate = formatTimestamp(timestamp);
        
        if (!lastDate || lastDate !== currentDate) {
            const dateSeparator = $('<div>')
                .addClass('conversation-date')
                .text(currentDate)
                .data('date', currentDate);
            chatMessages.append(dateSeparator);
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
                'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val(),
                'conversation_id': $('input[name=conversation_id]').val()
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
        if (confirm('Are you sure you want to clear the chat history? This will only clear the display, not the stored conversation.')) {
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

    // Add welcome message if no previous messages
    function addWelcomeMessage() {
        if (chatMessages.children().length === 0) {
            setTimeout(() => {
                addMessage(`👋 Hello! I'm Eneru, your AI assistant.

I can help you with:
- Answering questions
- Writing and reviewing code
- Explaining concepts
- Solving problems
- And much more!

I remember our conversations, so feel free to refer to our previous discussions! 😊`);
            }, 500);
        }
    }

    // Initialize chat
    if (isFirstLoad) {
        isFirstLoad = false;
        if (chatMessages.children().length === 0) {
            addWelcomeMessage();
        }
    }

    // Initialize syntax highlighting for any existing code blocks
    chatMessages.find('pre code').each(function(i, block) {
        hljs.highlightElement(block);
    });
});