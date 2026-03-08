import React from 'react';

const MobileFrame = ({ children, className = "", darkMode }) => {
  return (
    <div className={`relative w-[340px] h-[720px] bg-gray-900 rounded-[40px] shadow-2xl flex flex-col shrink-0 ring-1 ring-black/5 dark:ring-white/20 ${className}`}>
      {/* Notch */}
      <div className="absolute top-[12px] left-1/2 -translate-x-1/2 w-[140px] h-[28px] bg-gray-900 rounded-b-2xl z-[200] pointer-events-none"></div>
      
      {/* Screen Area - Inset by 12px to simulate bezel */}
      <div className="absolute top-[12px] left-[12px] right-[12px] bottom-[12px] bg-slate-50 dark:bg-slate-900 rounded-[28px] overflow-hidden flex flex-col transition-colors duration-300 isolation-isolate">
        {/* Status Bar */}
        <div className="h-10 px-5 pt-2.5 flex justify-between items-center text-xs font-semibold text-gray-700 dark:text-gray-300 bg-white dark:bg-slate-900 z-[150] relative transition-colors duration-300">
          <span>9:41</span>
          <span>🔋 100%</span>
        </div>

        {/* Content */}
        <div className="flex-1 flex flex-col relative overflow-hidden bg-slate-50 dark:bg-slate-900 transition-colors duration-300">
          {children}
        </div>
      </div>
    </div>
  );
};

export default MobileFrame;
