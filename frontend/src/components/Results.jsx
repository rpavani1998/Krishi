import React, { useState } from 'react';
import { ArrowLeft, TrendingUp, CloudRain, AlertTriangle, Truck, DollarSign, MapPin, Info, Mic, Bell, MessageSquare, Clock, ShieldCheck, ChevronRight } from 'lucide-react';
import { motion as Motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';

const Results = ({ data, harvestData, userProfile, onBack, onVoice }) => {
  const { t } = useTranslation();
  const [view, setView] = useState('overview'); // 'overview' | 'detail'
  const [selectedScenarioId, setSelectedScenarioId] = useState(null);

  if (!data || !data.scenarios) return null;

  // Extract scenarios
  const sellNow = data.scenarios.find(s => s.id === 'sell_now');
  const wait48h = data.scenarios.find(s => s.id === 'wait_48h') || data.scenarios.find(s => s.id === 'wait_24h');
  
  // If we only have sell_now, we can't show the comparison properly, but we'll try.
  const scenarios = [sellNow, wait48h].filter(Boolean);

  // Helper to format currency
  const formatCurrency = (val) => `₹${val?.toLocaleString('en-IN') || '0'}`;

  // Helper to get price range string
  const getPriceRange = (scenario) => {
      if (!scenario || !scenario.expected_revenue_range) return "₹0 - ₹0";
      // Assuming range is total revenue, but UI shows per kg price. 
      // We'll simulate per kg price by dividing by quantity if available, else show revenue.
      const quantity = harvestData?.quantity || 100; // Default to 100kg if missing
      const minPrice = Math.round(scenario.expected_revenue_range[0] / quantity);
      const maxPrice = Math.round(scenario.expected_revenue_range[1] / quantity);
      return `₹${minPrice}-${maxPrice}/kg`;
  };
  
  // Calculate Upside (Profit difference)
  const calculateUpside = () => {
      if (!sellNow || !wait48h) return 0;
      const sellAvg = (sellNow.expected_revenue_range[0] + sellNow.expected_revenue_range[1]) / 2;
      const waitAvg = (wait48h.expected_revenue_range[0] + wait48h.expected_revenue_range[1]) / 2;
      return Math.round(waitAvg - sellAvg);
  };
  
  const upsideValue = calculateUpside();
  const isUpsidePositive = upsideValue > 0;

  // Render Header
  const renderHeader = () => (
    <div className="flex items-center p-4 border-b bg-white dark:bg-slate-800 dark:border-slate-700 sticky top-0 z-10">
      <button 
        onClick={() => view === 'detail' ? setView('overview') : onBack()} 
        className="p-2 -ml-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
      >
        <ArrowLeft className="w-6 h-6 text-slate-700 dark:text-slate-200" />
      </button>
      <div className="ml-2 flex flex-col">
          <h1 className="text-xl font-bold text-slate-800 dark:text-white leading-tight">
            {view === 'overview' ? t('two_options_available') || "Two Options Available" : t('if_you_wait_48h') || "If you wait 48 hours..."}
          </h1>
          {userProfile?.name && view === 'overview' && (
              <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                  {t('for') || "For"} {userProfile.name} • {harvestData?.crop || userProfile.primary_crop || "Crop"}
              </span>
          )}
      </div>
    </div>
  );

  // Render Overview (Screen 1)
  const renderOverview = () => (
    <Motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
        className="p-4 space-y-4"
    >
      {/* Personalized Advice Card */}
      {data?.explanation && (
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-2xl p-4 border border-green-100 dark:border-green-900 shadow-sm relative overflow-hidden">
            <div className="flex items-start space-x-3 relative z-10">
                <div className="bg-white dark:bg-slate-800 p-2 rounded-full shadow-sm">
                    <MessageSquare className="w-5 h-5 text-green-600 dark:text-green-400" />
                </div>
                <div className="flex-1">
                    <h3 className="font-bold text-slate-800 dark:text-white text-sm mb-1">
                        {t('krishi_advice') || "Krishi's Advice"}
                    </h3>
                    <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                        {data.explanation}
                    </p>
                </div>
            </div>
            {/* Decorative background element */}
            <div className="absolute -bottom-4 -right-4 w-24 h-24 bg-green-100 dark:bg-green-800/20 rounded-full blur-2xl"></div>
        </div>
      )}

      {/* Sell Now Card */}
      {sellNow && (
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-5 shadow-sm border border-slate-200 dark:border-slate-700 relative overflow-hidden">
            <div className="flex justify-between items-start mb-4">
                <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                    <h3 className="font-bold text-lg text-slate-800 dark:text-white">{t('sell_now') || "Sell Now"}</h3>
                </div>
                <span className="bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-xs font-bold px-3 py-1 rounded-full">
                    {t('low_risk') || "Low Risk"}
                </span>
            </div>
            
            <div className="mb-4">
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">{t('estimated_price') || "Estimated Price"}</p>
                <div className="flex items-baseline space-x-2">
                    <span className="text-3xl font-bold text-slate-900 dark:text-white">{getPriceRange(sellNow)}</span>
                    <TrendingUp className="w-5 h-5 text-green-500" />
                </div>
            </div>

            <button className="w-full py-3 rounded-xl border border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-300 font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">
                {t('see_details') || "See Details"}
            </button>
        </div>
      )}

      {/* Wait Card */}
      {wait48h && (
        <div className="bg-orange-50 dark:bg-orange-900/10 rounded-2xl p-5 shadow-sm border border-orange-200 dark:border-orange-800 relative overflow-hidden ring-1 ring-orange-500/20">
             {/* Tag */}
             <div className="absolute top-0 right-0 bg-orange-500 text-white text-[10px] font-bold px-3 py-1 rounded-bl-xl shadow-sm">
                {t('high_risk') || "High Risk"}
             </div>

            <div className="flex justify-between items-start mb-4">
                <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                    <h3 className="font-bold text-lg text-slate-800 dark:text-white">
                        {wait48h.id === 'wait_48h' ? (t('wait_48h') || "Wait 48 Hours") : (t('wait_24h') || "Wait 24 Hours")}
                    </h3>
                </div>
            </div>
            
            <div className="mb-2">
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-1">{t('estimated_price') || "Estimated Price"}</p>
                <div className="flex items-center justify-between">
                    <span className="text-3xl font-bold text-slate-900 dark:text-white">{getPriceRange(wait48h)}</span>
                    {isUpsidePositive && (
                        <span className="bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 text-xs font-bold px-2 py-1 rounded-lg">
                            +{formatCurrency(upsideValue)} {t('profit') || "Profit"}?
                        </span>
                    )}
                </div>
            </div>

            <p className="text-xs text-slate-600 dark:text-slate-400 mb-4 flex items-center">
                {t('but_rain_chance') || "But chance of rain"} (40%)
            </p>

            <button 
                onClick={() => handleAnalyzeRisk(wait48h.id)}
                className="w-full py-3 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold shadow-md shadow-orange-500/20 transition-all active:scale-95"
            >
                {t('analyze_risk') || "Analyze Risk"}
            </button>
        </div>
      )}
    </Motion.div>
  );

  // Render Detail (Screen 2)
  const renderDetail = () => (
    <Motion.div 
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 20 }}
        className="p-4 space-y-6"
    >
        {/* Upside Section */}
        <div>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">{t('upside') || "UPSIDE"} (PROFIT)</h3>
            <div className="bg-green-50 dark:bg-green-900/10 rounded-2xl p-4 border border-green-100 dark:border-green-900 flex justify-between items-center">
                <div>
                    <h4 className="font-bold text-slate-800 dark:text-white text-lg">{t('price_increase') || "Price Increase"}</h4>
                    <p className="text-xs text-green-700 dark:text-green-400">{t('demand_increasing') || "Demand is increasing"}</p>
                </div>
                <div className="text-right">
                    <span className="text-xl font-bold text-green-600 dark:text-green-400">+{formatCurrency(upsideValue)}</span>
                    <p className="text-[10px] text-slate-500">{t('total_profit') || "Total Profit"}</p>
                </div>
            </div>
        </div>

        {/* Downside Section */}
        <div>
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">{t('downside') || "DOWNSIDE"} (RISK)</h3>
            <div className="space-y-3">
                {/* Weather Risk */}
                <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700 shadow-sm">
                    <div className="flex justify-between items-center mb-2">
                        <div className="flex items-center space-x-2">
                            <CloudRain className="w-5 h-5 text-blue-500" />
                            <span className="font-bold text-slate-800 dark:text-white">{t('rain') || "Rain"}</span>
                        </div>
                        <span className="bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 text-xs font-bold px-2 py-0.5 rounded">
                            {t('medium_risk') || "Medium"}
                        </span>
                    </div>
                    {/* Progress Bar */}
                    <div className="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-2 mb-1">
                        <div className="bg-orange-500 h-2 rounded-full w-[40%]"></div>
                    </div>
                    <p className="text-xs text-right text-slate-500">40% {t('chance_tomorrow_night') || "chance (tomorrow night)"}</p>
                </div>

                {/* Storage Risk */}
                <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700 shadow-sm">
                    <div className="flex justify-between items-center mb-2">
                        <div className="flex items-center space-x-2">
                            <Clock className="w-5 h-5 text-red-500" />
                            <span className="font-bold text-slate-800 dark:text-white">{t('storage_capability') || "Storage Capability"}</span>
                        </div>
                        <span className="bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-xs font-bold px-2 py-0.5 rounded">
                            {t('safe') || "Safe"}
                        </span>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-400">
                        {t('tomatoes_firm_msg') || "Your tomatoes are firm, will last 3 days."}
                    </p>
                </div>
            </div>
        </div>

        {/* Actions */}
        <div className="flex space-x-3 pt-4">
            <button className="flex-1 py-3 px-4 rounded-xl border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-700 dark:text-white font-medium shadow-sm flex items-center justify-center space-x-2 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">
                <Bell className="w-4 h-4" />
                <span>{t('reminder') || "Reminder"}</span>
            </button>
            <button className="flex-1 py-3 px-4 rounded-xl bg-slate-900 dark:bg-slate-700 text-white font-medium shadow-lg shadow-slate-900/20 flex items-center justify-center space-x-2 hover:bg-slate-800 dark:hover:bg-slate-600 transition-colors">
                <MessageSquare className="w-4 h-4" />
                <span>{t('send_sms') || "Send SMS"}</span>
            </button>
        </div>
    </Motion.div>
  );

  return (
    <div className="h-full w-full relative bg-slate-50 dark:bg-slate-900 overflow-y-auto pb-24">
      {renderHeader()}
      
      <AnimatePresence mode="wait">
        {view === 'overview' ? (
            <div key="overview">{renderOverview()}</div>
        ) : (
            <div key="detail">{renderDetail()}</div>
        )}
      </AnimatePresence>

      {/* Persistent Voice Bubble */}
      <Motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        whileTap={{ scale: 0.9 }}
        onClick={onVoice}
        className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-green-500 to-emerald-600 rounded-full shadow-lg shadow-green-500/40 flex items-center justify-center z-50 group"
      >
        <div className="absolute inset-0 bg-white rounded-full opacity-0 group-hover:opacity-20 transition-opacity" />
        <Mic className="w-6 h-6 text-white" />
        
        {/* Pulse effect */}
        <span className="absolute -inset-1 rounded-full border border-green-400 opacity-0 group-hover:opacity-100 animate-ping" />
      </Motion.button>
    </div>
  );
};

export default Results;
