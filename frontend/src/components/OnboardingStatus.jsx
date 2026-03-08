import React from 'react';
import { User, MapPin, Sprout, Ruler, Phone, CheckCircle2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const OnboardingStatus = ({ profile }) => {
  console.log("OnboardingStatus rendered with profile:", profile);
  const { t } = useTranslation();
  const tt = (key, def) => {
    const val = t(key);
    return val && val !== key ? val : def;
  };

  const fields = [
    { key: 'name', icon: User, label: tt('name', 'Name') },
    { key: 'location', icon: MapPin, label: tt('location', 'Location') },
    { key: 'primary_crop', icon: Sprout, label: tt('crop', 'Crop') },
    { key: 'farm_size_acres', icon: Ruler, label: tt('farm_size', 'Farm Size') },
    { key: 'mobile_number', icon: Phone, label: tt('mobile_number', 'Mobile Number') }
  ];

  const completedCount = fields.filter(f => profile && profile[f.key]).length;
  const progress = (completedCount / fields.length) * 100;

  return (
    <div className="w-full h-full p-4 flex flex-col">
      <div className="mb-3 shrink-0">
        <h2 className="text-lg font-bold text-slate-800 dark:text-white leading-tight">
          {tt('setup_profile', "Set up your profile")}
        </h2>
        <div className="flex items-center gap-2 mt-2">
            <div className="flex-1 h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                <div 
                style={{ width: `${progress}%`, transition: 'width 0.5s ease-out' }}
                className="h-full bg-green-500"
                />
            </div>
            <span className="text-xs text-slate-400 font-medium">{Math.round(progress)}%</span>
        </div>
      </div>

      {/* Fields - Compact List */}
      <div className=" flex-1 pr-1">
        {fields.map((field, index) => {
          const isCompleted = profile && profile[field.key];
          const firstIncompleteIndex = fields.findIndex(f => !profile || !profile[f.key]);
          const isActive = !isCompleted && index === firstIncompleteIndex;
          
          return (
            <div 
              key={field.key}
              className={`p-2.5 rounded-lg border transition-all duration-300 flex items-center gap-3 ${
                isCompleted 
                  ? 'border-green-500/20 bg-green-50/50 dark:bg-green-900/10' 
                  : isActive
                    ? 'border-green-500 bg-white dark:bg-slate-800 shadow-sm ring-1 ring-green-500/20'
                    : 'border-transparent bg-white/60 dark:bg-slate-800/60 opacity-70'
              }`}
            >
              <div className={`p-1.5 rounded-full shrink-0 ${
                isCompleted ? 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400' : 
                isActive ? 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400' :
                'bg-slate-200 dark:bg-slate-700 text-slate-400'
              }`}>
                <field.icon className="w-4 h-4" />
              </div>
              
              <div className="flex-1 min-w-0 flex items-center justify-between">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  {field.label}
                </span>
                
                {isCompleted ? (
                    <span className="text-sm font-bold text-slate-900 dark:text-white truncate max-w-[50%] text-right">
                        {profile[field.key]}
                    </span>
                ) : isActive ? (
                    <span className="text-xs font-medium text-green-600 dark:text-green-400 animate-pulse">
                        {tt('asking_now', "Asking now...")}
                    </span>
                ) : (
                    <span className="text-slate-300 dark:text-slate-600 text-xs">---</span>
                )}
              </div>
              
              {isCompleted && <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" />}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default OnboardingStatus;
