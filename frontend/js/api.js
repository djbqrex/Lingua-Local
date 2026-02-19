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
