import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { motion as Motion } from 'framer-motion';
import { ArrowLeft, User, MapPin, Globe, Moon, Sun, ChevronRight, LogOut, Volume2, Mic, Activity } from 'lucide-react';
import LanguageSelector from './LanguageSelector';

const Profile = ({ onBack, darkMode, toggleDarkMode, onLanguageChange, voiceSettings, onVoiceSettingsChange, userProfile }) => {
  const { t } = useTranslation();
  const [activeSection, setActiveSection] = useState('main');

  const handleVoiceChange = (key, value) => {
      onVoiceSettingsChange({ ...voiceSettings, [key]: value });
  };

  // Voice Settings Sub-Page
  if (activeSection === 'voice') {
      return (
        <div className="flex flex-col h-full bg-gray-50 dark:bg-slate-950 transition-colors duration-300">
            <div className="px-5 py-4 bg-white dark:bg-slate-900 border-b border-gray-100 dark:border-slate-800 flex items-center space-x-3 shadow-sm sticky top-0 z-10">
                <button 
                onClick={() => setActiveSection('main')}
                className="p-2 -ml-2 rounded-full hover:bg-gray-100 dark:hover:bg-slate-800 text-gray-600 dark:text-gray-300 transition-colors"
                >
                <ArrowLeft className="w-6 h-6" />
                </button>
                <h1 className="text-xl font-bold text-gray-800 dark:text-white">{t('voice_settings')}</h1>
            </div>

            <div className="p-5">
                <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-800 overflow-hidden p-4">
                    <div className="flex items-center mb-6 text-gray-800 dark:text-white font-medium">
                        <Mic className="w-5 h-5 mr-3 text-purple-500" />
                        {t('customize_agent_voice')}
                    </div>
                    
                    {/* Accent / Region */}
                    <div className="mb-6">
                        <div className="flex justify-between text-sm text-gray-600 dark:text-gray-300 mb-2">
                            <span>{t('accent_region')}</span>
                        </div>
                        <select 
                            value={voiceSettings?.accent || 'co.in'}
                            onChange={(e) => handleVoiceChange('accent', e.target.value)}
                            className="w-full p-2 bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-500 dark:text-white"
                        >
                            <option value="co.in">{t('indian_english')}</option>
                            <option value="com">{t('american_english')}</option>
                            <option value="co.uk">{t('british_english')}</option>
                            <option value="com.au">{t('australian_english')}</option>
                        </select>
                    </div>

                    {/* Speed */}
                    <div className="mb-6">
                        <div className="flex justify-between text-sm text-gray-600 dark:text-gray-300 mb-2">
                            <span>{t('speed_rate')}</span>
                            <span className="font-mono bg-gray-100 dark:bg-slate-800 px-2 py-0.5 rounded text-xs">{voiceSettings?.speed || 1.0}x</span>
                        </div>
                        <input 
                            type="range" 
                            min="0.5" 
                            max="2.0" 
                            step="0.1"
                            value={voiceSettings?.speed || 1.0}
                            onChange={(e) => handleVoiceChange('speed', parseFloat(e.target.value))}
                            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-slate-700 accent-green-600"
                        />
                        <div className="flex justify-between text-xs text-gray-400 mt-1">
                            <span>{t('slow')}</span>
                            <span>{t('normal')}</span>
                            <span>{t('fast')}</span>
                        </div>
                    </div>

                    {/* Pitch */}
                    <div className="mb-6">
                        <div className="flex justify-between text-sm text-gray-600 dark:text-gray-300 mb-2">
                            <span>{t('pitch_tone')}</span>
                            <span className="font-mono bg-gray-100 dark:bg-slate-800 px-2 py-0.5 rounded text-xs">{voiceSettings?.pitch || 1.0}</span>
                        </div>
                        <input 
                            type="range" 
                            min="0.5" 
                            max="2.0" 
                            step="0.1"
                            value={voiceSettings?.pitch || 1.0}
                            onChange={(e) => handleVoiceChange('pitch', parseFloat(e.target.value))}
                            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-slate-700 accent-purple-600"
                        />
                         <div className="flex justify-between text-xs text-gray-400 mt-1">
                            <span>{t('deep')}</span>
                            <span>{t('normal')}</span>
                            <span>{t('high')}</span>
                        </div>
                    </div>

                    {/* Volume */}
                    <div className="mb-2">
                        <div className="flex justify-between text-sm text-gray-600 dark:text-gray-300 mb-2">
                            <span>{t('volume')}</span>
                            <span className="font-mono bg-gray-100 dark:bg-slate-800 px-2 py-0.5 rounded text-xs">{Math.round((voiceSettings?.volume || 1.0) * 100)}%</span>
                        </div>
                        <input 
                            type="range" 
                            min="0.0" 
                            max="1.0" 
                            step="0.1"
                            value={voiceSettings?.volume || 1.0}
                            onChange={(e) => handleVoiceChange('volume', parseFloat(e.target.value))}
                            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-slate-700 accent-blue-600"
                        />
                    </div>
                </div>
            </div>
        </div>
      );
  }

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-slate-950 transition-colors duration-300">
      {/* Header */}
      <div className="px-5 py-4 bg-white dark:bg-slate-900 border-b border-gray-100 dark:border-slate-800 flex items-center space-x-3 shadow-sm sticky top-0 z-10">
        <button 
          onClick={onBack}
          className="p-2 -ml-2 rounded-full hover:bg-gray-100 dark:hover:bg-slate-700 text-gray-600 dark:text-gray-300 transition-colors"
        >
          <ArrowLeft className="w-6 h-6" />
        </button>
        <h1 className="text-xl font-bold text-gray-800 dark:text-white">{t('profile')}</h1>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        {/* User Info Card */}
        <Motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white dark:bg-slate-900 p-5 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-800 flex items-center space-x-4"
        >
          <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center text-green-600 dark:text-green-400">
            <User className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-gray-800 dark:text-white">{userProfile?.name || t('welcome_user')}</h2>
            <div className="flex items-center text-gray-500 dark:text-gray-400 text-sm mt-1">
              <MapPin className="w-3.5 h-3.5 mr-1" />
              <span>{userProfile?.location || 'Madanapalle, AP'}</span>
            </div>
          </div>
        </Motion.div>

        {/* Settings Section */}
        <Motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="space-y-4"
        >
          <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider ml-1">{t('app_settings')}</h3>
          
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-800">
            {/* Language Selector */}
            <div className="p-4 border-b border-gray-100 dark:border-slate-800 rounded-t-2xl">
              <div className="flex items-center mb-3 text-gray-800 dark:text-white font-medium">
                <Globe className="w-5 h-5 mr-3 text-blue-500" />
                Language / భాష / भाषा
              </div>
              <div className="flex items-center justify-between relative">
                <LanguageSelector onSelect={onLanguageChange} align="left" />
              </div>
            </div>

            {/* Voice Settings Button */}
            <button 
              onClick={() => setActiveSection('voice')}
              className="w-full p-4 flex items-center justify-between border-b border-gray-100 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors"
            >
              <div className="flex items-center text-gray-800 dark:text-white font-medium">
                <Volume2 className="w-5 h-5 mr-3 text-purple-500" />
                {t('voice_settings')}
              </div>
              <ChevronRight className="w-5 h-5 text-gray-400" />
            </button>

            {/* Dark Mode Toggle */}
            <button 
              onClick={toggleDarkMode}
              className="w-full p-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors rounded-b-2xl"
            >
              <div className="flex items-center text-gray-800 dark:text-white font-medium">
                {darkMode ? <Moon className="w-5 h-5 mr-3 text-purple-500" /> : <Sun className="w-5 h-5 mr-3 text-amber-500" />}
                {t('dark_mode')}
              </div>
              <div className={`w-12 h-6 rounded-full p-1 transition-colors ${darkMode ? 'bg-green-600' : 'bg-gray-300'}`}>
                <div className={`w-4 h-4 rounded-full bg-white shadow-sm transform transition-transform ${darkMode ? 'translate-x-6' : 'translate-x-0'}`} />
              </div>
            </button>
          </div>
        </Motion.div>

        {/* Other Options */}
        <Motion.div 
           initial={{ opacity: 0, y: 10 }}
           animate={{ opacity: 1, y: 0 }}
           transition={{ delay: 0.2 }}
           className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-gray-100 dark:border-slate-800 overflow-hidden"
        >
            <button className="w-full p-4 flex items-center justify-between border-b border-gray-100 dark:border-slate-800 hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors text-left">
                <span className="text-gray-800 dark:text-white font-medium">{t('help_support')}</span>
                <ChevronRight className="w-5 h-5 text-gray-400" />
            </button>
            <button className="w-full p-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors text-left text-red-500">
                <div className="flex items-center font-medium">
                    <LogOut className="w-5 h-5 mr-3" />
                    {t('sign_out')}
                </div>
            </button>
        </Motion.div>
        
        <div className="text-center text-xs text-gray-400 py-4">
            {t('version_footer')}
        </div>
      </div>
    </div>
  );
};

export default Profile;
