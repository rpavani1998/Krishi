import React, { useState, useRef } from 'react';
import { motion as Motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { Lock, ArrowLeft } from 'lucide-react';

const SetPin = ({ onSetPin, onBack }) => {
  const { t } = useTranslation();
  const [pin, setPin] = useState(['', '', '', '']);
  const [confirmPin, setConfirmPin] = useState(['', '', '', '']);
  const [step, setStep] = useState('create'); // create, confirm
  const [error, setError] = useState(false);
  
  const inputs = useRef([]);

  const handlePinChange = (index, value, isConfirm = false) => {
    if (isNaN(value)) return;
    
    const currentPin = isConfirm ? [...confirmPin] : [...pin];
    const setFunc = isConfirm ? setConfirmPin : setPin;
    
    currentPin[index] = value;
    setFunc(currentPin);
    setError(false);

    if (value && index < 3) {
      inputs.current[index + 1].focus();
    }
    
    // Auto-advance logic
    if (index === 3 && value) {
      if (!isConfirm) {
        setTimeout(() => {
            setStep('confirm');
            setConfirmPin(['', '', '', '']);
            // Reset focus to first input of confirm
            // We need to wait for render
            setTimeout(() => {
                 if(inputs.current[0]) inputs.current[0].focus();
            }, 100);
        }, 300);
      } else {
        // Check match
        const pinStr = pin.join('');
        const confirmStr = currentPin.join('');
        if (pinStr === confirmStr) {
          onSetPin(pinStr);
        } else {
          setError(true);
          setConfirmPin(['', '', '', '']);
          inputs.current[0].focus();
        }
      }
    }
  };

  const handleKeyDown = (index, e, isConfirm = false) => {
    const currentPin = isConfirm ? confirmPin : pin;
    if (e.key === 'Backspace' && !currentPin[index] && index > 0) {
      inputs.current[index - 1].focus();
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6 py-12 bg-white dark:bg-slate-900 h-full transition-colors duration-300">
      <Motion.div
        key={step}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
        className="w-full max-w-sm flex flex-col items-center"
      >
        <div className="w-20 h-20 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mb-6 relative">
          {onBack && (
            <button 
              onClick={onBack}
              className="absolute -left-16 top-1/2 -translate-y-1/2 p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400 transition-colors"
            >
              <ArrowLeft className="w-6 h-6" />
            </button>
          )}
          <Lock className="w-10 h-10 text-green-600 dark:text-green-400" />
        </div>

        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
          {step === 'create' ? t('set_pin_title') : t('confirm_pin_title')}
        </h2>
        <p className="text-slate-500 dark:text-slate-400 mb-8 text-center">
          {step === 'create' 
            ? t('create_pin_desc') 
            : t('reenter_pin_desc')}
        </p>

        <div className="flex gap-4 mb-8">
          {(step === 'create' ? pin : confirmPin).map((digit, index) => (
            <input
              key={index}
              ref={el => inputs.current[index] = el}
              type="password"
              inputMode="numeric"
              maxLength={1}
              value={digit}
              onChange={(e) => handlePinChange(index, e.target.value, step === 'confirm')}
              onKeyDown={(e) => handleKeyDown(index, e, step === 'confirm')}
              className={`w-14 h-16 text-center text-3xl font-bold rounded-xl border-2 bg-slate-50 dark:bg-slate-800 focus:outline-none transition-all duration-200 ${
                error 
                  ? 'border-red-500 text-red-500' 
                  : 'border-slate-200 dark:border-slate-700 focus:border-green-500 dark:focus:border-green-500 text-slate-900 dark:text-white'
              }`}
              autoFocus={index === 0}
            />
          ))}
        </div>

        {error && (
          <Motion.p 
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-red-500 text-sm font-medium mb-6"
          >
            {t('pin_mismatch')}
          </Motion.p>
        )}
      </Motion.div>
    </div>
  );
};

export default SetPin;
