// Haven JARVIS Dashboard - Frontend Logic

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const micButton = document.getElementById('mic-button');
const speakerButton = document.getElementById('speaker-button');
const statusIndicator = document.getElementById('status-indicator');
const connectionStatus = document.getElementById('connection-status');
const typingIndicator = document.getElementById('typing-indicator');
const agentToggle = document.getElementById('agent-toggle');

// WebSocket connection
let ws = null;
let isConnected = false;
let speakerEnabled = true; // Auto-enable speaker for Kokoro voice
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let ttsLoaded = false;
let sttLoaded = false;

// Connect to WebSocket
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${protocol}://${window.location.host}/ws/chat`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        isConnected = true;
        statusIndicator.className = 'status-indicator online';
        connectionStatus.textContent = 'Connected';
        chatInput.disabled = false;
        sendButton.disabled = false;
        speakerButton.disabled = false;
        console.log('[Haven] Connected to WebSocket');
    };

    ws.onclose = () => {
        isConnected = false;
        statusIndicator.className = 'status-indicator offline';
        connectionStatus.textContent = 'Disconnected - Reconnecting...';
        chatInput.disabled = true;
        sendButton.disabled = true;
        console.log('[Haven] WebSocket disconnected');
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = (error) => {
        console.error('[Haven] WebSocket error:', error);
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };
}

// Handle incoming messages
function handleMessage(data) {
    switch (data.type) {
        case 'message':
            typingIndicator.style.display = 'none';
            addMessage(data.text, data.role);
            // Play Kokoro TTS audio if included with message
            if (data.audio && data.role === 'haven') {
                playAudioBase64(data.audio);
            } else if (speakerEnabled && data.role === 'haven' && !ttsLoaded) {
                // Fallback to browser speech only if TTS is not loaded
                speakText(data.text);
            }
            break;
        case 'audio':
            // Delayed TTS audio arrives after the text message (fallback)
            if (data.audio && speakerEnabled) {
                playAudioBase64(data.audio);
            }
            break;
        case 'typing':
            typingIndicator.style.display = 'inline';
            break;
        case 'error':
            typingIndicator.style.display = 'none';
            addMessage(data.text, 'error');
            break;
    }
}

// Add message to chat
function addMessage(text, role) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.textContent = text;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Send message
function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || !isConnected) return;

    addMessage(text, 'user');
    chatInput.value = '';
    typingIndicator.style.display = 'inline';

    ws.send(JSON.stringify({ text: text }));
}

// Play audio from base64-encoded WAV (Kokoro TTS)
function playAudioBase64(audioBase64) {
    try {
        const binary = atob(audioBase64);
        const array = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
            array[i] = binary.charCodeAt(i);
        }
        const blob = new Blob([array], { type: 'audio/wav' });
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.play().catch(err => console.error('[Haven] Audio play error:', err));
        audio.onended = () => URL.revokeObjectURL(url);
    } catch (err) {
        console.error('[Haven] Failed to play audio:', err);
    }
}

// Fallback: speak text using Web Speech API (only if Kokoro TTS is not loaded)
function speakText(text) {
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'en-US';
        utterance.rate = 1.0;
        utterance.pitch = 1.1;

        // Try to find a female voice
        const voices = window.speechSynthesis.getVoices();
        const femaleVoice = voices.find(v =>
            v.lang.startsWith('en') && (v.name.toLowerCase().includes('female') ||
            v.name.toLowerCase().includes('zira') || v.name.toLowerCase().includes('samantha'))
        );
        if (femaleVoice) {
            utterance.voice = femaleVoice;
        }

        window.speechSynthesis.speak(utterance);
    }
}

// Toggle speaker
speakerButton.addEventListener('click', () => {
    speakerEnabled = !speakerEnabled;
    speakerButton.style.background = speakerEnabled ? '#1a73e8' : 'transparent';
    speakerButton.style.color = speakerEnabled ? 'white' : '#1a73e8';
});

// Voice recording — sends audio to server for Vosk STT
micButton.addEventListener('click', () => {
    if (!isRecording) {
        startRecording();
    } else {
        stopRecording();
    }
});

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: { 
                channelCount: 1,
                sampleRate: 16000,
                echoCancellation: true,
                noiseSuppression: true 
            } 
        });
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            sendAudioToServer(audioBlob);
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        isRecording = true;
        micButton.classList.add('recording');
    } catch (error) {
        console.error('[Haven] Microphone error:', error);
        addMessage('Microphone not available. Please check permissions.', 'error');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        micButton.classList.remove('recording');
    }
}

