import React, { useState } from 'react';
import { ArrowRight, TrendingUp, AlertTriangle, Check, ChevronDown, ChevronUp, DollarSign, CloudRain, Clock } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const HarvestDecision = ({ decision, onClose }) => {
  const { t } = useTranslation();
  const [expandedId, setExpandedId] = useState(null);

  if (!decision || !decision.scenarios) return null;

  const sellNow = decision.scenarios.find(s => s.id === 'sell_now');
  const waitScenarios = decision.scenarios.filter(s => s.id.startsWith('wait_'));
  
  // Prefer the recommended wait scenario, or the first one
  const recommendedWait = waitScenarios.find(s => s.tag === 'Recommended') || waitScenarios[0];

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const renderScenarioCard = (scenario, isRecommended) => {
    if (!scenario) return null;
    const isExpanded = expandedId === scenario.id;
    
    // Determine card styling based on tag/recommendation
    const isHighRisk = scenario.tag?.toLowerCase().includes('risk');
    const isHighReward = scenario.tag?.toLowerCase().includes('reward');
    const isSafe = scenario.tag?.toLowerCase().includes('safe');
    
    let borderColor = 'border-slate-200 dark:border-slate-700';
    let bgColor = 'bg-white dark:bg-slate-800';
    let tagColor = 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300';

    if (isRecommended) {
      borderColor = 'border-green-500 dark:border-green-400 ring-1 ring-green-500/20';
      bgColor = 'bg-green-50/50 dark:bg-green-900/10';
    }
    
    if (isHighRisk) tagColor = 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300';
    if (isHighReward) tagColor = 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300';
    if (isSafe) tagColor = 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300';
    if (scenario.tag === 'Recommended') tagColor = 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300';

    return (
      <div 
        key={scenario.id}
        className={`rounded-xl border ${borderColor} ${bgColor} p-4 transition-all duration-200 mb-3 relative overflow-hidden`}
        onClick={() => toggleExpand(scenario.id)}
      >
        {/* Recommendation Badge */}
        {isRecommended && (
          <div className="absolute top-0 right-0 bg-green-500 text-white text-xs font-bold px-2 py-1 rounded-bl-lg">
            {t('recommended') || 'RECOMMENDED'}
          </div>
        )}

        <div className="flex justify-between items-start mb-2">
          <div>
            <h3 className="font-bold text-slate-800 dark:text-white flex items-center">
              {scenario.title}
              {scenario.id === 'sell_now' && <DollarSign className="w-4 h-4 ml-1 text-slate-400" />}
              {scenario.id.startsWith('wait') && <Clock className="w-4 h-4 ml-1 text-slate-400" />}
            </h3>
            <div className={`text-xs font-medium px-2 py-0.5 rounded-full inline-block mt-1 ${tagColor}`}>
              {scenario.tag || 'Option'}
            </div>
          </div>
          <div className="text-right">
             <div className="text-lg font-bold text-slate-900 dark:text-white">
               ₹{Math.round(scenario.expected_revenue_range[1]).toLocaleString('en-IN')}
             </div>
             <div className="text-xs text-slate-500 dark:text-slate-400">
               ~₹{Math.round((scenario.expected_revenue_range[0] + scenario.expected_revenue_range[1])/2).toLocaleString('en-IN')} avg
             </div>
          </div>
        </div>

        {/* Upside / Downside Highlights */}
        <div className="space-y-1 mb-3">
            {scenario.upside && (
                <div className="flex items-center text-xs text-green-600 dark:text-green-400 font-medium">
                    <TrendingUp className="w-3 h-3 mr-1.5" />
                    {scenario.upside}
                </div>
            )}
            {scenario.downside && (
                <div className="flex items-center text-xs text-red-600 dark:text-red-400 font-medium">
                    <AlertTriangle className="w-3 h-3 mr-1.5" />
                    {scenario.downside}
                </div>
            )}
        </div>

        {/* Expandable Details */}
        {isExpanded && (
            <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-700/50 text-sm">
                <p className="text-slate-600 dark:text-slate-300 mb-2 leading-relaxed">
                    {scenario.description}
                </p>
                
                <div className="grid grid-cols-2 gap-2 mt-2">
                    <div className="bg-white/50 dark:bg-black/20 p-2 rounded border border-slate-100 dark:border-slate-700">
                        <span className="text-xs text-slate-500 block">Weather Risk</span>
                        <span className={`font-medium ${scenario.risk_assessment.weather === 'HIGH' ? 'text-red-600' : 'text-slate-700 dark:text-slate-300'}`}>
                            {scenario.risk_assessment.weather}
                        </span>
                    </div>
                    <div className="bg-white/50 dark:bg-black/20 p-2 rounded border border-slate-100 dark:border-slate-700">
                        <span className="text-xs text-slate-500 block">Price Trend</span>
                        <span className="font-medium text-slate-700 dark:text-slate-300">
                            {scenario.price_projection}
                        </span>
                    </div>
                </div>
            </div>
        )}
        
        <div className="flex justify-center mt-1">
            {isExpanded ? <ChevronUp className="w-4 h-4 text-slate-300" /> : <ChevronDown className="w-4 h-4 text-slate-300" />}
        </div>
      </div>
    );
  };

  return (
    <div className="w-full max-w-md mx-auto p-4 pb-24 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Header Section */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-800 dark:text-white mb-1">
          {t('decision_analysis') || 'Harvest Analysis'}
        </h2>
        <p className="text-slate-500 dark:text-slate-400 text-sm">
            {decision.weather_summary}
        </p>
      </div>

      {/* Primary Recommendation Banner */}
      {decision.recommendation && (
          <div className="mb-6 bg-gradient-to-r from-slate-800 to-slate-900 dark:from-slate-700 dark:to-slate-800 rounded-xl p-4 text-white shadow-lg shadow-slate-200 dark:shadow-none">
              <div className="flex items-center space-x-3 mb-2">
                  <div className="bg-white/20 p-1.5 rounded-full">
                      <Check className="w-4 h-4 text-white" />
                  </div>
                  <span className="font-bold text-sm tracking-wide uppercase opacity-90">
                      {t('krishi_recommends') || 'KRISHI RECOMMENDS'}
                  </span>
              </div>
              <p className="text-lg font-medium leading-tight">
                  {decision.recommendation === 'wait' 
                    ? (t('recommend_wait') || `Wait ${recommendedWait?.id.includes('48') ? '48h' : '24h'} for better prices`)
                    : (t('recommend_sell') || "Sell now to avoid risk")}
              </p>
          </div>
      )}

      {/* Cards */}
      <div className="space-y-2">
          {renderScenarioCard(sellNow, decision.recommendation === 'sell_now')}
          {renderScenarioCard(recommendedWait, decision.recommendation === 'wait')} 
      </div>

      <div className="mt-6 text-center">
        <p className="text-xs text-slate-400 dark:text-slate-500">
          {t('voice_tip_decision') || "Tap the microphone to ask specific questions about these options."}
        </p>
      </div>
    </div>
  );
};

export default HarvestDecision;
