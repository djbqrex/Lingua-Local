/**
 * Audio recording and playback module
 */

export class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
        this.isRecording = false;
        this.audioContext = null;
        this.analyser = null;
        this.silenceCheckRaf = null;
        this.silenceStart = null;
        this.hasSpeech = false;
        this.silenceThreshold = 0.02;
        this.silenceDurationMs = 900;
        this.onSilenceCallback = null;
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
    async startRecording(config = {}) {
        if (!this.stream) {
            const initialized = await this.initialize();
            if (!initialized) return false;
        }

        this.audioChunks = [];
        this.silenceStart = null;
        this.hasSpeech = false;
        this.onSilenceCallback = typeof config.onSilence === 'function' ? config.onSilence : null;
        this.silenceThreshold = config.silenceThreshold ?? this.silenceThreshold;
        this.silenceDurationMs = config.silenceDurationMs ?? this.silenceDurationMs;
        
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
            if (config.enableSilenceDetection) {
                this.startSilenceDetection();
            }
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

        this.stopSilenceDetection();
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
     * Start monitoring audio for silence
     */
    startSilenceDetection() {
        if (!this.stream) return;

        if (!this.audioContext) {
            this.audioContext = new AudioContext();
        }

        if (!this.analyser) {
            const source = this.audioContext.createMediaStreamSource(this.stream);
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 2048;
            source.connect(this.analyser);
        }

        const dataArray = new Uint8Array(this.analyser.fftSize);
        const check = () => {
            if (!this.analyser || !this.isRecording) return;

            this.analyser.getByteTimeDomainData(dataArray);
            let sum = 0;
            for (let i = 0; i < dataArray.length; i += 1) {
                const normalized = (dataArray[i] - 128) / 128;
                sum += normalized * normalized;
            }
            const rms = Math.sqrt(sum / dataArray.length);

            if (rms > this.silenceThreshold) {
                this.hasSpeech = true;
                this.silenceStart = null;
            } else if (this.hasSpeech) {
                if (!this.silenceStart) {
                    this.silenceStart = performance.now();
                } else if (performance.now() - this.silenceStart >= this.silenceDurationMs) {
                    if (this.onSilenceCallback) {
                        this.onSilenceCallback();
                    }
                    this.silenceStart = null;
                }
            }

            this.silenceCheckRaf = requestAnimationFrame(check);
        };

        this.silenceCheckRaf = requestAnimationFrame(check);
    }

    /**
     * Stop silence monitoring
     */
    stopSilenceDetection() {
        if (this.silenceCheckRaf) {
            cancelAnimationFrame(this.silenceCheckRaf);
            this.silenceCheckRaf = null;
        }
        this.silenceStart = null;
        this.hasSpeech = false;
        this.onSilenceCallback = null;
    }

    /**
     * Clean up resources
     */
    cleanup() {
        this.stopSilenceDetection();
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
        this.analyser = null;
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
