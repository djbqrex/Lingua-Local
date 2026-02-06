/**
 * Audio recording and playback module
 */

export class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
        this.isRecording = false;
    }

    /**
     * Initialize audio recording
     */
    async initialize() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    channelCount: 1,
                    sampleRate: 16000,
                    echoCancellation: true,
                    noiseSuppression: true
                } 
            });
            return true;
        } catch (error) {
            console.error('Failed to initialize audio:', error);
            alert('Microphone access denied. Please allow microphone access to use voice input.');
            return false;
        }
    }

    /**
     * Start recording
     */
    async startRecording() {
        if (!this.stream) {
            const initialized = await this.initialize();
            if (!initialized) return false;
        }

        this.audioChunks = [];
        
        try {
            // Use webm format with opus codec for better browser support
            const options = { mimeType: 'audio/webm;codecs=opus' };
            
            // Fallback to other formats if webm is not supported
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                options.mimeType = 'audio/webm';
                if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                    options.mimeType = 'audio/ogg;codecs=opus';
                    if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                        options.mimeType = ''; // Use default
                    }
                }
            }

            this.mediaRecorder = new MediaRecorder(this.stream, options);

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            return true;
        } catch (error) {
            console.error('Failed to start recording:', error);
            return false;
        }
    }

    /**
     * Stop recording and return audio blob
     */
    async stopRecording() {
        if (!this.mediaRecorder || !this.isRecording) {
            return null;
        }

        return new Promise((resolve) => {
            this.mediaRecorder.onstop = () => {
                const blob = new Blob(this.audioChunks, { type: 'audio/webm' });
                this.isRecording = false;
                resolve(blob);
            };

            this.mediaRecorder.stop();
        });
    }

    /**
     * Get recording state
     */
    getIsRecording() {
        return this.isRecording;
    }

    /**
     * Clean up resources
     */
    cleanup() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
    }
}

export class AudioPlayer {
    constructor(audioElement) {
        this.audioElement = audioElement;
        this.isPlaying = false;
    }

    /**
     * Play audio from blob
     */
    async play(audioBlob) {
        return new Promise((resolve, reject) => {
            const url = URL.createObjectURL(audioBlob);
            this.audioElement.src = url;
            
            this.audioElement.onended = () => {
                URL.revokeObjectURL(url);
                this.isPlaying = false;
                resolve();
            };

            this.audioElement.onerror = (error) => {
                URL.revokeObjectURL(url);
                this.isPlaying = false;
                reject(error);
            };

            this.audioElement.play()
                .then(() => {
                    this.isPlaying = true;
                })
                .catch(reject);
        });
    }

    /**
     * Stop current playback
     */
    stop() {
        this.audioElement.pause();
        this.audioElement.currentTime = 0;
        this.isPlaying = false;
    }

    /**
     * Get playing state
     */
    getIsPlaying() {
        return this.isPlaying;
    }
}
