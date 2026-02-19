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
        this.continuousToggle = document.getElementById('continuous-toggle');
        this.speechRateToggle = document.getElementById('speech-rate-toggle');
        this.recordBtnText = this.recordBtn.querySelector('.btn-text');

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
        this.continuousListening = false;
        this.continuousStopTimer = null;
        this.continuousRestartTimer = null;
        this.continuousMaxRecordingMs = 10000;
        this.continuousRestartDelayMs = 400;
        this.continuousSilenceDurationMs = 900;
        this.continuousSilenceThreshold = 0.02;

        // Initialize
        this.init();
    }

    /**
     * Initialize the application
     */
    async init() {
        this.setupEventListeners();
        this.updateRecordButtonText();
        await this.checkModelsStatus();
        this.updateStatus('Ready to practice!', 'success');
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Record button - hold to speak
        this.recordBtn.addEventListener('mousedown', () => {
            if (this.isContinuousModeEnabled()) return;
            this.startRecording();
        });
        this.recordBtn.addEventListener('mouseup', () => {
            if (this.isContinuousModeEnabled()) return;
            this.stopRecording();
        });
        this.recordBtn.addEventListener('mouseleave', () => {
            if (!this.isContinuousModeEnabled() && this.recorder.getIsRecording()) {
                this.stopRecording();
            }
        });
        this.recordBtn.addEventListener('click', () => {
            if (!this.isContinuousModeEnabled()) return;
            this.toggleContinuousListening();
        });

        // Touch events for mobile
        this.recordBtn.addEventListener('touchstart', (e) => {
            e.preventDefault();
            if (this.isContinuousModeEnabled()) return;
            this.startRecording();
        });
        this.recordBtn.addEventListener('touchend', (e) => {
            e.preventDefault();
            if (this.isContinuousModeEnabled()) return;
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

        if (this.continuousToggle) {
            this.continuousToggle.addEventListener('change', () => this.handleContinuousToggle());
        }
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
     * Check if continuous listening mode is enabled
     */
    isContinuousModeEnabled() {
        return !!this.continuousToggle && this.continuousToggle.checked;
    }

    /**
     * Handle changes to continuous listening toggle
     */
    handleContinuousToggle() {
        if (!this.isContinuousModeEnabled()) {
            this.continuousListening = false;
            this.clearContinuousTimers();
            this.updateRecordButtonText();
            if (this.recorder.getIsRecording()) {
                this.stopRecording();
            }
            this.updateStatus('Ready', 'success');
            return;
        }

        this.continuousListening = true;
        this.updateRecordButtonText();
        this.updateStatus('Listening...', 'info');
        this.startRecording(true);
    }

    /**
     * Toggle continuous listening on/off
     */
    toggleContinuousListening() {
        if (this.continuousListening) {
            this.continuousListening = false;
            this.updateRecordButtonText();
            if (this.recorder.getIsRecording()) {
                this.stopRecording();
            } else {
                this.updateStatus('Continuous listening stopped', 'info');
            }
            return;
        }

        this.continuousListening = true;
        this.updateRecordButtonText();
        this.updateStatus('Listening...', 'info');
        this.startRecording(true);
    }

    /**
     * Update record button label based on current mode
     */
    updateRecordButtonText() {
        if (!this.recordBtnText) return;

        if (this.isContinuousModeEnabled()) {
            this.recordBtnText.textContent = this.continuousListening ? 'Stop Listening' : 'Start Listening';
            this.recordBtn.title = this.continuousListening ? 'Stop listening' : 'Start listening';
        } else {
            this.recordBtnText.textContent = 'Hold to Speak';
            this.recordBtn.title = 'Hold to record';
        }
    }

    /**
     * Schedule auto-stop for continuous listening chunk
     */
    scheduleContinuousStop() {
        this.clearContinuousTimers();
        this.continuousStopTimer = setTimeout(() => {
            if (this.recorder.getIsRecording()) {
                this.stopRecording();
            }
        }, this.continuousMaxRecordingMs);
    }

    /**
     * Clear continuous listening timers
     */
    clearContinuousTimers() {
        if (this.continuousStopTimer) {
            clearTimeout(this.continuousStopTimer);
            this.continuousStopTimer = null;
        }
        if (this.continuousRestartTimer) {
            clearTimeout(this.continuousRestartTimer);
            this.continuousRestartTimer = null;
        }
    }

    /**
     * Resume continuous listening after processing
     */
    maybeResumeContinuousListening() {
        if (!this.isContinuousModeEnabled() || !this.continuousListening) return;
        if (this.recorder.getIsRecording()) return;

        this.continuousRestartTimer = setTimeout(() => {
            if (this.isContinuousModeEnabled() && this.continuousListening) {
                this.startRecording(true);
            }
        }, this.continuousRestartDelayMs);
    }

    /**
     * Determine speech rate for TTS
     */
    getSpeechRate() {
        if (!this.speechRateToggle) return 1.0;
        return this.speechRateToggle.checked ? 1.2 : 1.0;
    }

    /**
     * Start recording audio
     */
    async startRecording(fromContinuous = false) {
        if (this.recorder.getIsRecording()) return;

        if (this.player.getIsPlaying()) {
            this.player.stop();
        }

        const started = await this.recorder.startRecording({
            enableSilenceDetection: fromContinuous,
            silenceDurationMs: this.continuousSilenceDurationMs,
            silenceThreshold: this.continuousSilenceThreshold,
            onSilence: () => {
                if (this.continuousListening) {
                    this.stopRecording();
                }
            }
        });
        if (started) {
            this.recordBtn.classList.add('recording');
            this.recordingIndicator.style.display = 'flex';
            this.updateStatus('Recording...', 'error');
            if (fromContinuous) {
                this.scheduleContinuousStop();
            }
        }
    }

    /**
     * Stop recording and process audio
     */
    async stopRecording() {
        if (!this.recorder.getIsRecording()) return;

        this.clearContinuousTimers();
        this.recordBtn.classList.remove('recording');
        this.recordingIndicator.style.display = 'none';
        this.updateStatus('Processing...', 'info');

        try {
            const audioBlob = await this.recorder.stopRecording();
            
            if (!audioBlob || audioBlob.size === 0) {
                this.updateStatus('Recording too short', 'warning');
                this.maybeResumeContinuousListening();
                return;
            }

            await this.processVoiceInput(audioBlob);

        } catch (error) {
            console.error('Recording error:', error);
            this.updateStatus('Recording failed', 'error');
            this.maybeResumeContinuousListening();
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

            let userMessageDiv = null;
            let assistantMessageDiv = null;
            let assistantContentDiv = null;
            let fullResponse = '';
            let transcribedText = '';

            // Use streaming endpoint for real-time response
            await API.speakAndRespondStream(
                audioBlob,
                language,
                difficulty,
                scenario,
                this.sessionId,
                {
                    onTranscription: (data) => {
                        // Display transcribed user message
                        transcribedText = data.text;
                        this.updateStatus(`You said: "${data.text}"`, 'info');
                        userMessageDiv = this.addMessageElement('user', data.text);
                    },
                    onResponseStart: () => {
                        this.updateStatus('Assistant is responding...', 'info');
                        // Create assistant message element that we'll update
                        assistantMessageDiv = this.createMessageElement('assistant', '');
                        assistantContentDiv = assistantMessageDiv.querySelector('.message-content');
                        this.conversationHistory.appendChild(assistantMessageDiv);
                    },
                    onResponseChunk: (chunk) => {
                        // Update assistant message with new chunk
                        fullResponse += chunk;
                        assistantContentDiv.innerHTML = `<strong>Assistant:</strong> ${this.escapeHtml(fullResponse)}`;
                        // Auto-scroll to bottom
                        this.conversationHistory.scrollTop = this.conversationHistory.scrollHeight;
                    },
                    onComplete: async (data) => {
                        // Update conversation history
                        if (transcribedText) {
                            this.messages.push({ role: 'user', content: transcribedText });
                        }
                        this.messages.push({ role: 'assistant', content: data.full_response });

                        // Synthesize and play response
                        this.updateStatus('Speaking response...', 'info');
                        await this.speakText(data.full_response, language);

                        this.updateStatus('Ready', 'success');
                    },
                    onError: (error) => {
                        console.error('Streaming error:', error);
                        this.addMessage('system', `Error: ${error}`);
                        this.updateStatus('Error in conversation', 'error');
                    }
                }
            );

        } catch (error) {
            console.error('Voice processing error:', error);
            this.addMessage('system', `Error: ${error.message}`);
            this.updateStatus('Error processing voice', 'error');
        } finally {
            this.enableInputs();
            this.maybeResumeContinuousListening();
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

            let assistantMessageDiv = null;
            let assistantContentDiv = null;
            let fullResponse = '';

            // Use streaming for text messages too
            await API.sendMessageStream(
                message,
                language,
                difficulty,
                scenario,
                this.messages,
                {
                    onStart: () => {
                        // Create assistant message element that we'll update
                        assistantMessageDiv = this.createMessageElement('assistant', '');
                        assistantContentDiv = assistantMessageDiv.querySelector('.message-content');
                        this.conversationHistory.appendChild(assistantMessageDiv);
                    },
                    onChunk: (chunk) => {
                        // Update assistant message with new chunk
                        fullResponse += chunk;
                        assistantContentDiv.innerHTML = `<strong>Assistant:</strong> ${this.escapeHtml(fullResponse)}`;
                        // Auto-scroll to bottom
                        this.conversationHistory.scrollTop = this.conversationHistory.scrollHeight;
                    },
                    onComplete: async (data) => {
                        // Update conversation history
                        this.messages.push({ role: 'assistant', content: data.full_response });

                        // Synthesize and play response
                        this.updateStatus('Speaking response...', 'info');
                        await this.speakText(data.full_response, language);

                        this.updateStatus('Ready', 'success');
                    },
                    onError: (error) => {
                        console.error('Streaming error:', error);
                        this.addMessage('system', `Error: ${error}`);
                        this.updateStatus('Error in conversation', 'error');
                    }
                }
            );

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
            const speechRate = this.getSpeechRate();
            const audioBlob = await API.synthesizeSpeech(text, language, null, speechRate);
            await this.player.play(audioBlob);
        } catch (error) {
            console.error('Speech synthesis error:', error);
            // Non-critical error, just log it
        }
    }

    /**
     * Create a message element without adding to messages array
     */
    createMessageElement(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const roleLabel = role === 'user' ? 'You' : 
                         role === 'assistant' ? 'Assistant' : 'System';
        
        contentDiv.innerHTML = `<strong>${roleLabel}:</strong> ${this.escapeHtml(content)}`;
        
        messageDiv.appendChild(contentDiv);
        return messageDiv;
    }

    /**
     * Add message element to conversation history
     */
    addMessageElement(role, content) {
        const messageDiv = this.createMessageElement(role, content);
        this.conversationHistory.appendChild(messageDiv);

        // Scroll to bottom
        this.conversationHistory.scrollTop = this.conversationHistory.scrollHeight;
        
        return messageDiv;
    }

    /**
     * Add message to conversation history
     */
    addMessage(role, content) {
        // Add to messages array
        if (role !== 'system') {
            this.messages.push({ role, content });
        }

        // Create and add message element
        this.addMessageElement(role, content);
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
