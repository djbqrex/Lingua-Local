/**
 * Main application logic
 */

import { API } from './api.js';
import { AudioRecorder, AudioPlayer } from './audio.js';

class LanguageLearningApp {
    constructor() {
        // UI Elements
        this.conversationHistory = document.getElementById('conversation-history');
        this.recordBtn = document.getElementById('record-btn');
        this.textInput = document.getElementById('text-input');
        this.sendBtn = document.getElementById('send-btn');
        this.languageSelect = document.getElementById('language-select');
        this.difficultySelect = document.getElementById('difficulty-select');
        this.scenarioSelect = document.getElementById('scenario-select');
        this.clearHistoryBtn = document.getElementById('clear-history');
        this.statusIndicator = document.getElementById('status-indicator');
        this.recordingIndicator = document.getElementById('recording-indicator');
        this.audioPlayer = document.getElementById('audio-player');

        // Model status badges
        this.modelStatusSTT = document.getElementById('model-status-stt');
        this.modelStatusLLM = document.getElementById('model-status-llm');
        this.modelStatusTTS = document.getElementById('model-status-tts');

        // Audio handling
        this.recorder = new AudioRecorder();
        this.player = new AudioPlayer(this.audioPlayer);

        // Conversation state
        this.messages = [];
        this.sessionId = this.generateSessionId();

        // Initialize
        this.init();
    }

