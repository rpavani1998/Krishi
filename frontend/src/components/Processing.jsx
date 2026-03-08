import React from 'react';
import { motion as Motion } from 'framer-motion';

const Processing = () => {
  return (
    <div className="flex-1 bg-slate-50 dark:bg-slate-900 flex flex-col items-center justify-center p-8 relative overflow-hidden h-full transition-colors duration-300">
      {/* Background Glow - Lighter for Light Mode */}
      <div className="absolute top-1/4 left-1/4 w-32 h-32 bg-green-200 dark:bg-green-900/30 rounded-full blur-[60px] opacity-40 animate-pulse"></div>
      <div className="absolute bottom-1/4 right-1/4 w-32 h-32 bg-blue-200 dark:bg-blue-900/30 rounded-full blur-[60px] opacity-40 animate-pulse delay-1000"></div>

      {/* Spinner */}
      <Motion.div 
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        className="w-16 h-16 border-4 border-green-500 border-t-transparent rounded-full mb-6 z-10"
      />

      <h2 className="text-2xl font-bold text-slate-800 dark:text-white mb-2 z-10">విశ్లేషిస్తున్నాం...</h2>
      <p className="text-slate-500 dark:text-slate-400 text-sm z-10">మార్కెట్ ధరలు మరియు వాతావరణం పరిశీలిస్తున్నాం</p>

      <div className="mt-8 bg-white/80 dark:bg-slate-800/80 rounded-2xl p-4 text-left border border-slate-200 dark:border-slate-700 shadow-sm backdrop-blur-sm z-10 w-full max-w-xs transition-colors duration-300">
        <div className="flex items-center space-x-3 mb-3">
          <div className="w-5 h-5 rounded-full bg-green-100 dark:bg-green-900/50 border border-green-200 dark:border-green-800 flex items-center justify-center">
            <svg className="w-3 h-3 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <span className="text-slate-700 dark:text-slate-300 text-sm font-medium">డేటా సేకరించబడింది</span>
        </div>
        <div className="flex items-center space-x-3">
          <Motion.div 
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-5 h-5 rounded-full border-2 border-slate-300 dark:border-slate-600 border-t-green-500"
          />
          <span className="text-slate-500 dark:text-slate-400 text-sm">రిస్క్ అంచనా వేస్తున్నాం...</span>
        </div>
      </div>
    </div>
  );
};

export default Processing;