// Send recorded audio to server for Vosk STT
async function sendAudioToServer(audioBlob) {
    if (!sttLoaded) {
        // Fallback to browser speech recognition if STT is not loaded
        recognizeSpeechFallback();
        return;
    }

    try {
        const formData = new FormData();
        formData.append('file', audioBlob, 'audio.webm');

        const response = await fetch('/api/voice/stt', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`STT failed: ${response.status}`);
        }

        const data = await response.json();
        const transcript = data.text;

        if (transcript) {
            chatInput.value = transcript;
            sendMessage();
        } else {
            addMessage("I didn't catch that. Could you try again?", 'haven');
        }
    } catch (error) {
        console.error('[Haven] STT error:', error);
        addMessage('Speech recognition failed. Please try again.', 'error');
    }
}

// Fallback: browser speech recognition (only if server STT is not loaded)
function recognizeSpeechFallback() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            chatInput.value = transcript;
            sendMessage();
        };

        recognition.onerror = (event) => {
            console.error('[Haven] Speech recognition error:', event.error);
            addMessage('Speech recognition failed. Please try again.', 'error');
        };

        recognition.start();
    } else {
        addMessage('Speech recognition not supported in this browser.', 'error');
    }
}

// Event listeners
sendButton.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Agent toggle
agentToggle.addEventListener('change', () => {
    console.log('[Haven] Agent toggled:', agentToggle.checked ? 'enabled' : 'disabled');
});

// Fetch system info
async function fetchSystemInfo() {
    try {
        const response = await fetch('/api/system');
        const data = await response.json();

        document.getElementById('cpu-bar').style.width = `${data.cpu_percent}%`;
        document.getElementById('cpu-percent').textContent = `${Math.round(data.cpu_percent)}%`;

        document.getElementById('ram-bar').style.width = `${data.memory_percent}%`;
        document.getElementById('ram-percent').textContent = `${Math.round(data.memory_percent)}%`;

        document.getElementById('disk-bar').style.width = `${data.disk_percent}%`;
        document.getElementById('disk-percent').textContent = `${Math.round(data.disk_percent)}%`;
    } catch (error) {
        console.error('[Haven] Failed to fetch system info:', error);
    }
}

// Fetch status
async function fetchStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        document.getElementById('model-status').textContent = data.model_loaded ? 'Loaded' : 'Not loaded';
        document.getElementById('memory-status').textContent = data.memory_loaded ? 'Active' : 'Not loaded';
        
        // Update voice status
        ttsLoaded = data.tts_loaded || false;
        sttLoaded = data.stt_loaded || false;
        
        const ttsEl = document.getElementById('tts-status');
        const sttEl = document.getElementById('stt-status');
        
        if (ttsEl) {
            ttsEl.textContent = ttsLoaded ? `Active (${data.tts_voice || 'af_heart'})` : 'Not loaded';
            ttsEl.style.color = ttsLoaded ? '#4caf50' : '#ff9800';
        }
        if (sttEl) {
            sttEl.textContent = sttLoaded ? 'Active' : 'Not loaded';
            sttEl.style.color = sttLoaded ? '#4caf50' : '#ff9800';
        }
        
        // Enable/disable mic button based on STT availability
        if (micButton) {
            micButton.disabled = !sttLoaded;
            micButton.title = sttLoaded ? 'Speak (Vosk STT)' : 'STT not loaded — use text';
        }
        
        // Set speaker button state (enabled by default when TTS is loaded)
        if (speakerButton && ttsLoaded) {
            speakerEnabled = true;
            speakerButton.style.background = '#1a73e8';
            speakerButton.style.color = 'white';
        }
    } catch (error) {
        console.error('[Haven] Failed to fetch status:', error);
    }
}

// Initialize
window.addEventListener('load', () => {
    connectWebSocket();
    fetchStatus();
    fetchSystemInfo();

    // Update system info every 5 seconds
    setInterval(fetchSystemInfo, 5000);

    // Load voices for speech synthesis
    if ('speechSynthesis' in window) {
        window.speechSynthesis.getVoices();
        window.speechSynthesis.onvoiceschanged = () => {
            window.speechSynthesis.getVoices();
        };
    }

    // Welcome message
    addMessage('Hello! I\'m Haven. How can I help you today?', 'haven');
});
