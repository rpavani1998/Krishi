import { useState, useEffect } from 'react';
import axios from 'axios';
import { AnimatePresence, motion as Motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import './locales/i18n';

import MobileFrame from './components/MobileFrame';
import Welcome from './components/Welcome';
import Login from './components/Login';
import Home from './components/Home';
import HarvestForm from './components/HarvestForm';
import Processing from './components/Processing';
import Results from './components/Results';
import MarketNews from './components/MarketNews';
import MarketPrices from './components/MarketPrices';
import VoiceOverlay from './components/VoiceOverlay';
import OfflineIndicator from './components/OfflineIndicator';
import Profile from './components/Profile';
import ManualOnboardingForm from './components/ManualOnboardingForm';
import ConfirmDetails from './components/ConfirmDetails';
import SetPin from './components/SetPin';
import CollectiveSale from './components/CollectiveSale';

function App() {
  const { t, i18n } = useTranslation();
  
  // Initialize user profile from local storage
  const [userProfile, setUserProfile] = useState(() => {
    try {
      const stored = localStorage.getItem('krishi_user_profile');
      return stored ? JSON.parse(stored) : null;
    } catch (e) {
      console.error("Failed to parse profile", e);
      return null;
    }
  });

  const [hasOnboarded, setHasOnboarded] = useState(!!userProfile);

  const [step, setStep] = useState(() => {
    if (userProfile) {
        return userProfile.pin ? 'login' : 'home';
    }
    return 'welcome';
  });

  const [harvestData, setHarvestData] = useState(null);
  const [apiData, setApiData] = useState(null);
  const [, setError] = useState(null);
  const [showVoiceOverlay, setShowVoiceOverlay] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [voiceSettings, setVoiceSettings] = useState({
      speed: 1.0,
      pitch: 1.0,
      volume: 1.0,
      accent: 'co.in'
  });
  
  const [tempProfile, setTempProfile] = useState(null);
  const [preferredMode, setPreferredMode] = useState('voice'); // voice or manual
  const [welcomeInitialStep, setWelcomeInitialStep] = useState('splash');

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const toggleDarkMode = () => {
    console.log("App: Toggling Dark Mode. Previous:", darkMode);
    setDarkMode(prev => !prev);
  };

  const handleLanguageChange = (lang) => {
    i18n.changeLanguage(lang);
  };

  const handleWelcomeComplete = (mode) => {
    setPreferredMode(mode);
    if (mode === 'manual') {
        setStep('onboarding_form');
        setShowVoiceOverlay(false);
    } else {
        setStep('onboarding_voice');
        setShowVoiceOverlay(true);
    }
  };

  const handleManualSubmit = (profileData) => {
      setTempProfile(profileData);
      setStep('confirm_details');
      setShowVoiceOverlay(false); // Ensure overlay is closed
  };

  const handleConfirmDetails = () => {
      setStep('set_pin');
  };

  const handleEditDetails = () => {
      // Go back to the preferred mode to edit
      if (preferredMode === 'manual') {
          setStep('onboarding_form');
      } else {
          setStep('onboarding_voice');
          setShowVoiceOverlay(true);
      }
  };

  const handleBackFromSetPin = () => {
      setStep('confirm_details');
  };

  const handleSetPin = (pin) => {
      // Save final profile
      const finalProfile = { 
          ...tempProfile, 
          pin: pin, 
          created_at: new Date().toISOString() 
      };
      
      localStorage.setItem('krishi_user_profile', JSON.stringify(finalProfile));
      setUserProfile(finalProfile);
      setHasOnboarded(true);
      setStep('home');
  };

  const handleLogin = (pin) => {
    if (userProfile && userProfile.pin === pin) {
      setStep('home');
    } else {
      alert(t('incorrect_pin')); // Should be handled in Login component
    }
  };

  const handleReset = () => {
    if (confirm(t('reset_confirm'))) {
        localStorage.removeItem('krishi_user_profile');
        setUserProfile(null);
        setHasOnboarded(false);
        setStep('welcome');
    }
  };

  const handleStart = () => {
    setShowVoiceOverlay(true);
  };

  const handleOpenNews = () => {
    if (!hasOnboarded) {
      alert(i18n.t('complete_onboarding_first') || "Please complete onboarding first!");
      return;
    }
    setStep('market_news');
  };

  const handleOpenMarket = () => {
    if (!hasOnboarded) {
      alert(i18n.t('complete_onboarding_first') || "Please complete onboarding first!");
      return;
    }
    setStep('market_prices');
  };

  const handleOpenProfile = () => {
    if (!hasOnboarded) {
      alert(i18n.t('complete_onboarding_first') || "Please complete onboarding first!");
      return;
    }
    setStep('profile');
  };

  const handleOpenHarvest = () => {
    if (!hasOnboarded) {
      alert(i18n.t('complete_onboarding_first') || "Please complete onboarding first!");
      return;
    }
    setStep('form');
  };

  const handleOpenCollectiveSale = () => {
    if (!hasOnboarded) {
      alert(i18n.t('complete_onboarding_first') || "Please complete onboarding first!");
      return;
    }
    setStep('collective_sale');
  };

  const handleVoiceResult = async (result) => {
    console.log("Voice Result:", result);
    
    // Normalize data structure
    const intent = result.intent;
    const text = result.text || result.transcript;
    const extractedData = result;

    if (!intent && !text) {
      return;
    }

    // 0. Onboarding Progress (Partial)
    if (step === 'onboarding_voice') {
        if (extractedData.profile) {
            console.log("Onboarding Progress:", extractedData.profile);
            setTempProfile(extractedData.profile);
        }
    }

    // 1. Direct Answer Intents (Weather, Price) - Stay in Voice Overlay
    if (intent === 'weather' || intent === 'market_price') {
      setApiData({ ...extractedData, text: text });
      return;
    }

    // 2. Harvest Advice
    if (intent === 'harvest_advice') {
      if (extractedData.rag_context) {
        setApiData({ ...extractedData, text: text });
        return;
      }
      return;
    }

    // 3. Decision Support (Harvest Form result via Voice)
    if (intent === 'decision_support') {
        console.log("Decision Support Triggered:", extractedData);
        
        // Unwrap data if nested (extractedData.data contains the actual decision/scenarios)
        if (extractedData.data && extractedData.data.scenarios) {
             setApiData({ 
                ...extractedData.data, 
                intent: intent, 
                text: text,
                explanation: extractedData.response // Pass the LLM reasoning
             });
             setStep('results');
             setShowVoiceOverlay(false);
             return;
        } 
        
        // If scenarios are missing, it means we need more info (follow-up question)
        // So we stay in the overlay and let the fallback logic handle the text response
        // Fall through to fallback
    }

    // 4. Onboarding Complete
    if (intent === 'onboarding_complete') {
        const { profile } = extractedData;
        console.log("Onboarding Complete:", profile);
        
        setTempProfile(profile);
        setStep('confirm_details');
        setShowVoiceOverlay(false);
        return;
    }

    // 5. Fallback
    setApiData({ ...extractedData, text: text });
  };

  const handleFormSubmit = async (data) => {
    setHarvestData(data);
    setStep('processing');
    setError(null);

    try {
      const response = await axios.post('/api/v1/harvest/decision', data);
      
      // Add artificial delay for UX
      setTimeout(() => {
        setApiData(response.data);
        setStep('results');
      }, 2000);
      
    } catch (err) {
      console.error("API Error:", err);
      setError(t('process_error'));
      setStep('form'); 
    }
  };

  const handleBack = () => {
    setStep('home');
    setApiData(null);
    setHarvestData(null);
  };

  return (
    <div className="flex justify-center items-center min-h-screen bg-slate-100 dark:bg-slate-950 p-4 font-sans transition-colors duration-300">
      <MobileFrame 
        darkMode={darkMode} 
        toggleDarkMode={toggleDarkMode}
        onHome={() => hasOnboarded && setStep('home')}
        onNews={handleOpenNews}
        onProfile={handleOpenProfile}
        onHarvest={handleOpenHarvest}
        hasOnboarded={hasOnboarded}
      >
        <OfflineIndicator />
        <AnimatePresence mode="wait">
        
        {step === 'loading' && (
            <Motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center justify-center h-full bg-white dark:bg-slate-900"
            >
                <div className="w-10 h-10 border-4 border-green-500 border-t-transparent rounded-full animate-spin"></div>
            </Motion.div>
        )}

        {step === 'welcome' && (
          <Motion.div 
            key="welcome"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="h-full w-full"
          >
            <Welcome onComplete={handleWelcomeComplete} initialStep={welcomeInitialStep} />
          </Motion.div>
        )}

        {step === 'onboarding_form' && (
            <Motion.div
                key="onboarding_form"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="h-full w-full"
            >
                <ManualOnboardingForm 
                    profile={tempProfile || userProfile} 
                    onSubmit={handleManualSubmit}
                    isProcessing={false}
                    onBack={() => {
                        setWelcomeInitialStep('mode');
                        setStep('welcome');
                    }}
                />
            </Motion.div>
        )}

        {step === 'onboarding_voice' && (
            <Motion.div
                key="onboarding_voice"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="h-full w-full flex items-center justify-center bg-slate-50 dark:bg-slate-900"
            >
                <div className="text-center p-6">
                    <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
                        <span className="text-3xl">🎙️</span>
                    </div>
                    <h2 className="text-xl font-bold text-slate-800 dark:text-white mb-2">
                        {t('listening')}
                    </h2>
                    <p className="text-slate-500 dark:text-slate-400">
                        {t('listening_prompt')}
                    </p>
                </div>
            </Motion.div>
        )}

        {step === 'confirm_details' && (
            <Motion.div
                key="confirm_details"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="h-full w-full"
            >
                <ConfirmDetails 
                    profile={tempProfile} 
                    onConfirm={handleConfirmDetails}
                    onEdit={handleEditDetails}
                    onBack={handleEditDetails}
                />
            </Motion.div>
        )}

        {step === 'set_pin' && (
            <Motion.div
                key="set_pin"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="h-full w-full"
            >
                <SetPin onSetPin={handleSetPin} onBack={handleBackFromSetPin} />
            </Motion.div>
        )}

        {step === 'login' && (
          <Motion.div 
            key="login"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.3 }}
            className="h-full w-full"
          >
            <Login onLogin={handleLogin} onReset={handleReset} />
          </Motion.div>
        )}

        {step === 'home' && (
          <Motion.div 
            key="home"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="h-full w-full"
          >
            <Home 
                onStart={handleStart} 
                onOpenNews={handleOpenNews}
                onOpenMarket={handleOpenMarket}
                onOpenProfile={handleOpenProfile}
                onOpenHarvest={handleOpenHarvest}
                onOpenCollectiveSale={handleOpenCollectiveSale}
                darkMode={darkMode}
                toggleDarkMode={toggleDarkMode}
                userName={userProfile?.name}
                userProfile={userProfile}
            />
          </Motion.div>
        )}

        {step === 'form' && (
          <Motion.div 
            key="form"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="h-full w-full"
          >
            <HarvestForm 
                userProfile={userProfile}
                onSubmit={handleFormSubmit} 
                onCancel={handleBack} 
                onVoice={() => setShowVoiceOverlay(true)}
            />
          </Motion.div>
        )}

        {step === 'processing' && (
          <Motion.div 
            key="processing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="h-full w-full"
          >
            <Processing />
          </Motion.div>
        )}

        {step === 'results' && (
          <Motion.div 
            key="results"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="h-full w-full"
          >
            <Results 
                data={apiData} 
                harvestData={harvestData}
                userProfile={userProfile}
                onBack={handleBack}
                onVoice={() => setIsVoiceOpen(true)}
            />
          </Motion.div>
        )}

        {step === 'market_news' && (
          <Motion.div 
            key="market_news"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="h-full w-full"
          >
            <MarketNews 
                onBack={handleBack} 
                onVoice={() => setShowVoiceOverlay(true)}
                userProfile={userProfile}
            />
          </Motion.div>
        )}

        {step === 'market_prices' && (
          <Motion.div 
            key="market_prices"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="h-full w-full"
          >
            <MarketPrices 
                onClose={handleBack} 
                userProfile={userProfile}
                onVoice={() => setShowVoiceOverlay(true)}
            />
          </Motion.div>
        )}

        {step === 'collective_sale' && (
          <Motion.div 
            key="collective_sale"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="h-full w-full"
          >
            <CollectiveSale 
                onBack={handleBack}
                darkMode={darkMode}
            />
          </Motion.div>
        )}

        {step === 'profile' && userProfile && (
          <Motion.div 
            key="profile"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="h-full w-full"
          >
            <Profile 
              onBack={handleBack}
              darkMode={darkMode}
              toggleDarkMode={toggleDarkMode}
              onLanguageChange={handleLanguageChange}
              voiceSettings={voiceSettings}
              onVoiceSettingsChange={setVoiceSettings}
              userProfile={userProfile}
            />
          </Motion.div>
        )}

      </AnimatePresence>

      </MobileFrame>
      
      <VoiceOverlay 
        isOpen={showVoiceOverlay} 
        mode={step === 'onboarding_voice' ? (preferredMode === 'manual' ? 'onboarding_manual' : 'onboarding') : 'voice'}
        onClose={() => {
            // First close the overlay to trigger cleanup, then navigate after a small delay
            setShowVoiceOverlay(false);
            
            // Use setTimeout to ensure audio cleanup completes before navigation
            setTimeout(() => {
                if (step === 'onboarding_voice') {
                    setWelcomeInitialStep('mode');
                    setStep('welcome');
                }
            }, 100); // Small delay to ensure audio cleanup
        }}
        onResult={handleVoiceResult}
        darkMode={darkMode}
        toggleDarkMode={toggleDarkMode}
        voiceSettings={voiceSettings}
        userProfile={tempProfile || userProfile}
      />
    </div>
  );
}

export default App;
