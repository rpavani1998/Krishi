import React, { useState, useEffect } from 'react';
import { motion as Motion, AnimatePresence } from 'framer-motion';
import { Mic, Keyboard, ArrowLeft } from 'lucide-react';
import LanguageSelector from './LanguageSelector';
import KrishiLogo from '../assets/Krishi.png';
import { useTranslation } from 'react-i18next';

const Welcome = ({ onComplete, initialStep = 'splash' }) => {
  const { t } = useTranslation();
  const [step, setStep] = useState(initialStep); // splash, language, mode

  const [currentTaglineIndex, setCurrentTaglineIndex] = useState(0);

  const splashTexts = [
    { appName: "Krishi", tagline: "Sell Thoughtfully" },
    { appName: "కృషి", tagline: "ఆలోచించి అమ్మండి" },
    { appName: "कृषि", tagline: "सोच-समझकर बेचें" }
  ];

  useEffect(() => {
    // If initialStep is 'splash', run the timer. Otherwise, stay on the step.
    if (step === 'splash') {
      const t1 = setTimeout(() => setCurrentTaglineIndex(1), 2000);
      const t2 = setTimeout(() => setCurrentTaglineIndex(2), 3500);
      const t3 = setTimeout(() => setStep('language'), 5000);
      
      return () => {
        clearTimeout(t1);
        clearTimeout(t2);
        clearTimeout(t3);
      };
    }
  }, [step]);

  // If initialStep prop changes, update local state (useful for returning from other pages)
  useEffect(() => {
    if (initialStep !== 'splash') {
        setStep(initialStep);
    }
  }, [initialStep]);

  const handleLanguageSelect = () => {
    // i18n.changeLanguage is already handled by LanguageSelector
    // Just need to move to next step
    setStep('mode');
  };

  const handleModeSelect = (mode) => {
    // Pass the selected mode to the parent component
    onComplete(mode);
  };

  const handleBack = () => {
      if (step === 'mode') {
          setStep('language');
      }
  };

  const containerVariants = {
    hidden: { opacity: 0, x: 20 },
    visible: { opacity: 1, x: 0, transition: { duration: 0.5 } },
    exit: { opacity: 0, x: -20, transition: { duration: 0.3 } }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6 py-12 bg-gradient-to-b from-white via-green-50 to-green-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 h-full transition-colors duration-300 overflow-hidden relative">
      
      {/* Background Elements */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute -top-20 -right-20 w-64 h-64 bg-green-200/30 rounded-full blur-3xl"></div>
        <div className="absolute top-40 -left-20 w-72 h-72 bg-emerald-200/20 rounded-full blur-3xl"></div>
      </div>

      <AnimatePresence mode="wait">
        {step === 'splash' && (
          <Motion.div 
            key="splash"
            className="flex flex-col items-center justify-center w-full h-full z-10"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <Motion.div 
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5 }}
              className="mb-8 w-40 h-40 bg-white dark:bg-slate-800 rounded-3xl flex items-center justify-center shadow-xl shadow-green-100 dark:shadow-none border border-green-50 dark:border-slate-700 overflow-hidden p-4"
            >
              <img src={KrishiLogo} alt="Krishi Logo" className="w-full h-full object-contain" />
            </Motion.div>
            
            <div className="h-14 relative w-full flex justify-center mb-3">
              <AnimatePresence mode="wait">
                <Motion.h1 
                  key={currentTaglineIndex}
                  initial={{ opacity: 0, scale: 0.95, filter: "blur(5px)" }}
                  animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
                  exit={{ opacity: 0, scale: 1.05, filter: "blur(5px)" }}
                  transition={{ duration: 0.4, ease: "easeOut", delay: currentTaglineIndex === 0 ? 0.3 : 0 }}
                  className="text-5xl font-bold text-slate-900 dark:text-white tracking-tight font-sans absolute w-full text-center top-0"
                >
                  {splashTexts[currentTaglineIndex].appName}
                </Motion.h1>
              </AnimatePresence>
            </div>

            <Motion.div 
              initial={{ width: 0 }}
              animate={{ width: 80 }}
              transition={{ delay: 0.5, duration: 0.5 }}
              className="h-1.5 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full mb-8"
            />
            
            <div className="h-8 relative w-full flex justify-center">
              <AnimatePresence mode="wait">
                <Motion.p 
                  key={currentTaglineIndex}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.3, delay: currentTaglineIndex === 0 ? 0.8 : 0 }}
                  className="text-xl font-medium text-slate-600 dark:text-slate-400 absolute"
                >
                  {splashTexts[currentTaglineIndex].tagline}
                </Motion.p>
              </AnimatePresence>
            </div>
          </Motion.div>
        )}

        {step === 'language' && (
          <Motion.div 
            key="language"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="flex flex-col items-center w-full max-w-sm z-10"
          >
            <h2 className="text-3xl font-bold text-slate-800 dark:text-white mb-2 text-center">
              {t('select_language')}
            </h2>
            <p className="text-slate-500 dark:text-slate-400 mb-8 text-center">
              {t('choose_preferred_language')}
            </p>

            <LanguageSelector variant="large" onSelect={handleLanguageSelect} />
          </Motion.div>
        )}

        {step === 'mode' && (
          <Motion.div 
            key="mode"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="flex flex-col items-center w-full max-w-sm z-10"
          >
            <div className="w-full flex justify-start mb-4">
                <button 
                    onClick={handleBack}
                    className="p-2 -ml-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 transition-colors"
                    aria-label={t('back')}
                >
                    <ArrowLeft className="w-6 h-6" />
                </button>
            </div>

            <h2 className="text-3xl font-bold text-slate-800 dark:text-white mb-2 text-center">
              {t('how_do_you_prefer')}
            </h2>
            <p className="text-slate-500 dark:text-slate-400 mb-8 text-center">
              {t('choose_interaction_mode')}
            </p>

            <div className="w-full space-y-4">
              <button
                onClick={() => handleModeSelect('voice')}
                className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white rounded-xl p-6 flex flex-col items-center justify-center transition-all duration-200 shadow-lg shadow-green-200 dark:shadow-none group relative overflow-hidden"
              >
                <div className="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-bl-full -mr-4 -mt-4 transition-transform group-hover:scale-110"></div>
                <div className="bg-white/20 p-4 rounded-full mb-3 backdrop-blur-sm">
                  <Mic className="w-8 h-8 text-white" />
                </div>
                <span className="text-xl font-bold mb-1">{t('voice_mode')}</span>
                <span className="text-green-100 text-sm opacity-90">{t('talk_naturally')}</span>
              </button>

              <button
                onClick={() => handleModeSelect('manual')}
                className="w-full bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border-2 border-slate-200 dark:border-slate-700 rounded-xl p-6 flex flex-col items-center justify-center transition-all duration-200 group"
              >
                <div className="bg-slate-100 dark:bg-slate-700 p-4 rounded-full mb-3 group-hover:bg-white dark:group-hover:bg-slate-600 transition-colors">
                  <Keyboard className="w-8 h-8 text-slate-600 dark:text-slate-300" />
                </div>
                <span className="text-xl font-bold mb-1">{t('manual_mode')}</span>
                <span className="text-slate-500 dark:text-slate-400 text-sm">{t('type_details')}</span>
              </button>
            </div>
          </Motion.div>
        )}
      </AnimatePresence>
      

    </div>
  );
};

export default Welcome;
