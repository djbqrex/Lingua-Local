/**
 * API communication module
 */

const API_BASE = '/api';

export class API {
    /**
     * Check API health
     */
    static async checkHealth() {
        const response = await fetch(`${API_BASE}/health`);
        return await response.json();
    }

    /**
     * Check model status
     */
    static async checkModels() {
        const response = await fetch(`${API_BASE}/health/models`);
        return await response.json();
    }

    /**
     * Get supported languages
     */
    static async getLanguages() {
        const response = await fetch(`${API_BASE}/health/languages`);
        return await response.json();
    }

    /**
     * Get available scenarios
     */
    static async getScenarios() {
        const response = await fetch(`${API_BASE}/health/scenarios`);
        return await response.json();
    }

    /**
     * Send text message and get response
     */
    static async sendMessage(
        message,
        language,
        difficulty,
        scenario,
        teachingIntensity = 'standard',
        history = []
    ) {
        const response = await fetch(`${API_BASE}/conversation/text`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message,
                language,
                difficulty,
                scenario,
                teaching_intensity: teachingIntensity,
                history
            })
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        return await response.json();
    }

    /**
     * Send text message and get streaming response
     * @param {string} message - Text message
     * @param {string} language - Target language
     * @param {string} difficulty - Difficulty level
     * @param {string} scenario - Conversation scenario
     * @param {string} teachingIntensity - Teaching intensity
     * @param {Array} history - Conversation history
     * @param {Object} callbacks - Event callbacks
     * @param {Function} callbacks.onStart - Called when response starts
     * @param {Function} callbacks.onChunk - Called for each response chunk
     * @param {Function} callbacks.onComplete - Called with full response
     * @param {Function} callbacks.onError - Called on error
     */
    static async sendMessageStream(
        message,
        language,
        difficulty,
        scenario,
        teachingIntensity = 'standard',
        history = [],
        callbacks = {}
    ) {
        const response = await fetch(`${API_BASE}/conversation/text-stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message,
                language,
                difficulty,
                scenario,
                teaching_intensity: teachingIntensity,
                history
            })
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        // Process Server-Sent Events
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const dataStr = line.substring(6);
                    try {
                        const data = JSON.parse(dataStr);
                        
                        if (data.status === 'generating') {
                            if (callbacks.onStart) {
                                callbacks.onStart();
                            }
                        } else if (data.chunk) {
                            if (callbacks.onChunk) {
                                callbacks.onChunk(data.chunk);
                            }
                        } else if (data.full_response) {
                            if (callbacks.onComplete) {
                                callbacks.onComplete(data);
                            }
                        } else if (data.error) {
                            if (callbacks.onError) {
                                callbacks.onError(data.error);
                            }
                        }
                    } catch (e) {
                        console.error('Failed to parse SSE data:', e, dataStr);
                    }
                }
            }
        }
    }

    /**
     * Transcribe audio to text
     */
    static async transcribeAudio(audioBlob, language = null) {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        if (language) {
            formData.append('language', language);
        }

        const response = await fetch(`${API_BASE}/conversation/transcribe`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Transcription error: ${response.statusText}`);
        }

        return await response.json();
    }

    /**
     * Synthesize speech from text
     */
    static async synthesizeSpeech(
        text,
        language,
        voice = null,
        speechRate = null,
        voiceStyle = 'female',
        explanationLanguage = 'en',
        difficulty = 'beginner',
        teachingIntensity = 'standard',
        explanationVoice = null
    ) {
        const formData = new FormData();
        formData.append('text', text);
        formData.append('language', language);
        if (voice) {
            formData.append('voice', voice);
        }
        if (speechRate !== null && speechRate !== undefined) {
            formData.append('speech_rate', speechRate.toString());
        }
        if (voiceStyle) {
            formData.append('voice_style', voiceStyle);
        }
        if (explanationLanguage) {
            formData.append('explanation_language', explanationLanguage);
        }
        if (difficulty) {
            formData.append('difficulty', difficulty);
        }
        if (teachingIntensity) {
            formData.append('teaching_intensity', teachingIntensity);
        }
        if (explanationVoice) {
            formData.append('explanation_voice', explanationVoice);
        }

        const response = await fetch(`${API_BASE}/conversation/synthesize`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Speech synthesis error: ${response.statusText}`);
        }

        return await response.blob();
    }

    /**
     * Complete conversation: send audio, get text response
     */
    static async speakAndRespond(
        audioBlob,
        language,
        difficulty,
        scenario,
        teachingIntensity = 'standard',
        sessionId = null
    ) {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        formData.append('language', language);
        formData.append('difficulty', difficulty);
        formData.append('scenario', scenario);
        formData.append('teaching_intensity', teachingIntensity);
        if (sessionId) {
            formData.append('session_id', sessionId);
        }

        const response = await fetch(`${API_BASE}/conversation/speak`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Conversation error: ${response.statusText}`);
        }

        return await response.json();
    }

    /**
     * Streaming conversation: send audio, receive streamed response
     * @param {Blob} audioBlob - Audio recording
     * @param {string} language - Target language
     * @param {string} difficulty - Difficulty level
     * @param {string} scenario - Conversation scenario
     * @param {string} teachingIntensity - Teaching intensity
     * @param {string|null} sessionId - Session ID
     * @param {Object} callbacks - Event callbacks
     * @param {Function} callbacks.onTranscription - Called with transcription result
     * @param {Function} callbacks.onResponseStart - Called when response generation starts
     * @param {Function} callbacks.onResponseChunk - Called for each response chunk
     * @param {Function} callbacks.onComplete - Called with full response
     * @param {Function} callbacks.onError - Called on error
     */
    static async speakAndRespondStream(
        audioBlob,
        language,
        difficulty,
        scenario,
        teachingIntensity = 'standard',
        sessionId = null,
        callbacks = {}
    ) {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        formData.append('language', language);
        formData.append('difficulty', difficulty);
        formData.append('scenario', scenario);
        formData.append('teaching_intensity', teachingIntensity);
        if (sessionId) {
            formData.append('session_id', sessionId);
        }

        const response = await fetch(`${API_BASE}/conversation/speak-stream`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Conversation error: ${response.statusText}`);
        }

        // Process Server-Sent Events
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer

            for (const line of lines) {
                if (line.startsWith('event: ')) {
                    const eventType = line.substring(7).trim();
                    continue;
                }
                
                if (line.startsWith('data: ')) {
                    const dataStr = line.substring(6);
                    try {
                        const data = JSON.parse(dataStr);
                        
                        // Determine event type from previous line or current data
                        if (data.status === 'transcribing') {
                            // Start event
                        } else if (data.text && data.language && 'language' in data) {
                            // Transcription event
                            if (callbacks.onTranscription) {
                                callbacks.onTranscription(data);
                            }
                        } else if (data.status === 'generating') {
                            // Response start
                            if (callbacks.onResponseStart) {
                                callbacks.onResponseStart();
                            }
                        } else if (data.chunk) {
                            // Response chunk
                            if (callbacks.onResponseChunk) {
                                callbacks.onResponseChunk(data.chunk);
                            }
                        } else if (data.full_response) {
                            // Complete
                            if (callbacks.onComplete) {
                                callbacks.onComplete(data);
                            }
                        } else if (data.error) {
                            // Error
                            if (callbacks.onError) {
                                callbacks.onError(data.error);
                            }
                        }
                    } catch (e) {
                        console.error('Failed to parse SSE data:', e, dataStr);
                    }
                }
            }
        }
    }

    /**
     * Get session history
     */
    static async getSessionHistory(sessionId) {
        const response = await fetch(`${API_BASE}/conversation/session/${sessionId}`);
        return await response.json();
    }

    /**
     * Clear session history
     */
    static async clearSession(sessionId) {
        const response = await fetch(`${API_BASE}/conversation/session/${sessionId}`, {
            method: 'DELETE'
        });
        return await response.json();
    }

    /**
     * Get available voices
     */
    static async getVoices() {
        const response = await fetch(`${API_BASE}/conversation/voices`);
        return await response.json();
    }
}
