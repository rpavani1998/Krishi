import React, { useState, useEffect } from 'react';
import { WifiOff } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { motion as Motion, AnimatePresence } from 'framer-motion';

const OfflineIndicator = () => {
  const { t } = useTranslation();
  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <AnimatePresence>
      {isOffline && (
        <Motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className="bg-red-500 text-white px-4 py-2 flex items-center justify-center text-xs font-medium z-[160] absolute top-[40px] left-0 right-0 shadow-md"
        >
          <WifiOff className="w-3.5 h-3.5 mr-2" />
          <span>{t('offline_mode')}</span>
        </Motion.div>
      )}
    </AnimatePresence>
  );
};

export default OfflineIndicator;
