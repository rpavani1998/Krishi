import { useState, useEffect, useRef } from 'react';
import { Mic, X, Pause, Play, Moon, Sun, RotateCcw, Keyboard, Volume2, Check, ArrowRight, ChevronUp, ChevronDown } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { useVoiceStateMachine, VOICE_STATES } from '../hooks/useVoiceStateMachine';
import OnboardingStatus from './OnboardingStatus';
import ManualOnboardingForm from './ManualOnboardingForm';
import LanguageSelector from './LanguageSelector';
import MobileFrame from './MobileFrame';
import HarvestDecision from './HarvestDecision';

const USE_BACKEND_STT = false;

const nowMs = () => Date.now();

const VoiceOverlay = ({ isOpen, onClose, onResult, darkMode, toggleDarkMode, voiceSettings, mode = 'voice', userProfile }) => {
  const { t, i18n } = useTranslation();
  const { state, transition, getCurrentState } = useVoiceStateMachine(VOICE_STATES.IDLE);
  
  const [onboardingSession, setOnboardingSession] = useState({ profile: userProfile || {} }); // Store onboarding state
  const onboardingSessionRef = useRef(onboardingSession);

  // Keep ref in sync with state
  useEffect(() => {
    console.log("Onboarding Session Updated:", onboardingSession);
    onboardingSessionRef.current = onboardingSession;
  }, [onboardingSession]);
  
  // Update local profile when prop changes
  useEffect(() => {
    // Only update if userProfile has actual data and is not just an empty object
    if (userProfile && Object.keys(userProfile).length > 0) {
        console.log("Syncing userProfile prop to onboardingSession:", userProfile);
        setOnboardingSession(prev => ({ 
            ...prev, 
            profile: { ...prev.profile, ...userProfile } 
        }));
    }
  }, [userProfile]);

  // Stop listening when closed
  useEffect(() => {
    if (!isOpen) {
        console.log("isOpen is false, calling handleClose");
        handleClose();
    }
  }, [isOpen]);

  const [isManualMode, setIsManualMode] = useState(mode === 'manual' || mode === 'onboarding_manual'); // Toggle manual entry
  
  // Update manual mode when prop changes (e.g. from Welcome screen)
  useEffect(() => {
    if (mode === 'manual' || mode === 'onboarding_manual') {
        setIsManualMode(true);
    } else {
        setIsManualMode(false);
    }
  }, [mode]);

  const [messages, setMessages] = useState([]);
  const [transcript, setTranscript] = useState(''); // Real-time transcript
  const [savedStateBeforePause, setSavedStateBeforePause] = useState(null); // Save state for pause/resume
  const [textInputValue, setTextInputValue] = useState(''); // Text input value
  const [errorMessage, setErrorMessage] = useState(null); // Error message display
  const [isSoundDetected, setIsSoundDetected] = useState(false); // Visual feedback for mic input
  const messagesEndRef = useRef(null);
  const messagesRef = useRef([]);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  // Auto-start onboarding conversation with welcome message - HANDLED IN INIT EFFECT

  
  const transcriptRef = useRef('');
  const accumulatedTranscriptRef = useRef(''); // Accumulate text across sessions
  const currentResponseTextRef = useRef(''); // To store current AI response for echo cancellation
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null);
  const silenceTimerRef = useRef(null);
  const commitTimerRef = useRef(null); // Ref for commit timer to allow global clearing
  const SILENCE_TIMEOUT = 8000; // Increased to 8s for better user experience
  const autoRestartTimerRef = useRef(null); 
  const audioRef = useRef(null);
  const isMounted = useRef(true);
  const abortControllerRef = useRef(null); // For cancelling fetch requests
  const recordingLanguageRef = useRef(i18n.language); // Track language at start of recording
  const shouldListenRef = useRef(false); // Track if we intend to listen (for auto-restart logic)
  const [visualizerData, setVisualizerData] = useState(new Array(5).fill(10));
  const [sheetMode, setSheetMode] = useState('normal'); // 'minimized', 'normal', 'expanded'

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      console.log("VoiceOverlay unmounting. Cleaning up...");
      isMounted.current = false;
      
      // 1. Abort any ongoing fetch requests
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        console.log("Cleanup: Aborted ongoing fetch request.");
      } else {
        console.log("Cleanup: No active fetch request to abort.");
      }

      // 2. Stop any TTS audio
      if ('speechSynthesis' in window) {
        console.log("Cleanup: Cancelling browser TTS.");
        window.speechSynthesis.cancel();
      }
      if (audioRef.current) {
        console.log("Cleanup: Pausing and nullifying audio element.");
        audioRef.current.pause();
        audioRef.current.src = ""; // Detach source
        audioRef.current = null;
      } else {
        console.log("Cleanup: No active audio element to stop.");
      }

      // 3. Stop any recognition services
      console.log("Cleanup: Stopping recognition services.");
      stopListening(true); // Pass true to indicate a final stop

      // 4. Clear all timers
      console.log("Cleanup: Clearing all timers.");
      clearTimeout(silenceTimerRef.current);
      clearTimeout(commitTimerRef.current);
      clearTimeout(autoRestartTimerRef.current);
      console.log("Cleanup complete.");
    };
  }, []);

  const handleClose = () => {
    console.log("handleClose called. Initiating cleanup...");
    
    // 1. Abort any ongoing fetch requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      console.log("handleClose: Aborted fetch request.");
    }

    // 2. Stop any TTS audio
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = "";
      audioRef.current = null;
    }
    console.log("handleClose: Stopped TTS audio.");

    // 3. Stop any recognition services
    stopListening(true);

    // 4. Clear all timers
    clearTimeout(silenceTimerRef.current);
    clearTimeout(commitTimerRef.current);
    clearTimeout(autoRestartTimerRef.current);
    console.log("handleClose: Cleared all timers.");

    // 5. Call the parent onClose handler
    onClose();
  };

  const getSheetHeightClass = () => {
      switch(sheetMode) {
          case 'minimized': return 'h-[280px]';
          case 'expanded': return 'h-[90%]';
          case 'normal': default: return 'h-[90%]';
      }
  };
  
  // Use backend STT (Whisper) for local setup reliability
  // Default to FALSE for faster response/transcription (Web Speech API)
  // BUT: Default to TRUE for Indian languages (te, hi) as Web Speech API is often unreliable for them
  const [isBackendSTTActive, setIsBackendSTTActive] = useState(
      i18n.language.startsWith('te') || i18n.language.startsWith('hi')
  );
  const isBackendSTTActiveRef = useRef(isBackendSTTActive);

  useEffect(() => {
      isBackendSTTActiveRef.current = isBackendSTTActive;
  }, [isBackendSTTActive]);

  // Force backend STT for regional languages when language changes
  useEffect(() => {
      if (i18n.language.startsWith('te') || i18n.language.startsWith('hi')) {
          if (!isBackendSTTActive) setIsBackendSTTActive(true);
      }
  }, [i18n.language]);

  // Helper to check if transcript is a status message
  const isStatusMessage = (text) => {
      if (!text) return false;
      const statusKeywords = [
          'Listening', 
          'Processing', 
          'Error:', 
          'No speech', 
          'Ready', 
          'Tap mic',
          'Microphone',
          'Speech recognition'
      ];
      return statusKeywords.some(keyword => text.startsWith(keyword));
  };

  // Derived state flags for backward compatibility
  const isListening = state === VOICE_STATES.LISTENING;
  const isProcessing = state === VOICE_STATES.PROCESSING || state === VOICE_STATES.THINKING;
  const isPlaying = state === VOICE_STATES.SPEAKING;
  const isPaused = state === VOICE_STATES.PAUSED;

  useEffect(() => {
    transcriptRef.current = transcript;
  }, [transcript]);

  // Sync real-time transcript to text input for visibility
  useEffect(() => {
    if (isListening) {
        // Always sync transcript to input if it's not a status message
        // This ensures the user sees exactly what is being heard in the input field
        if (transcript && !isStatusMessage(transcript)) {
            setTextInputValue(transcript);
        } else if (!transcript) {
             // Clear input when starting fresh listening session (if transcript is empty)
             setTextInputValue('');
        }
    }
  }, [transcript, isListening]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, transcript, state]);

  // Ensure voices are loaded for browser TTS
  useEffect(() => {
    const loadVoices = () => {
        if ('speechSynthesis' in window) {
            const voices = window.speechSynthesis.getVoices();
            if (voices.length > 0) {
                console.log("Browser voices loaded:", voices.length);
            }
        }
    };
    loadVoices();
    if ('speechSynthesis' in window && window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  }, []);

  // --- TTS Helper ---
  const speakBrowserTTS = (text, onComplete) => {
      if (!('speechSynthesis' in window)) {
          console.error("Browser TTS not supported");
          onComplete?.();
          return;
      }

      // Clean text for TTS (remove markdown asterisks, hashes, underscores, code blocks)
      const cleanText = text
          .replace(/\*/g, '')
          .replace(/#/g, '')
          .replace(/_/g, '')
          .replace(/`/g, '')
          .replace(/\[(.*?)\]\(.*?\)/g, '$1'); // Remove links [text](url) -> text

      console.log("Starting Browser TTS:", cleanText);

      // Cancel any ongoing speech
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(cleanText);
      let isCompleted = false;

      const safeComplete = () => {
          if (!isCompleted) {
              isCompleted = true;
              console.log("Browser TTS safeComplete called");
              onComplete?.();
          }
      };
      
      // Select Voice (Prioritize Indian English/Regional)
      const voices = window.speechSynthesis.getVoices();
      let selectedVoice = null;
      const langCode = i18n.language === 'te' ? 'te-IN' : (i18n.language === 'hi' ? 'hi-IN' : 'en-IN');
      
      // Try to find a suitable voice
      if (voices.length > 0) {
          selectedVoice = voices.find(v => v.lang === langCode) || 
                          voices.find(v => v.lang.startsWith(langCode.split('-')[0])) ||
                          voices.find(v => v.lang === 'en-IN') ||
                          voices.find(v => v.name.includes('India') || v.name.includes('Google'));
      }

      if (selectedVoice) {
          utterance.voice = selectedVoice;
          console.log("Using browser voice:", selectedVoice.name);
      } else {
          console.warn("No specific voice found, using default");
      }

      utterance.lang = langCode;
      utterance.rate = voiceSettings?.speed || 0.9;
      utterance.volume = voiceSettings?.volume || 1.0;

      utterance.onend = () => {
          console.log("Browser TTS finished (onend)");
          safeComplete();
      };

      utterance.onerror = (e) => {
          console.error("Browser TTS error:", e);
          safeComplete(); // Fail gracefully
      };

      try {
          window.speechSynthesis.speak(utterance);
          
          // Fallback: If onend doesn't fire (some Android/Chrome bugs), force complete after estimated time
          const estimatedDuration = (text.length / 10) * 1000; // rough estimate
          setTimeout(() => {
              if (window.speechSynthesis.speaking) {
                  // still speaking, do nothing? Or force stop?
                  // Let's force stop if it's taking way too long (2x estimate)
              } else {
                  // Not speaking, but maybe onend didn't fire?
                  console.warn("Browser TTS fallback timer fired (not speaking)");
                  safeComplete();
              }
          }, estimatedDuration + 2000);
          
          // Absolute timeout safety net
          setTimeout(() => {
               if (!isCompleted) {
                   console.warn("Browser TTS absolute timeout");
                   window.speechSynthesis.cancel();
                   safeComplete();
               }
          }, Math.max(10000, estimatedDuration * 3));

      } catch (e) {
          console.error("speechSynthesis.speak failed:", e);
          safeComplete();
      }
  };

  // Helper to restart listening safely
  const restartListening = () => {
    if (!isMounted.current) return;
    const currentState = getCurrentState();
    if (currentState === VOICE_STATES.PAUSED || currentState === VOICE_STATES.PROCESSING || currentState === VOICE_STATES.SPEAKING) {
        return;
    }
    console.log("Forcing restart of listening session...");
    stopListening();
    setTimeout(() => {
        if (isMounted.current) startListening();
    }, 100);
  };

  // Watchdog timer to ensure listening is active when it should be
  useEffect(() => {
      const interval = setInterval(() => {
          if (!isMounted.current || !isOpen) return;
          
          const currentState = getCurrentState();
          // If we think we should be listening (red dot pulsing) but no recognition is active
          if (currentState === VOICE_STATES.LISTENING && shouldListenRef.current) {
              // Check if recognition is actually running? 
              // Hard to check directly, but we can check if it's been too long since last start without result?
              // For now, let's just rely on the fact that if we are in LISTENING state, we expect events.
          }
          
          // If we are in IDLE state but isOpen is true and we are not processing/speaking/paused
          if (currentState === VOICE_STATES.IDLE && mode !== 'manual') {
               console.log("Watchdog: State is IDLE but should be active. Restarting...");
               restartListening();
          }
      }, 5000);
      return () => clearInterval(interval);
  }, [isOpen, state, mode]);

  // Visualizer Animation Loop
  useEffect(() => {
    let interval;
    if ((isListening || isPlaying) && !isPaused) {
        interval = setInterval(() => {
            // Higher amplitude if sound is actually detected or AI is speaking
            const isActive = isSoundDetected || isPlaying;
            const base = isActive ? 15 : 5;
            const range = isActive ? 35 : 10;
            setVisualizerData(prev => prev.map(() => Math.random() * range + base));
        }, 100);
    }
    return () => clearInterval(interval);
  }, [isListening, isPlaying, isPaused, isSoundDetected]);

  const togglePause = () => {
    const currentState = getCurrentState();
    
    if (currentState === VOICE_STATES.PAUSED) {
        // Resume - Requirement 2.7: Restore previous state and continue
        console.log("Resuming from pause, restoring state:", savedStateBeforePause);
        
        // Restore audio if it was playing
        if (audioRef.current && audioRef.current.paused && savedStateBeforePause?.wasPlaying) {
            transition(VOICE_STATES.SPEAKING);
            audioRef.current.play().catch(err => {
                console.error("Error resuming audio:", err);
                // If audio can't resume, just start listening
                transition(VOICE_STATES.LISTENING);
                startListening();
            });
        } else {
            // Otherwise start listening
            transition(VOICE_STATES.LISTENING);
            startListening();
        }
        
        // Clear saved state
        setSavedStateBeforePause(null);
    } else {
        // Pause - Requirement 2.7: Stop all listening and playback, save state
        console.log("Pausing, saving current state:", currentState);
        
        // Save current state
        const stateToSave = {
            previousState: currentState,
            wasPlaying: audioRef.current && !audioRef.current.paused,
            audioTime: audioRef.current ? audioRef.current.currentTime : 0,
            transcript: transcript
        };
        setSavedStateBeforePause(stateToSave);
        
        // Stop listening
        stopListening();
        
        // Pause audio if playing
        if (audioRef.current && !audioRef.current.paused) {
            audioRef.current.pause();
        }
        
        // Transition to paused state
        transition(VOICE_STATES.PAUSED);
    }
  };

  const handleInterrupt = () => {
    console.log("Interrupted by user");
    
    // Stop Audio Element
    if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
    }
    
    // Stop Browser TTS
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
    }
    
    // Transition to Listening immediately
    transition(VOICE_STATES.LISTENING);
    
    // Start Listening
    startListening();
  };

  async function playResponse(text, options = {}) {
    console.log("playResponse called with:", text, options);
    if (!isMounted.current) {
        console.log("playResponse aborted: Component not mounted");
        return;
    }

    // Stop listening immediately to prevent echo/self-capture (Requirement 3)
    stopListening();

    // If no text, just ensure we are listening and return
    if (!text) {
        console.log("playResponse aborted: No text provided");
        const currentState = getCurrentState();
        if (currentState === VOICE_STATES.IDLE) {
            transition(VOICE_STATES.LISTENING);
            startListening();
        }
        return;
    }
    
    // Stop any currently playing audio
    if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
        audioRef.current = null;
    }

    // Transition to SPEAKING state (guard invalid transitions)
    // Direct transition is now allowed via updated state machine
    transition(VOICE_STATES.SPEAKING);
    currentResponseTextRef.current = text;

    return new Promise((resolve) => {
        // --- Helper for completion ---
        const handlePlaybackComplete = () => {
             console.log("Playback complete (handlePlaybackComplete)");
             if (isMounted.current) {
                 const currentState = getCurrentState();
                 // Only transition to LISTENING if we are still in SPEAKING state (not PAUSED or ERROR)
                 if (currentState === VOICE_STATES.SPEAKING) {
                     console.log("Transitioning from SPEAKING to LISTENING");
                     transition(VOICE_STATES.LISTENING);
                     startListening();
                 } else {
                     console.log("Skipping transition to LISTENING because state is:", currentState);
                 }
                 resolve();
             }
        };

        const play = async () => {
            // Abort if unmounted OR if user interrupted (switched to LISTENING or PAUSED)
            const currentState = getCurrentState();
            if (!isMounted.current || currentState === VOICE_STATES.LISTENING || currentState === VOICE_STATES.PAUSED) { 
                console.log("Audio playback aborted: User interrupted or component unmounted");
                resolve(); 
                return; 
            }
            
            // 1. Force Browser TTS (Fast path for greeting)
        if (options.forceBrowserTTS) {
             console.log("Forcing Browser TTS...");
             
             // Add a small delay to ensure state transitions complete
             setTimeout(() => {
                 speakBrowserTTS(text, handlePlaybackComplete);
             }, 100);
             return;
        }

            // 2. Try Backend TTS
            try {
                console.log("Requesting TTS from backend...");
                abortControllerRef.current = new AbortController();
                const response = await axios.post('/api/v1/voice/speak', { 
                    text: text,
                    language: i18n.language 
                }, {
                    responseType: 'blob',
                    signal: abortControllerRef.current.signal
                });
                console.log("TTS audio blob received, size:", response.data.size);
                
                if (response.data.size === 0) {
                    throw new Error("Empty audio blob received from backend");
                }

                // Abort if unmounted OR if user interrupted
                const stateAfterFetch = getCurrentState();
                if (!isMounted.current || stateAfterFetch === VOICE_STATES.LISTENING || stateAfterFetch === VOICE_STATES.PAUSED) { 
                    console.log("Audio playback aborted: User interrupted or component unmounted");
                    resolve(); 
                    return; 
                }

                // Stop again just in case another request finished first
                if (audioRef.current) {
                    try { audioRef.current.pause(); } catch { /* ignore */ }
                    audioRef.current = null;
                }

                const audioUrl = URL.createObjectURL(response.data);
                const audio = new Audio(audioUrl);
                
                // Apply Voice Settings (Frontend)
                if (voiceSettings) {
                    if (voiceSettings.volume !== undefined) audio.volume = voiceSettings.volume;
                    if (voiceSettings.speed !== undefined) audio.playbackRate = voiceSettings.speed;
                }

                audioRef.current = audio;
                
                audio.onended = () => {
                    console.log("Backend Audio playback finished");
                    if (!isMounted.current) return;
                    if (audioRef.current === audio) {
                         currentResponseTextRef.current = ''; // Clear text
                         handlePlaybackComplete();
                    } else {
                        resolve();
                    }
                };
                
                try {
                    console.log("Attempting to play backend audio...");
                    await audio.play();
                    console.log("Backend Audio playback started");
                } catch (err) {
                    console.error("Audio play failed (Autoplay blocked?):", err);
                    throw err; // Trigger fallback
                }
            } catch (error) {
                console.error("TTS Error (Backend):", error);
                
                // Fallback to browser SpeechSynthesis
                console.log("Attempting fallback to browser SpeechSynthesis...");
                speakBrowserTTS(text, handlePlaybackComplete);
            }
        };
        play();
    });
  }

  function stopListening() {
    shouldListenRef.current = false; // Signal intent to stop
    // Stop Web Speech API
    if (recognitionRef.current) {
      try {
          recognitionRef.current.stop();
      } catch { void 0; }
    }
    
    // Stop MediaRecorder (Backend STT)
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        try {
            console.log("Stopping MediaRecorder...");
            mediaRecorderRef.current.stop();
        } catch (e) {
            console.error("Error stopping MediaRecorder:", e);
        }
    }

    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    if (autoRestartTimerRef.current) {
      clearTimeout(autoRestartTimerRef.current);
      autoRestartTimerRef.current = null;
    }
    if (commitTimerRef.current) {
      clearTimeout(commitTimerRef.current);
      commitTimerRef.current = null;
    }
  }

  async function startListening() {
    if (!isMounted.current) return;
    
    shouldListenRef.current = true; // Signal intent to listen
    
    const currentState = getCurrentState();
    if (currentState === VOICE_STATES.PAUSED) return;
    
    // Don't start if Processing or Thinking or Speaking
    if (currentState === VOICE_STATES.PROCESSING || currentState === VOICE_STATES.THINKING || currentState === VOICE_STATES.SPEAKING) {
        console.log("Cannot start listening - System busy:", currentState);
        return;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        console.log("Already recording");
        return;
    }

    // Use Ref to avoid stale closures in timeouts/callbacks
    if (isBackendSTTActiveRef.current) {
        // --- Backend STT (Whisper) Implementation ---
        try {
            console.log("Starting listening (Backend STT)...");
            recordingLanguageRef.current = i18n.language; // Capture current language
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Setup MediaRecorder
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                if (!isMounted.current) return;
                
                const audioBlob = new Blob(audioChunksRef.current, { type: mediaRecorder.mimeType || 'audio/webm' });
                if (audioBlob.size < 1000) {
                    console.log("Audio blob too small, ignoring");
                    return; 
                }
                
                console.log("Audio recorded, sending to backend...", audioBlob.size);
                await handleSendAudio(audioBlob);
                
                // Stop tracks
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start();
            if (getCurrentState() !== VOICE_STATES.LISTENING) {
                transition(VOICE_STATES.LISTENING);
            }
            setIsSoundDetected(false); // Will be updated by AudioContext
            setTranscript(t('listening') || "Listening...");

            // Setup AudioContext for Silence Detection
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = audioContext.createMediaStreamSource(stream);
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 256;
            source.connect(analyser);
            
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            
            // Silence detection loop
            let silenceStart = nowMs();
            let speechStarted = false;
            let recordingStart = nowMs();
            const MAX_RECORDING_DURATION = 10000; // 10 seconds max

            const checkSilence = () => {
                if (!isMounted.current || mediaRecorder.state === 'inactive') {
                    audioContext.close();
                    return;
                }

                // Check Max Duration
                if (nowMs() - recordingStart > MAX_RECORDING_DURATION) {
                    console.log("Max recording duration reached, stopping...");
                    stopListening();
                    return;
                }

                analyser.getByteFrequencyData(dataArray);
                
                // Calculate average volume
                let sum = 0;
                for(let i = 0; i < bufferLength; i++) {
                    sum += dataArray[i];
                }
                const average = sum / bufferLength;

                // Thresholds - Lowered to 20 to be more sensitive to soft speech
                const NOISE_THRESHOLD = 20; 
                
                if (average > NOISE_THRESHOLD) {
                    // Sound detected
                    silenceStart = nowMs();
                    if (!speechStarted) {
                        console.log("Speech started");
                        speechStarted = true;
                        setIsSoundDetected(true);
                        setTranscript(t('listening_speech_detected') || "Listening... (Speech Detected)");
                    }
                    // Visualizer update
                    setVisualizerData(prev => prev.map(() => Math.random() * 45 + 20));
                } else {
                    // Silence
                    // If speech was started, check for silence timeout (end of speech)
                    if (speechStarted && (nowMs() - silenceStart > SILENCE_TIMEOUT)) {
                        console.log("Silence timeout (Backend STT), stopping...");
                        stopListening();
                        return; 
                    }
                    // If speech never started, just update visualizer to show we are alive
                    setVisualizerData(new Array(5).fill(average > 5 ? 15 : 10));
                }
                
                requestAnimationFrame(checkSilence);
            };
            
            checkSilence();

        } catch (err) {
            console.error("Microphone error (Backend STT):", err);
            transition(VOICE_STATES.ERROR, { reason: 'mic_permission_denied' });
            setErrorMessage("Microphone access denied. Please check settings.");
        }

    } else {
        // --- Web Speech API Implementation (Legacy/Fallback) ---
        try {
          const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
          if (!SpeechRecognition) {
            transition(VOICE_STATES.ERROR, { reason: 'browser_unsupported' });
            return;
          }

          // Stop any existing instance
          if (recognitionRef.current) {
            try {
                recognitionRef.current.stop();
            } catch { void 0; }
          }

          const recognition = new SpeechRecognition();
          recognitionRef.current = recognition;
          
          recognition.continuous = false; // Changed to false for better mobile stability
          recognition.interimResults = true; 
          
          // Robust language code selection
          let langCode = 'en-IN';
          if (i18n.language.startsWith('te')) langCode = 'te-IN';
          else if (i18n.language.startsWith('hi')) langCode = 'hi-IN';
          
          recognition.lang = langCode;

          // Flag to prevent double submission
          let hasProcessed = false;

          const resetCommitTimer = () => {
              if (commitTimerRef.current) clearTimeout(commitTimerRef.current);
              commitTimerRef.current = setTimeout(() => {
                  console.log("Commit timer fired. Transcript:", transcriptRef.current, "hasProcessed:", hasProcessed);
                  if (isMounted.current && transcriptRef.current.trim().length > 0 && !hasProcessed) {
                      console.log("Commit timer: Silence detected, forcing send of:", transcriptRef.current);
                      hasProcessed = true; // Prevent onend from sending again
                      
                      const textToSend = transcriptRef.current;
                      setTranscript(''); // Clear visual immediately
                      accumulatedTranscriptRef.current = ''; // Reset accumulation
                      
                      // Send immediately
                      handleSend(textToSend);
                      
                      // Stop recognition (will trigger onend, which will see hasProcessed=true and do nothing)
                      try { recognition.stop(); } catch { void 0; }
                  } else {
                      console.log("Commit timer ignored. Conditions not met.");
                  }
              }, 2000); // Increased to 2000ms to allow for natural pauses
          };

          console.log(`Starting recognition with lang: ${recognition.lang}`);

          recognition.onstart = () => {
            if (!isMounted.current) return;
            console.log("Recognition started");
            transition(VOICE_STATES.LISTENING);
            setIsSoundDetected(false);
            
            // IMPORTANT: Restore accumulated transcript to visual state on restart
            if (accumulatedTranscriptRef.current) {
                 setTranscript(accumulatedTranscriptRef.current);
                 transcriptRef.current = accumulatedTranscriptRef.current;
            } else {
                 setTranscript('');
            }

            // Start silence timer (long timeout)
            if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = setTimeout(() => {
                if (isMounted.current && transcriptRef.current.length === 0) {
                    console.log("Silence timeout - restarting recognition session");
                    // Don't call stopListening() as that kills the intent to listen.
                    // Just stop the recognition instance to trigger onend and restart.
                    if (recognitionRef.current) {
                        try { recognitionRef.current.stop(); } catch { void 0; }
                    }
                }
            }, 8000); // Increased to 8s to prevent premature stopping
          };

          recognition.onsoundstart = () => {
              // Visual feedback that sound is detected
              if (isMounted.current) {
                  setIsSoundDetected(true);
                  setVisualizerData(prev => prev.map(() => Math.random() * 35 + 15)); // Higher spikes
                  
                  // Clear silence timer when sound is detected
                  if (silenceTimerRef.current) {
                      clearTimeout(silenceTimerRef.current);
                      silenceTimerRef.current = null;
                  }
              }
          };

          recognition.onspeechstart = () => {
              // Visual feedback that speech is detected
               if (isMounted.current) {
                  setIsSoundDetected(true);
                  setVisualizerData(prev => prev.map(() => Math.random() * 45 + 20)); // Even higher spikes
                  
                  // Clear silence timer when speech is detected
                  if (silenceTimerRef.current) {
                      clearTimeout(silenceTimerRef.current);
                      silenceTimerRef.current = null;
                  }
                  resetCommitTimer();
              }
          };

          recognition.onspeechend = () => {
              // Start silence timer when speech ends
              if (isMounted.current && !silenceTimerRef.current) {
                  console.log("Speech ended, starting silence timer...");
                  silenceTimerRef.current = setTimeout(() => {
                      console.log("Silence timeout reached, restarting listening...");
                      const currentState = getCurrentState();
                      if (currentState === VOICE_STATES.LISTENING && isMounted.current) {
                          // Restart listening
                          startListening();
                      }
                  }, SILENCE_TIMEOUT);
              }
          };

          recognition.onerror = (event) => {
            console.error("Speech recognition error:", event.error);
            if (isMounted.current) {
                // Ignore 'aborted' errors as they are often triggered by manual stops or restarts
                if (event.error === 'aborted') {
                    return;
                }

                // [DEBUG] Always show detailed error in transcript area for visibility
                setTranscript(`${t('error_prefix')}${event.error}`); 

                if (event.error === 'not-allowed') {
                    transition(VOICE_STATES.ERROR, { reason: 'mic_permission_denied' });
                    const permissionMessage = t('mic_permission_denied') || 
                        "Microphone access denied. Please enable microphone permissions in your browser settings and refresh the page.";
                    setMessages(prev => [...prev, { 
                        role: 'assistant', 
                        text: permissionMessage
                    }]);
                    setErrorMessage(permissionMessage);
                } else if (event.error === 'service-not-allowed' || event.error === 'language-not-supported' || event.error === 'network') {
                    console.warn(`Web Speech API error: ${event.error}. Falling back to Backend STT.`);
                    setIsBackendSTTActive(true);
                    isBackendSTTActiveRef.current = true; // Immediate update for safety
                    setTranscript(t('switching_engine'));
                    
                    // Restart with backend STT
                    setTimeout(() => {
                        if (isMounted.current) startListening();
                    }, 500);
                    
                } else if (event.error === 'no-speech') {
                    console.log("No speech detected, auto-retrying...");
                    // Don't show "No speech" error to user, just silently restart
                    // setTranscript(t('no_speech_retry')); 
                    
                    // Immediate restart logic for no-speech
                    if (recognitionRef.current) {
                        try { recognitionRef.current.stop(); } catch { void 0; }
                    }
                    
                    setTimeout(() => {
                        const currentState = getCurrentState();
                        if (currentState !== VOICE_STATES.PAUSED && isMounted.current) {
                            startListening();
                        }
                    }, 100); // Fast restart
                } else if (event.error === 'aborted') {
                    // Normal abort, don't transition to error
                } else {
                    transition(VOICE_STATES.ERROR, { reason: event.error });
                    const errorMsg = t('recognition_error') || 
                        `Speech recognition error: ${event.error}. Please try again.`;
                    setErrorMessage(errorMsg);
                    setMessages(prev => [...prev, { 
                        role: 'assistant', 
                        text: errorMsg
                    }]);
                }
            }
          };

          recognition.onresult = (event) => {
            if (!isMounted.current) return;
            
            let finalTranscript = '';
            let interimTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            // Check state to ensure we don't process if we shouldn't be listening
            const currentState = getCurrentState();
            if (currentState !== VOICE_STATES.LISTENING) {
                console.log("Ignored result in state:", currentState);
                return;
            }

            if (interimTranscript) {
                const fullTranscript = (accumulatedTranscriptRef.current + " " + interimTranscript).trim();
                setTranscript(fullTranscript);
                transcriptRef.current = fullTranscript; // Update ref immediately to avoid race condition
                
                // Reset commit timer on every new result
                resetCommitTimer();
            }

            if (finalTranscript) {
                // Append to accumulated
                accumulatedTranscriptRef.current = (accumulatedTranscriptRef.current + " " + finalTranscript).trim();
                const fullTranscript = accumulatedTranscriptRef.current;
                
                // Update to final transcript
                setTranscript(fullTranscript); 
                transcriptRef.current = fullTranscript; // Update ref immediately
                
                // NOTE: Do NOT send immediately on finalTranscript. Wait for commitTimer (3.5s silence).
                resetCommitTimer();
            }
          };

          recognition.onend = () => {
            if (!isMounted.current) return;
            console.log("Recognition ended. hasProcessed:", hasProcessed, "transcript:", transcriptRef.current, "shouldListen:", shouldListenRef.current);
            
            if (silenceTimerRef.current) {
                clearTimeout(silenceTimerRef.current);
                silenceTimerRef.current = null;
            }

            // Only restart if we still intend to listen and haven't processed a result
            if (!hasProcessed && shouldListenRef.current) {
                console.log("Browser stopped, restarting to wait for 3.5s pause...");
                
                const currentText = transcriptRef.current.trim();
                const accumulatedText = accumulatedTranscriptRef.current.trim();
                
                if (currentText.length > accumulatedText.length) {
                    console.log("Saving interim text to accumulated before restart:", currentText);
                    accumulatedTranscriptRef.current = currentText;
                }

                // Restart listening loop
                const currentState = getCurrentState();
                if (currentState !== VOICE_STATES.PAUSED && 
                    currentState !== VOICE_STATES.PROCESSING && 
                    currentState !== VOICE_STATES.THINKING &&
                    currentState !== VOICE_STATES.SPEAKING) {
                    try {
                        setTimeout(() => {
                            const stateNow = getCurrentState();
                            if (isMounted.current && 
                                stateNow !== VOICE_STATES.PAUSED && 
                                stateNow !== VOICE_STATES.PROCESSING && 
                                stateNow !== VOICE_STATES.THINKING &&
                                stateNow !== VOICE_STATES.SPEAKING) {
                                startListening(); 
                            }
                        }, 100); 
                    } catch (e) {
                        console.error("Restart error:", e);
                    }
                }
            }
          };

          recognition.start();
        } catch (error) {
          console.error("Speech recognition error:", error);
          if (isMounted.current) {
              transition(VOICE_STATES.ERROR, { reason: 'recognition_start_failed', error: error.message });
          }
        }
    }
  }

  // Requirement: Restart listening when language changes
  useEffect(() => {
      if (isListening) {
          console.log(`Language changed to ${i18n.language} - restarting recognition...`);
          stopListening();
          setTimeout(() => {
              if (isMounted.current) {
                  startListening();
              }
          }, 500);
      }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [i18n.language]);

  useEffect(() => {
    isMounted.current = true;
    let startTimer;

    const init = async () => {
        if (!isOpen) return;

        console.log("VoiceOverlay init started. Mode:", mode);
        
        // Show initial loading/prompt message
        setMessages([{ role: 'assistant', text: t('allow_mic_access') }]);
        
        // Requirement: Request Mic Permissions IMMEDIATELY
        // This ensures the browser prompt appears right away, not just when the agent stops speaking.
        try {
            console.log("Requesting initial mic permission...");
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop()); // Release immediately, we'll reopen in startListening
            console.log("Initial mic permission granted.");
        } catch (e) {
            console.warn("Initial mic permission denied/dismissed:", e);
            // We continue anyway, as startListening will try again and handle the error
            setMessages([{ role: 'assistant', text: t('mic_required') }]);
        }

        // Show loading state immediately
        setMessages([{ role: 'assistant', text: t('loading') }]);

        let greetingText = t('greeting');
        
        // Reset state to ensure fresh start
        transition(VOICE_STATES.IDLE);
        
        if (mode.startsWith('onboarding')) {
            // Requirement: Specific greeting for onboarding
            greetingText = t('onboarding_greeting');
            
            try {
                // Check if we have existing profile data to resume
                const hasExistingData = userProfile && (
                    userProfile.name || 
                    userProfile.location || 
                    userProfile.primary_crop || 
                    userProfile.farm_size_acres || 
                    userProfile.mobile_number
                );

                if (hasExistingData) {
                    console.log("Resuming onboarding with profile:", userProfile);
                    const session = {
                        profile: userProfile,
                        conversation_history: [],
                        completed: false
                    };
                    
                    // Call process to get the next question
                    const res = await axios.post('/api/v1/onboarding/process', {
                        user_input: "continue", 
                        session_state: session,
                        language: i18n.language
                    });
                    
                    if (res.data.success) {
                        setOnboardingSession(res.data.session_state);
                        greetingText = res.data.next_prompt;
                    }
                } else {
                     // Even for new onboarding, start with the specific greeting
                     // We can play it optimistically while fetching session in background
                     // This ensures instant feedback (Requirement: Low Latency)
                     
                     // Play Greeting IMMEDIATELY using Browser TTS
                     const defaultGreeting = t('onboarding_greeting');
                     greetingText = defaultGreeting;
                     
                     // Show UI immediately
                     setMessages([{ role: 'assistant', text: greetingText }]);
                     
                     // Play audio immediately (browser TTS for speed)
                     setTimeout(() => {
                         if (isMounted.current && isOpen) {
                            playResponse(greetingText, { forceBrowserTTS: true });
                         }
                     }, 50);

                     // Fetch backend session in background
                     console.log("Fetching onboarding start (background)...");
                     
                     // Helper to get location safely
                     const getLocation = () => new Promise((resolve) => {
                         if (!navigator.geolocation) return resolve(null);
                         navigator.geolocation.getCurrentPosition(
                             (pos) => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
                             (err) => { console.warn("Geo error:", err); resolve(null); },
                             { timeout: 3000, enableHighAccuracy: false }
                         );
                     });

                     getLocation().then(loc => {
                        let url = `/api/v1/onboarding/start?language=${i18n.language}`;
                        if (loc) {
                            url += `&latitude=${loc.lat}&longitude=${loc.lon}`;
                        }
                        
                        axios.get(url, { timeout: 8000 })
                            .then(res => {
                                if (res.data.success && isMounted.current) {
                                    // Use callback to ensure we don't overwrite if state advanced (though unlikely this early)
                                    setOnboardingSession(prev => {
                                        if (prev && prev.conversation_history && prev.conversation_history.length > 1) {
                                            // Session already advanced? Keep current but maybe merge suggested_location?
                                            // For safety, if we already have a session with user input, ignore this late init
                                            console.warn("Onboarding session advanced before init completed, ignoring init.");
                                            return prev;
                                        }
                                        console.log("Setting initial onboarding session:", res.data.session_state);
                                        return res.data.session_state;
                                    });
                                }
                            })
                            .catch(e => {
                                console.error("Failed to init onboarding session:", e);
                                if (isMounted.current) {
                                    // Ensure we at least have a session so UI doesn't break
                                    setOnboardingSession({
                                        profile: {},
                                        conversation_history: [],
                                        completed: false
                                    });
                                }
                            });
                     });
                         
                     // Return early so we don't double-play the greeting
                     return;
                }
            } catch (e) {
                console.error("Failed to start/resume onboarding:", e);
                // Fallback
                greetingText = t('onboarding_greeting');
            }
        }
        
        if (isMounted.current && isOpen) {
            console.log("Setting greeting text:", greetingText);
            setMessages([{ role: 'assistant', text: greetingText }]);
            
            // Allow state update to propagate
            setTimeout(() => {
                if (isMounted.current && isOpen) {
                    console.log("Calling playResponse with:", greetingText);
                    playResponse(greetingText, { forceBrowserTTS: true }); // Default to fast greeting
                }
            }, 50);
        }
    };

    init();
    
    return () => {
      // Cleanup
      isMounted.current = false; // Ensure we don't update state on unmounted component
      if (startTimer) clearTimeout(startTimer);
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      if (autoRestartTimerRef.current) clearTimeout(autoRestartTimerRef.current);
      stopListening();
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (e) { void e; }
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        try { mediaRecorderRef.current.stop(); } catch (e) { void e; }
      }
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, mode]); // Re-run when opened or mode changes

  const handleSendAudio = async (audioBlob) => {
    if (!isMounted.current) return;
    
    // Add user message (Placeholder)
    setMessages(prev => [...prev, { role: 'user', text: t('audio_message') }]);
    
    // Transition to PROCESSING state
    transition(VOICE_STATES.PROCESSING);
    
    try {
        const formData = new FormData();
        const filename = audioBlob.type?.includes('webm') ? 'recording.webm' : 'recording.wav';
        formData.append('file', audioBlob, filename);
        // Use the language that was active when recording started, NOT current language
        // This prevents race conditions where language is switched mid-processing
        const langToSend = recordingLanguageRef.current || i18n.language;
                formData.append('language', langToSend);
                
                // Append user profile if available to provide context
                if (userProfile) {
                    formData.append('profile', JSON.stringify(userProfile));
                }

                // Append chat history for context
                const history = messages.map(m => ({ role: m.role, content: m.text }));
                formData.append('history', JSON.stringify(history));
                
                console.log(`Sending audio with language: ${langToSend} (Current UI: ${i18n.language})`);

        if (mode.startsWith('onboarding')) {
            // Use ref to get latest session state, avoiding stale closures
            const currentSession = onboardingSessionRef.current;
            formData.append('session_state', JSON.stringify(currentSession));
            const response = await axios.post('/api/v1/onboarding/interact_audio', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });
            if (!isMounted.current) return;

            const { transcript, next_prompt, session_state, completed, profile, scenario } = response.data;

            setMessages(prev => {
                const newMsgs = [...prev];
                newMsgs[newMsgs.length - 1].text = transcript || t('audio_placeholder');
                return newMsgs;
            });

            if (session_state) setOnboardingSession(session_state);

            transition(VOICE_STATES.THINKING);
            const responseText = next_prompt || t('didnt_catch_that');
            setMessages(prev => [...prev, { role: 'assistant', text: responseText }]);
            await playResponse(responseText);

            if (completed) {
                setTimeout(() => {
                    if (isMounted.current) {
                        onResult({
                            intent: 'onboarding_complete',
                            profile: profile,
                            scenario: scenario,
                            text: responseText
                        });
                    }
                }, 1000);
            }
        } else {
            const response = await axios.post('/api/v1/voice/interact', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });
            
            if (!isMounted.current) return;
            
            const { intent, response_text, transcript, data } = response.data;
            
            setMessages(prev => {
                const newMsgs = [...prev];
                newMsgs[newMsgs.length - 1].text = transcript || t('audio_placeholder');
                return newMsgs;
            });
            
            transition(VOICE_STATES.THINKING);
            const finalText = response_text || (intent === 'unknown' ? t('couldnt_understand') : t('thinking'));
            setMessages(prev => [...prev, { role: 'assistant', text: finalText }]);
            
            await playResponse(finalText);

            if (intent === 'decision_support' && data) {
                 setMessages(prev => [...prev, { role: 'assistant', type: 'harvest_decision', data: data }]);
            }
            
            if (intent !== 'greeting' && intent !== 'unknown' && data) {
               setTimeout(() => {
                   if (isMounted.current) onResult({ intent, ...data, text: response_text });
               }, 1000);
            }
        }

    } catch (error) {
        console.error("Audio Interaction error:", error);
        // Error handling...
        if (isMounted.current) {
            setMessages(prev => [...prev, { role: 'assistant', text: t('audio_process_error') }]);
            transition(VOICE_STATES.ERROR, { reason: 'interaction_error', error: error.message });
            setTimeout(() => {
                const currentState = getCurrentState();
                if (currentState !== VOICE_STATES.PAUSED) {
                    startListening();
                }
            }, 2000);
        }
    }
  };

  const handleSend = async (text) => {
    if (!text.trim() || !isMounted.current) return;

    // Add user message
    setMessages(prev => [...prev, { role: 'user', text }]);
    
    // Transition to PROCESSING state
    transition(VOICE_STATES.PROCESSING);

    try {
      const useStream = mode.startsWith('onboarding') ? false : true;

      if (mode.startsWith('onboarding')) {
          // Onboarding Flow
          transition(VOICE_STATES.THINKING);
          // Use ref to get latest session state
          const currentSession = onboardingSessionRef.current;
          const response = await axios.post('/api/v1/onboarding/process', {
              user_input: text,
              session_state: currentSession,
              language: i18n.language
          });
          
          if (!isMounted.current) return;
          
          const { next_prompt, session_state, completed, profile, scenario } = response.data;
          
          setOnboardingSession(session_state);
          
          const responseText = next_prompt || "I didn't catch that.";
          setMessages(prev => [...prev, { role: 'assistant', text: responseText }]);
          
          await playResponse(responseText);
          
          if (completed) {
              console.log("Onboarding completed!", profile);
              setTimeout(() => {
                  if (isMounted.current) {
                      onResult({ 
                          intent: 'onboarding_complete', 
                          profile: profile,
                          scenario: scenario,
                          text: responseText
                      });
                  }
              }, 1000);
          }
      } else if (useStream) {
        transition(VOICE_STATES.THINKING);
        let metaIntent = null;
        let metaData = null;
        let aiText = "";
        
        // Use prop profile if available (normal mode), otherwise session profile (onboarding)
        const profileToUse = userProfile || onboardingSession?.profile;
        console.log("Using profile for text stream:", profileToUse);
        
        const profileParam = profileToUse ? `&profile=${encodeURIComponent(JSON.stringify(profileToUse))}` : "";
        const baseUrl = import.meta.env.VITE_API_URL || '';
        const url = `${baseUrl}/api/v1/voice/interact_text_stream?text=${encodeURIComponent(text)}&language=${encodeURIComponent(i18n.language)}${profileParam}`;
        
        abortControllerRef.current = new AbortController();
        const signal = abortControllerRef.current.signal;

        try {
            const res = await fetch(url, { signal });
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const parts = buffer.split("\n\n");
                buffer = parts.pop() || "";
                for (const p of parts) {
                    const line = p.trim();
                    if (!line) continue;
                    if (line.startsWith("event: meta")) continue;
                    if (line.startsWith("data:")) {
                        const jsonStr = line.slice(5).trim();
                        try {
                            const obj = JSON.parse(jsonStr);
                            if (obj.profile) {
                                console.log("Updating profile from SSE:", obj.profile);
                                setOnboardingSession(prev => ({ ...prev, profile: obj.profile }));
                            }
                            if (obj.intent) {
                                metaIntent = obj.intent;
                            }
                            if (obj.data) {
                                metaData = obj.data;
                            }
                            if (obj.text) {
                                aiText += obj.text;
                                setMessages(prev => {
                                    const lastMsg = prev[prev.length - 1];
                                    if (lastMsg && lastMsg.role === 'assistant' && lastMsg.isStreaming) {
                                        const newMsgs = [...prev];
                                        newMsgs[newMsgs.length - 1] = { ...lastMsg, text: aiText };
                                        return newMsgs;
                                    }
                                    return [...prev, { role: 'assistant', text: aiText, isStreaming: true }];
                                });
                            }
                        } catch { void 0; }
                    }
                }
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('Fetch aborted for text stream.');
                return; // Stop further processing
            }
            throw error; // Re-throw other errors
        }

        if (!isMounted.current) return;
        await playResponse(aiText);
        
        if (metaIntent === 'decision_support' && metaData) {
             setMessages(prev => [...prev, { role: 'assistant', type: 'harvest_decision', data: metaData }]);
        } else if (metaIntent && metaIntent !== 'greeting' && metaIntent !== 'unknown') {
          onResult({ intent: metaIntent, text: aiText });
        }
      } else {
        const chatHistory = messagesRef.current.map(m => ({ role: m.role, content: m.text }));
        
        // Use prop profile if available (normal mode), otherwise session profile (onboarding)
        const profileToUse = userProfile || onboardingSession?.profile;
        console.log("Using profile for text interaction:", profileToUse);

        const response = await axios.post('/api/v1/voice/interact_text', {
          text: text,
          language: i18n.language,
          context: {
             history: chatHistory,
             profile: profileToUse
          }
        });
        if (!isMounted.current) return;
        const { intent, response_text, data, profile } = response.data;
        
        if (profile) {
             setOnboardingSession(prev => ({ ...prev, profile: profile }));
        } else if (data && data.profile) {
             setOnboardingSession(prev => ({ ...prev, profile: data.profile }));
        }

        transition(VOICE_STATES.THINKING);
        setMessages(prev => [...prev, { role: 'assistant', text: response_text }]);
        await playResponse(response_text);
        
        if (intent === 'decision_support' && data) {
            setMessages(prev => [...prev, { role: 'assistant', type: 'harvest_decision', data: data }]);
        } else if (intent !== 'greeting' && intent !== 'unknown' && data) {
           setTimeout(() => {
               if (isMounted.current) onResult({ intent, ...data, text: response_text });
           }, 1000);
        }
      }

    } catch (error) {
      console.error("Interaction error:", error);
      if (isMounted.current) {
          let errorMessage = "Sorry, I'm having trouble connecting. Please try again.";
          
          if (error.response) {
              // Server responded with error
              if (error.response.status === 500) {
                  errorMessage = `I'm having trouble thinking right now (Backend 500). Details: ${error.response.data?.detail || error.message}`;
              } else {
                  errorMessage = `Server Error (${error.response.status}): ${error.response.data?.detail || error.message}`;
              }
          } else if (error.request) {
              // Network error
              errorMessage = `I cannot reach the server. Network Error: ${error.message}`;
          } else {
              errorMessage = `Error: ${error.message}`;
          }

          setMessages(prev => [...prev, { role: 'assistant', text: errorMessage }]);
          transition(VOICE_STATES.ERROR, { reason: 'interaction_error', error: error.message });
          
          // Try to restart listening even on error
          const currentState = getCurrentState();
          if (currentState !== VOICE_STATES.PAUSED) {
            // slightly delay to avoid loop
            setTimeout(() => {
                        if (getCurrentState() !== VOICE_STATES.LISTENING) {
                            transition(VOICE_STATES.LISTENING);
                        }
                startListening();
            }, 2000);
          }
      }
    }
  };

  const handleManualSubmit = (formData) => {
    console.log("Manual Form Submitted:", formData);
    
    // Update local state
    const updatedProfile = { ...onboardingSession.profile, ...formData };
    setOnboardingSession(prev => ({
        ...prev,
        profile: updatedProfile,
        completed: true 
    }));

    // Trigger completion
    onResult({
        intent: 'onboarding_complete',
        profile: updatedProfile,
        scenario: null,
        text: "Manual entry completed."
    });
  };

  useEffect(() => {
    console.log("VoiceOverlay mounted. isOpen:", isOpen, "mode:", mode);
    return () => console.log("VoiceOverlay unmounted");
  }, [isOpen, mode]);

  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-gray-100 dark:bg-gray-900 transition-colors duration-300 p-4 md:p-0">
      <MobileFrame darkMode={darkMode} className="shadow-2xl">
        <div className="flex flex-col h-full w-full overflow-hidden bg-slate-50 dark:bg-slate-900 transition-colors duration-300 relative">
          
          {/* Top Toolbar - Always Visible */}
          <div className="px-5 py-3 flex justify-between items-center bg-white dark:bg-slate-900 border-b border-gray-50 dark:border-slate-800 shrink-0 shadow-sm z-10 transition-colors duration-300 relative">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center text-green-700 dark:text-green-400 font-bold">K</div>
              <div className="flex flex-col">
                <span className="font-bold text-gray-800 dark:text-white text-sm leading-tight">Krishi Assistant</span>
                <div className="flex items-center space-x-1">
                  <div className={`w-1.5 h-1.5 rounded-full ${isListening ? 'bg-red-500 animate-pulse' : 'bg-green-500'}`}></div>
                  <span className={`text-[10px] font-bold ${isListening ? 'text-red-500' : 'text-green-700 dark:text-green-400'}`}>
                    {isListening ? 'Listening' : 'Online'}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {/* Manual/Voice Toggle */}
              {mode.startsWith('onboarding') && (
                <button 
                  onClick={() => setIsManualMode(!isManualMode)}
                  className="p-2 bg-slate-100 dark:bg-slate-700 rounded-full text-slate-500 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                  title={isManualMode ? "Switch to Voice" : "Switch to Manual"}
                >
                  {isManualMode ? <Mic className="w-5 h-5" /> : <Keyboard className="w-5 h-5" />}
                </button>
              )}

              {toggleDarkMode && (
                <button 
                  onClick={toggleDarkMode}
                  className="p-2 bg-slate-100 dark:bg-slate-700 rounded-full text-slate-500 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                >
                  {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                </button>
              )}
              
               <button 
                  onClick={togglePause}
                  className={`p-2 rounded-full transition-colors ${
                      isPaused 
                          ? 'bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400' 
                          : 'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
                  }`}
                  title={isPaused ? "Resume" : "Pause"}
                >
                  {isPaused ? <Play className="w-5 h-5 fill-current" /> : <Pause className="w-5 h-5 fill-current" />}
              </button>

              <button 
                onClick={onClose}
                className="p-2 bg-slate-100 dark:bg-slate-700 rounded-full text-slate-500 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {mode.startsWith('onboarding') ? (
            isManualMode ? (
                <div className="flex-1 overflow-hidden relative flex flex-col bg-slate-50 dark:bg-slate-900">
                    <div className="flex-1 overflow-y-auto pb-10">
                         <ManualOnboardingForm 
                            profile={onboardingSession?.profile}
                            onSubmit={handleManualSubmit}
                            isProcessing={isProcessing}
                            onBack={() => setIsManualMode(false)}
                         />
                    </div>
                </div>
            ) : (
                <div className="flex-1 overflow-hidden relative flex flex-col">
                  {/* Full Screen Form Container with Bottom Padding for Sheet */}
                  <div className={`absolute inset-0 overflow-y-auto bg-slate-50 dark:bg-slate-900 scroll-smooth transition-all duration-300 ${
                      sheetMode === 'minimized' ? 'pb-[220px]' : 
                      sheetMode === 'expanded' ? 'pb-[92vh]' : 
                      'pb-[48vh]'
                  }`}>
                    {onboardingSession ? (
                        <OnboardingStatus profile={onboardingSession.profile || {}} />
                    ) : (
                        <div className="flex items-center justify-center h-full">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500"></div>
                        </div>
                    )}
                  </div>
                  
                  {/* Glassmorphic Bottom Sheet - Taller & More Transparent */}
              <div className={`absolute bottom-0 left-0 right-0 z-20 flex flex-col
                            bg-white/80 dark:bg-slate-800/90 backdrop-blur-xl
                            rounded-t-[2.5rem] border-t border-white/20 dark:border-slate-600/50
                            shadow-[0_-8px_32px_rgba(0,0,0,0.12)] transition-all duration-300 ease-in-out
                            ${getSheetHeightClass()}`}>
                    
                    {/* Drag Handle / Visualizer Header */}
                    <div 
                        className="flex flex-col justify-center items-center pt-3 pb-1 gap-2 cursor-pointer hover:bg-black/5 dark:hover:bg-white/5 transition-colors rounded-t-[2.5rem]"
                        onClick={(e) => {
                            // If user taps the header area (visualizer), treat it as a "Wake Up" or "Restart" signal
                            if (isListening) {
                                 // Already listening, maybe they want to expand/collapse
                                 setSheetMode(prev => prev === 'minimized' ? 'normal' : 'expanded');
                            } else if (!isProcessing && !isPlaying) {
                                 // If idle/paused, restart listening
                                 console.log("User tapped header to wake up/restart listening");
                                 restartListening();
                            }
                        }}
                    >
                       {/* Partition Line */}
                       <div className="w-16 h-1 bg-slate-200 dark:bg-slate-700 rounded-full mb-1" />
                       
                       {/* Resize Indicator - Now Interactive */}
                       <button 
                          className="absolute right-6 top-6 p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors z-30"
                          onClick={(e) => {
                              e.stopPropagation();
                              setSheetMode(prev => {
                                  if (prev === 'minimized') return 'normal';
                                  if (prev === 'expanded') return 'minimized';
                                  return 'minimized';
                              });
                          }}
                       >
                          {sheetMode === 'minimized' ? <ChevronUp size={24} /> : <ChevronDown size={24} />}
                       </button>
    
                       {isListening ? (
                          <div className="flex items-end gap-1 h-4">
                            {visualizerData.slice(0, 5).map((height, i) => (
                              <div 
                                key={i} 
                                style={{ height: `${Math.max(4, height/2)}px`, transition: 'height 0.1s ease' }} 
                                className="w-1 bg-green-500 rounded-full" 
                              />
                            ))}
                          </div>
                        ) : (
                          <div className="w-12 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full" />
                        )}
                    </div>
    
                    {/* Messages Area */}
                    <div className="flex-1 overflow-y-auto px-5 space-y-3 scroll-smooth mask-image-top-fade">
                      {messages.length === 0 && (
                        <div className="text-center text-slate-400 text-sm mt-4">
                          {t('say_hello') || "Say 'Hello' to start"}
                        </div>
                      )}
                      {messages.map((msg, idx) => (
                        <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                          <div className={`max-w-[90%] p-3.5 rounded-2xl text-sm leading-relaxed shadow-sm backdrop-blur-sm
                            ${msg.role === 'user' 
                              ? 'bg-green-600/90 text-white rounded-br-none shadow-green-500/20' 
                              : 'bg-white/80 dark:bg-slate-800/80 text-slate-800 dark:text-slate-200 rounded-bl-none border border-white/40 dark:border-slate-700'
                            }`}>
                            {msg.text}
                          </div>
                        </div>
                      ))}
                      <div ref={messagesEndRef} />
                    </div>
                    
                    {/* Floating Controls Area */}
                    <div className="p-4 pb-6">
                      <div className="min-h-[1.5rem] mb-2 text-center px-4 transition-all duration-200">
                        {transcript ? (
                            <p className={`text-base font-medium whitespace-pre-wrap break-words ${isStatusMessage(transcript) ? 'text-green-600 dark:text-green-400 animate-pulse' : 'text-slate-700 dark:text-slate-200'}`}>
                                {transcript}
                            </p>
                        ) : (
                            <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
                                {isListening ? "Listening..." : isProcessing ? "Processing..." : isPlaying ? "Tap mic to interrupt" : "Tap mic to speak"}
                            </p>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-3">
                        <div className="flex-1 relative">
                          <input
                            type="text"
                            value={textInputValue}
                            onChange={(e) => setTextInputValue(e.target.value)}
                            placeholder={t('type_message') || "Type a message..."}
                            disabled={isProcessing}
                            className={`w-full bg-slate-100/50 dark:bg-slate-800/50 border border-white/20 dark:border-slate-700/50 backdrop-blur-md rounded-full py-3.5 px-5 text-sm text-slate-800 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-green-500/50 outline-none transition-all ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' && textInputValue.trim()) {
                                handleSend(textInputValue);
                                setTextInputValue('');
                              }
                            }}
                          />
                        </div>
                        
                        <button
                          onClick={() => {
                            if (onboardingSession?.completed) {
                               onResult({
                                intent: 'onboarding_complete',
                                profile: onboardingSession.profile,
                                scenario: onboardingSession.scenario,
                                text: "Confirmed."
                              });
                            } else if (isProcessing) {
                              return;
                            } else if (isListening) {
                              stopListening();
                            } else if (isPlaying) {
                              handleInterrupt();
                            } else {
                              startListening();
                            }
                          }}
                          disabled={isProcessing && !onboardingSession?.completed}
                          className={`w-14 h-14 rounded-full flex items-center justify-center transition-all shadow-xl ${
                            onboardingSession?.completed
                              ? 'bg-green-500 hover:bg-green-600 shadow-green-400/30'
                              : isListening 
                                ? 'bg-red-500 hover:bg-red-600 scale-105 shadow-red-400/30' 
                                : isProcessing
                                  ? 'bg-slate-200 dark:bg-slate-700 cursor-not-allowed'
                                  : isPlaying
                                      ? 'bg-amber-500 hover:bg-amber-600 animate-pulse shadow-amber-400/30'
                                      : 'bg-green-600 hover:bg-green-700 shadow-green-400/30'
                          }`}
                        >
                          {onboardingSession?.completed ? (
                             <Check className="w-6 h-6 text-white" />
                          ) : isListening ? (
                            <div className="w-5 h-5 bg-white rounded-md animate-pulse" />
                          ) : isProcessing ? (
                             <div className="w-5 h-5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
                          ) : (
                            <Mic className="w-6 h-6 text-white" />
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
            )
          ) : (
            <div className="flex-1 flex flex-col overflow-hidden bg-slate-50 dark:bg-slate-900 transition-colors duration-300 relative">
              <div className="flex-1 overflow-y-auto p-5 space-y-4 pb-64 scroll-smooth">
                {messages.map((msg, idx) => (
                  <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} w-full`}>
                    {msg.type === 'harvest_decision' ? (
                         <div className="w-full">
                            <HarvestDecision decision={msg.data} />
                         </div>
                    ) : (
                        <div className={`max-w-[85%] p-4 rounded-2xl text-sm leading-relaxed shadow-sm ${msg.role === 'user' ? 'bg-green-600 text-white rounded-br-none' : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded-bl-none border border-slate-100 dark:border-slate-700'}`}>
                          {msg.text}
                        </div>
                    )}
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
              
              {/* Floating Controls - Transparent/Glassmorphic */}
              <div className="absolute bottom-4 left-4 right-4 p-5 bg-white/90 dark:bg-slate-800/95 backdrop-blur-md border border-slate-100/50 dark:border-slate-600/50 transition-all duration-300 z-20 rounded-3xl shadow-xl shadow-black/5">
                <div className="flex justify-center items-center h-16 mb-2 space-x-1.5">
                  {isListening ? (
                    <>
                      {visualizerData.map((height, i) => (
                        <div 
                          key={i} 
                          style={{ height: `${Math.max(4, height)}px`, transition: 'height 0.1s ease' }} 
                          className="w-1.5 bg-green-500 rounded-full shadow-[0_0_8px_rgba(34,197,94,0.6)]" 
                        />
                      ))}
                    </>
                  ) : isProcessing ? (
                    <div className="flex space-x-1">
                      <div className="w-3 h-3 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
                      <div className="w-3 h-3 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                      <div className="w-3 h-3 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                    </div>
                  ) : (
                    <div className="text-slate-400 dark:text-slate-300 text-sm font-medium">{isPlaying ? (t('tap_to_interrupt') || "Tap mic to interrupt") : (t('tap_mic') || "Tap mic to start")}</div>
                  )}
                </div>
                <div className="h-6 mb-3 text-center">
                  {transcript ? (
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-200 truncate px-4">{transcript}</p>
                  ) : (
                    <p className="text-xs text-slate-400 dark:text-slate-300">
                      {isListening ? (USE_BACKEND_STT ? (t('listening_local') || "Listening (Local Whisper)...") : (t('listening') || "Listening...")) : isProcessing ? (t('processing') || "Processing...") : (t('ready') || "Ready")}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      value={textInputValue}
                      onChange={(e) => setTextInputValue(e.target.value)}
                      placeholder={t('type_message') || "Type a message..."}
                      className="w-full bg-slate-100 dark:bg-slate-700 border-none rounded-full py-3 px-4 text-sm text-slate-800 dark:text-white placeholder-slate-400 focus:ring-2 focus:ring-green-500 outline-none transition-all"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && textInputValue.trim()) {
                          handleSend(textInputValue);
                          setTextInputValue('');
                        }
                      }}
                    />
                  </div>
                  <button
                    onClick={() => {
                      if (isListening) {
                        stopListening();
                      } else if (isPlaying) {
                        handleInterrupt();
                      } else {
                        startListening();
                      }
                    }}
                    className={`w-12 h-12 rounded-full flex items-center justify-center transition-all shadow-lg ${
                      isListening 
                        ? 'bg-red-500 hover:bg-red-600 scale-110 shadow-red-200 dark:shadow-red-900/50' 
                        : isPlaying
                            ? 'bg-amber-500 hover:bg-amber-600 animate-pulse shadow-amber-200 dark:shadow-amber-900/50'
                            : 'bg-green-600 hover:bg-green-700 shadow-green-200 dark:shadow-green-900/50'
                    }`}
                  >
                    {isListening ? (
                      <div className="w-4 h-4 bg-white rounded-sm animate-pulse" />
                    ) : isPlaying ? (
                       <Mic className="w-5 h-5 text-white" />
                    ) : (
                      <Mic className="w-5 h-5 text-white" />
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </MobileFrame>
    </div>
  );
};

export default VoiceOverlay;
