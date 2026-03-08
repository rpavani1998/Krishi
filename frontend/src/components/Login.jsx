import React, { useState } from 'react';
import { motion as Motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { Lock, ArrowRight, X } from 'lucide-react';

const Login = ({ onLogin, onReset }) => {
  const { t } = useTranslation();

  const [pin, setPin] = useState(['', '', '', '']);
  const [error, setError] = useState(false);

  // Focus management
  const inputs = React.useRef([]);

  const handleChange = (index, value) => {
    if (isNaN(value)) return;
    
    const newPin = [...pin];
    newPin[index] = value;
    setPin(newPin);
    setError(false);

    // Auto-advance
    if (value && index < 3) {
      inputs.current[index + 1].focus();
    }
    
    // Check if complete
    if (index === 3 && value) {
        handleSubmit(newPin.join(''));
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !pin[index] && index > 0) {
      inputs.current[index - 1].focus();
    }
  };

  const handleSubmit = async (pinValue) => {
    // Simulate API call or check against stored PIN
    // In a real app, this would be a backend call
    // Here we just pass it up to App.jsx to verify
    
    setTimeout(() => {
        onLogin(pinValue);
    }, 500);
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6 py-12 bg-white dark:bg-slate-900 h-full transition-colors duration-300">
      
      <Motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-full max-w-sm flex flex-col items-center"
      >
        <div className="w-20 h-20 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mb-6">
          <Lock className="w-10 h-10 text-green-600 dark:text-green-400" />
        </div>

        <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">{t('welcome_back')}</h2>
        <p className="text-slate-500 dark:text-slate-400 mb-8 text-center">
          {t('enter_pin')}
        </p>

        <div className="flex gap-4 mb-8">
          {pin.map((digit, index) => (
            <input
              key={index}
              ref={el => inputs.current[index] = el}
              type="password"
              inputMode="numeric"
              maxLength={1}
              value={digit}
              onChange={(e) => handleChange(index, e.target.value)}
              onKeyDown={(e) => handleKeyDown(index, e)}
              className={`w-14 h-16 text-center text-3xl font-bold rounded-xl border-2 bg-slate-50 dark:bg-slate-800 focus:outline-none transition-all duration-200 ${
                error 
                  ? 'border-red-500 text-red-500' 
                  : 'border-slate-200 dark:border-slate-700 focus:border-green-500 dark:focus:border-green-500 text-slate-900 dark:text-white'
              }`}
            />
          ))}
        </div>

        {error && (
          <Motion.p 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-red-500 text-sm font-medium mb-6"
          >
            {t('incorrect_pin_msg')}
          </Motion.p>
        )}

        <button
            onClick={() => onReset()}
            className="text-sm text-slate-400 hover:text-green-600 dark:hover:text-green-400 transition-colors"
        >
            {t('forgot_pin')}
        </button>

      </Motion.div>
    </div>
  );
};

export default Login;
