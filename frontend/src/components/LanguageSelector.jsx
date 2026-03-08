import React, { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { ChevronDown, Check } from 'lucide-react';

const LanguageSelector = ({ variant = 'default', onSelect, align = 'right' }) => {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const languages = [
    { code: 'en', label: 'English', native: 'English' },
    { code: 'te', label: 'Telugu', native: 'తెలుగు' },
    { code: 'hi', label: 'Hindi', native: 'हिंदी' }
  ];

  const currentLang = languages.find(l => l.code === i18n.language) || languages[0];

  if (variant === 'large') {
    return (
      <div className="w-full max-w-xs space-y-3">
        {languages.map((lang) => (
          <button
            key={lang.code}
            onClick={() => {
              i18n.changeLanguage(lang.code);
              if (onSelect) onSelect(lang.code);
            }}
            className={`w-full flex items-center justify-between p-4 rounded-xl border-2 transition-all ${
              i18n.language === lang.code
                ? 'border-green-500 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:border-green-200 dark:hover:border-green-800'
            }`}
          >
            <span className="font-medium text-lg">{lang.native}</span>
            <span className="text-sm opacity-70">{lang.label}</span>
            {i18n.language === lang.code && <Check className="w-5 h-5 text-green-600" />}
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 bg-slate-100 dark:bg-slate-700 rounded-full px-4 py-2 transition-all hover:bg-slate-200 dark:hover:bg-slate-600 border border-transparent hover:border-slate-300 dark:hover:border-slate-500"
      >
        <span className="text-sm font-bold text-slate-700 dark:text-slate-200">
          {currentLang.label}
        </span>
        <ChevronDown className={`w-4 h-4 text-slate-500 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div
          className={`absolute top-full mt-2 w-40 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-100 dark:border-slate-700 overflow-hidden z-50 animate-in fade-in zoom-in-95 duration-100 ${align === 'left' ? 'left-0' : 'right-0'}`}
        >
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => {
                i18n.changeLanguage(lang.code);
                setIsOpen(false);
                if (onSelect) onSelect(lang.code);
              }}
              className={`w-full text-left px-4 py-3 text-sm font-medium transition-colors flex justify-between items-center ${
                i18n.language === lang.code
                  ? 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400'
                  : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'
              }`}
            >
              <span>{lang.label}</span>
              {i18n.language === lang.code && <Check className="w-4 h-4" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default LanguageSelector;
