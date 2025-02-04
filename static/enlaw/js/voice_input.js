let recognition;
let isRecording = false;

function updateVoiceStatus(message, isError = false) {
    const statusEl = document.getElementById('voiceStatus');
    if (statusEl) {
        statusEl.textContent = message;
        statusEl.className = `text-sm ${isError ? 'text-red-500' : 'text-gray-600'}`;
    }
}

function startVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
        updateVoiceStatus('Speech recognition not supported in this browser', true);
        return;
    }

    if (isRecording) {
        recognition?.stop();
        return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        isRecording = true;
        updateVoiceStatus('Listening...');
        const activeField = document.querySelector('.editable-field:focus');
        if (activeField) {
            activeField.classList.add('recording-active');
        }
    };

    recognition.onend = () => {
        isRecording = false;
        updateVoiceStatus('');
        document.querySelectorAll('.recording-active').forEach(el => {
            el.classList.remove('recording-active');
        });
    };

    recognition.onerror = (event) => {
        isRecording = false;
        updateVoiceStatus(`Error: ${event.error}`, true);
        document.querySelectorAll('.recording-active').forEach(el => {
            el.classList.remove('recording-active');
        });
    };

    recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
            .map(result => result[0].transcript)
            .join('');

        const activeField = document.querySelector('.editable-field:focus');
        if (activeField) {
            if (event.results[0].isFinal) {
                activeField.textContent = transcript;
                // Trigger change event for validation
                activeField.dispatchEvent(new Event('input'));
            }
        } else {
            updateVoiceStatus('Please select a field to edit', true);
        }
    };

    try {
        recognition.start();
    } catch (error) {
        updateVoiceStatus('Error starting voice recognition', true);
    }
}

// Initialize voice controls
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.editable-field').forEach(field => {
        field.contentEditable = true;
        
        field.addEventListener('focus', function() {
            if (isRecording) {
                this.classList.add('recording-active');
            }
        });
        
        field.addEventListener('blur', function() {
            this.classList.remove('recording-active');
        });

        // Add validation on input
        field.addEventListener('input', function() {
            if (this.hasAttribute('required') && !this.textContent.trim()) {
                this.classList.add('field-invalid');
            } else {
                this.classList.remove('field-invalid');
            }
        });
    });
});
