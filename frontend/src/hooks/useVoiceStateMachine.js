import { useState, useRef, useCallback, useEffect } from 'react';

/**
 * Voice Interaction State Machine Hook
 * 
 * States:
 * - IDLE: No interaction, waiting for user to start
 * - LISTENING: Actively listening for user speech
 * - PROCESSING: Transcribing and analyzing user input
 * - THINKING: AI generating response
 * - SPEAKING: Playing AI response audio
 * - PAUSED: User manually paused interaction
 * - ERROR: Error state, waiting for recovery
 * 
 * Valid State Transitions:
 * IDLE -> LISTENING (user taps mic or auto-start)
 * LISTENING -> PROCESSING (speech detected)
 * PROCESSING -> THINKING (transcription complete)
 * THINKING -> SPEAKING (response ready)
 * SPEAKING -> LISTENING (audio complete, auto-resume)
 * SPEAKING -> PROCESSING (barge-in detected)
 * ANY -> PAUSED (user pauses)
 * PAUSED -> LISTENING (user resumes)
 * ANY -> ERROR (error occurs)
 * ERROR -> IDLE (user retries)
 */

const VOICE_STATES = {
  IDLE: 'IDLE',
  LISTENING: 'LISTENING',
  PROCESSING: 'PROCESSING',
  THINKING: 'THINKING',
  SPEAKING: 'SPEAKING',
  PAUSED: 'PAUSED',
  ERROR: 'ERROR'
};

// Valid state transitions map
const VALID_TRANSITIONS = {
  [VOICE_STATES.IDLE]: [VOICE_STATES.LISTENING, VOICE_STATES.PAUSED, VOICE_STATES.ERROR, VOICE_STATES.SPEAKING],
  [VOICE_STATES.LISTENING]: [VOICE_STATES.PROCESSING, VOICE_STATES.PAUSED, VOICE_STATES.ERROR, VOICE_STATES.IDLE, VOICE_STATES.SPEAKING],
  [VOICE_STATES.PROCESSING]: [VOICE_STATES.THINKING, VOICE_STATES.PAUSED, VOICE_STATES.ERROR, VOICE_STATES.IDLE],
  [VOICE_STATES.THINKING]: [VOICE_STATES.SPEAKING, VOICE_STATES.PAUSED, VOICE_STATES.ERROR, VOICE_STATES.IDLE],
  [VOICE_STATES.SPEAKING]: [VOICE_STATES.LISTENING, VOICE_STATES.PROCESSING, VOICE_STATES.PAUSED, VOICE_STATES.ERROR, VOICE_STATES.IDLE],
  [VOICE_STATES.PAUSED]: [VOICE_STATES.LISTENING, VOICE_STATES.IDLE, VOICE_STATES.ERROR, VOICE_STATES.SPEAKING],
  [VOICE_STATES.ERROR]: [VOICE_STATES.IDLE, VOICE_STATES.LISTENING]
};

// Timeout configurations (in milliseconds)
const STATE_TIMEOUTS = {
  [VOICE_STATES.PROCESSING]: 30000, // 30 seconds
  [VOICE_STATES.THINKING]: 60000    // 60 seconds
};

export const useVoiceStateMachine = (initialState = VOICE_STATES.IDLE) => {
  const [state, setState] = useState(initialState);
  const stateRef = useRef(initialState);
  const timeoutRef = useRef(null);
  const callbacksRef = useRef([]);

  // Update ref whenever state changes
  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  /**
   * Check if a state transition is valid
   */
  const canTransition = useCallback((toState) => {
    const currentState = stateRef.current;
    const validTransitions = VALID_TRANSITIONS[currentState] || [];
    return validTransitions.includes(toState);
  }, []);

  /**
   * Clear any existing timeout
   */
  const clearStateTimeout = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  /**
   * Set a timeout for states that should not be stuck
   */
  const setStateTimeout = useCallback((newState) => {
    clearStateTimeout();
    
    const timeout = STATE_TIMEOUTS[newState];
    if (timeout) {
      timeoutRef.current = setTimeout(() => {
        const previousState = stateRef.current;
        console.warn(`State timeout: ${newState} exceeded ${timeout}ms, transitioning to ERROR`);
        clearStateTimeout();
        setState(VOICE_STATES.ERROR);
        stateRef.current = VOICE_STATES.ERROR;
        callbacksRef.current.forEach(callback => {
          try {
            callback(VOICE_STATES.ERROR, previousState, { reason: 'timeout', previousState: newState });
          } catch (error) {
            console.error('Error in state change callback:', error);
          }
        });
      }, timeout);
    }
  }, [clearStateTimeout]);

  /**
   * Transition to a new state with validation
   */
  const transition = useCallback((toState, metadata = {}) => {
    const currentState = stateRef.current;
    
    // Validate transition
    if (!canTransition(toState)) {
      console.error(`Invalid state transition: ${currentState} -> ${toState}`);
      return false;
    }

    // Log transition
    console.log(`State transition: ${currentState} -> ${toState}`, metadata);

    // Clear any existing timeout
    clearStateTimeout();

    // Update state
    setState(toState);
    stateRef.current = toState;

    // Set timeout for new state if applicable
    setStateTimeout(toState);

    // Notify callbacks
    callbacksRef.current.forEach(callback => {
      try {
        callback(toState, currentState, metadata);
      } catch (error) {
        console.error('Error in state change callback:', error);
      }
    });

    return true;
  }, [canTransition, clearStateTimeout, setStateTimeout]);

  /**
   * Register a callback for state changes
   */
  const onStateChange = useCallback((callback) => {
    if (typeof callback === 'function') {
      callbacksRef.current.push(callback);
      
      // Return unsubscribe function
      return () => {
        callbacksRef.current = callbacksRef.current.filter(cb => cb !== callback);
      };
    }
  }, []);

  /**
   * Get current state (from ref for immediate access in async callbacks)
   */
  const getCurrentState = useCallback(() => {
    return stateRef.current;
  }, []);

  /**
   * Reset to initial state
   */
  const reset = useCallback(() => {
    clearStateTimeout();
    setState(initialState);
    stateRef.current = initialState;
    console.log(`State machine reset to ${initialState}`);
  }, [initialState, clearStateTimeout]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearStateTimeout();
    };
  }, [clearStateTimeout]);

  return {
    state,
    stateRef,
    transition,
    canTransition,
    onStateChange,
    getCurrentState,
    reset,
    VOICE_STATES
  };
};

export { VOICE_STATES };