    /**
     * Initialize the application
     */
    async init() {
        this.setupEventListeners();
        await this.checkModelsStatus();
        this.updateStatus('Ready to practice!', 'success');
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Record button - hold to speak
        this.recordBtn.addEventListener('mousedown', () => this.startRecording());
        this.recordBtn.addEventListener('mouseup', () => this.stopRecording());
        this.recordBtn.addEventListener('mouseleave', () => {
            if (this.recorder.getIsRecording()) {
                this.stopRecording();
            }
        });

        // Touch events for mobile
        this.recordBtn.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.startRecording();
        });
        this.recordBtn.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.stopRecording();
        });

        // Send button
        this.sendBtn.addEventListener('click', () => this.sendTextMessage());

        // Enter key in text input
        this.textInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendTextMessage();
            }
        });

        // Clear history button
        this.clearHistoryBtn.addEventListener('click', () => this.clearHistory());
    }

    /**
     * Check models status
     */
    async checkModelsStatus() {
        try {
            const result = await API.checkModels();
            const models = result.models || {};

            // Update STT status
            this.updateModelBadge(
                this.modelStatusSTT,
                'STT',
                models.stt === 'loaded'
            );

            // Update LLM status
            this.updateModelBadge(
                this.modelStatusLLM,
                'LLM',
                models.llm === 'loaded'
            );

            // Update TTS status
            this.updateModelBadge(
                this.modelStatusTTS,
                'TTS',
                models.tts === 'loaded'
            );

        } catch (error) {
            console.error('Failed to check models:', error);
            this.updateStatus('Failed to connect to API', 'error');
        }
    }

    /**
     * Update model badge
     */
    updateModelBadge(element, name, isLoaded) {
        element.textContent = `${name}: ${isLoaded ? 'Ready' : 'Not Loaded'}`;
        element.className = 'model-badge';
        if (isLoaded) {
            element.classList.add('loaded');
        } else {
            element.classList.add('error');
        }
    }

    /**
     * Update status indicator
     */
    updateStatus(message, type = 'info') {
        const statusText = this.statusIndicator.querySelector('.status-text');
        const statusDot = this.statusIndicator.querySelector('.status-dot');
        
        statusText.textContent = message;
        
        // Update dot color based on type
        statusDot.style.background = {
            'success': 'var(--success)',
            'error': 'var(--danger-color)',
            'warning': 'var(--warning)',
            'info': 'var(--primary-color)'
        }[type] || 'var(--primary-color)';
    }

    /**
     * Start recording audio
     */
    async startRecording() {
        const started = await this.recorder.startRecording();
        if (started) {
            this.recordBtn.classList.add('recording');
            this.recordingIndicator.style.display = 'flex';
            this.updateStatus('Recording...', 'error');
        }
    }

    /**
     * Stop recording and process audio
     */
    async stopRecording() {
        if (!this.recorder.getIsRecording()) return;

        this.recordBtn.classList.remove('recording');
        this.recordingIndicator.style.display = 'none';
        this.updateStatus('Processing...', 'info');

        try {
            const audioBlob = await this.recorder.stopRecording();
            
            if (!audioBlob || audioBlob.size === 0) {
                this.updateStatus('Recording too short', 'warning');
                return;
            }

            await this.processVoiceInput(audioBlob);

        } catch (error) {
            console.error('Recording error:', error);
            this.updateStatus('Recording failed', 'error');
        }
    }

    /**
     * Process voice input
     */
    async processVoiceInput(audioBlob) {
        const language = this.languageSelect.value;
        const difficulty = this.difficultySelect.value;
        const scenario = this.scenarioSelect.value;

        try {
            this.disableInputs();

            // Use the speak endpoint for complete workflow
            const result = await API.speakAndRespond(
                audioBlob,
                language,
                difficulty,
                scenario,
                this.sessionId
            );

            // The transcription is implicit, but we show what the user said
            // by using detected_language if available
            this.addMessage('user', `[You spoke in ${result.detected_language || language}]`);
            this.addMessage('assistant', result.response);

            // Synthesize and play response
            await this.speakText(result.response, language);

            this.updateStatus('Ready', 'success');

        } catch (error) {
            console.error('Voice processing error:', error);
            this.addMessage('system', `Error: ${error.message}`);
            this.updateStatus('Error processing voice', 'error');
        } finally {
            this.enableInputs();
        }
    }

    /**
     * Send text message
     */
    async sendTextMessage() {
        const message = this.textInput.value.trim();
        if (!message) return;

        const language = this.languageSelect.value;
        const difficulty = this.difficultySelect.value;
        const scenario = this.scenarioSelect.value;

        try {
            this.disableInputs();
            this.textInput.value = '';
            this.updateStatus('Thinking...', 'info');

            // Add user message
            this.addMessage('user', message);

            // Send to API
            const result = await API.sendMessage(
                message,
                language,
                difficulty,
                scenario,
                this.messages
            );

            // Add assistant response
            this.addMessage('assistant', result.response);

            // Synthesize and play response
            await this.speakText(result.response, language);

            this.updateStatus('Ready', 'success');

        } catch (error) {
            console.error('Message error:', error);
            this.addMessage('system', `Error: ${error.message}`);
            this.updateStatus('Error sending message', 'error');
        } finally {
            this.enableInputs();
        }
    }

    /**
     * Synthesize and play text as speech
     */
    async speakText(text, language) {
        try {
            const audioBlob = await API.synthesizeSpeech(text, language);
            await this.player.play(audioBlob);
        } catch (error) {
            console.error('Speech synthesis error:', error);
            // Non-critical error, just log it
        }
    }

    /**
     * Add message to conversation history
     */
    addMessage(role, content) {
        // Add to messages array
        if (role !== 'system') {
            this.messages.push({ role, content });
        }

        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const roleLabel = role === 'user' ? 'You' : 
                         role === 'assistant' ? 'Assistant' : 'System';
        
        contentDiv.innerHTML = `<strong>${roleLabel}:</strong> ${this.escapeHtml(content)}`;
        
        messageDiv.appendChild(contentDiv);
        this.conversationHistory.appendChild(messageDiv);

        // Scroll to bottom
        this.conversationHistory.scrollTop = this.conversationHistory.scrollHeight;
    }

    /**
     * Clear conversation history
     */
    async clearHistory() {
        if (!confirm('Clear conversation history?')) return;

        this.messages = [];
        
        // Clear from server
        try {
            await API.clearSession(this.sessionId);
            this.sessionId = this.generateSessionId();
        } catch (error) {
            console.error('Failed to clear session:', error);
        }

        // Clear UI
        this.conversationHistory.innerHTML = `
            <div class="message assistant">
                <div class="message-content">
                    <strong>Assistant:</strong> History cleared! Ready to start a new conversation.
                </div>
            </div>
        `;

        this.updateStatus('History cleared', 'success');
    }

    /**
     * Disable input controls
     */
    disableInputs() {
        this.recordBtn.disabled = true;
        this.sendBtn.disabled = true;
        this.textInput.disabled = true;
    }

    /**
     * Enable input controls
     */
    enableInputs() {
        this.recordBtn.disabled = false;
        this.sendBtn.disabled = false;
        this.textInput.disabled = false;
    }

    /**
     * Generate unique session ID
     */
    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new LanguageLearningApp();
});
