import React, { useState, useEffect } from 'react';
import { ArrowLeft, MapPin, TrendingUp, TrendingDown, Minus, ExternalLink, Store, Tractor, ChevronDown, Mic } from 'lucide-react';
import { motion as Motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

const MarketPrices = ({ onClose, userProfile, onVoice }) => {
  const { t, i18n } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [selectedCrop, setSelectedCrop] = useState(userProfile?.primary_crop || 'Tomato');
  const [selectedLocation, setSelectedLocation] = useState(userProfile?.location || 'Andhra Pradesh');
  const [isLocationOpen, setIsLocationOpen] = useState(false);

  // Mock locations for exploration
  const availableLocations = [
      userProfile?.location || 'Andhra Pradesh',
      'Hyderabad, Telangana',
      'Guntur, Andhra Pradesh',
      'Krishna, Andhra Pradesh',
      'Warangal, Telangana',
      'Kolar, Karnataka',
      'Nashik, Maharashtra',
      'Nagpur, Maharashtra'
  ].filter((v, i, a) => v && a.indexOf(v) === i);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Parse location
        let state = 'Andhra Pradesh';
        let district = 'Krishna';
        
        if (selectedLocation) {
            const parts = selectedLocation.split(',').map(p => p.trim());
            if (parts.length > 1) {
                district = parts[0];
                state = parts[1];
            } else {
                // Treat single part as the primary location identifier (district or state)
                // This ensures "Hyderabad" is passed as district to the API, 
                // which ceda_service uses as the location lookup key
                district = parts[0];
                state = ''; 
            }
        }

        const response = await axios.get('/api/v1/market/prices', {
          params: {
            commodity: selectedCrop,
            state: state,
            district: district,
            language: i18n.language
          }
        });

        if (response.data) {
          setData(response.data);
        }
      } catch (error) {
        console.error("Error fetching market data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedCrop, selectedLocation, i18n.language]);

  const getTrendIcon = (trend) => {
    if (trend === 'rising' || trend === 'up' || trend === 'RISING') return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (trend === 'falling' || trend === 'down' || trend === 'FALLING') return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-slate-400" />;
  };

  // Mock farms data (since API doesn't provide this yet)
  const nearbyFarms = [
      { name: "Local Farm", distance: "2 km", crop: selectedCrop, price: data?.current_price ? Math.round(data.current_price/100 * 0.95) : 0, unit: "kg" },
      { name: "Green Acres", distance: "5 km", crop: selectedCrop, price: data?.current_price ? Math.round(data.current_price/100 * 0.98) : 0, unit: "kg" },
      { name: "Lakshmi Organics", distance: "8 km", crop: selectedCrop, price: data?.current_price ? Math.round(data.current_price/100 * 1.1) : 0, unit: "kg" },
  ];

  return (
    <div className="flex flex-col h-full bg-slate-50 dark:bg-slate-900 overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 flex items-center bg-white dark:bg-slate-800 border-b border-slate-100 dark:border-slate-700 shadow-sm shrink-0 z-10">
        <button onClick={onClose} className="mr-4 p-2 -ml-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
          <ArrowLeft className="w-6 h-6 text-slate-600 dark:text-slate-300" />
        </button>
        <h1 className="text-xl font-bold text-slate-800 dark:text-white">{t('selling_options') || 'Selling Options'}</h1>
      </div>

      <div className="flex-1 overflow-y-auto p-5 pb-24">
        {/* Location & Crop Filter */}
        <div className="bg-white dark:bg-slate-800 p-4 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 mb-6">
            <div className="flex items-center space-x-2 text-slate-500 dark:text-slate-400 mb-2">
                <MapPin className="w-4 h-4" />
                <span className="text-xs font-medium uppercase tracking-wider">{t('location')}</span>
            </div>
            
            <div className="relative mb-4">
                <button 
                    onClick={() => setIsLocationOpen(!isLocationOpen)}
                    className="flex items-center justify-between w-full text-lg font-bold text-slate-800 dark:text-white border-b border-slate-200 dark:border-slate-700 pb-2"
                >
                    <span>{selectedLocation}</span>
                    <ChevronDown className={`w-5 h-5 transition-transform ${isLocationOpen ? 'rotate-180' : ''}`} />
                </button>
                
                {isLocationOpen && (
                    <div className="absolute top-full left-0 w-full bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 rounded-b-xl shadow-lg z-20 max-h-48 overflow-y-auto">
                        {availableLocations.map(loc => (
                            <button
                                key={loc}
                                onClick={() => {
                                    setSelectedLocation(loc);
                                    setIsLocationOpen(false);
                                }}
                                className="w-full text-left px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-sm border-b border-slate-50 dark:border-slate-700 last:border-0"
                            >
                                {loc}
                            </button>
                        ))}
                    </div>
                )}
            </div>
            
            <div className="flex space-x-2 overflow-x-auto pb-2 hide-scrollbar">
                {['Tomato', 'Onion', 'Potato', 'Cotton', 'Paddy', 'Chilli'].map(crop => (
                    <button 
                        key={crop}
                        onClick={() => setSelectedCrop(crop)}
                        className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
                            selectedCrop === crop 
                                ? 'bg-green-600 text-white shadow-md' 
                                : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600'
                        }`}
                    >
                        {crop}
                    </button>
                ))}
            </div>
        </div>

        {loading ? (
           <div className="flex flex-col items-center justify-center py-20">
             <div className="w-8 h-8 border-4 border-green-500 border-t-transparent rounded-full animate-spin mb-4"></div>
             <p className="text-slate-400 text-sm">Loading market data...</p>
           </div>
        ) : data ? (
            <div className="space-y-6">
                {/* Main Price Card */}
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/10 p-5 rounded-3xl border border-green-100 dark:border-green-800/30 shadow-sm relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-green-200 dark:bg-green-800/20 rounded-full blur-3xl -mr-10 -mt-10 pointer-events-none"></div>
                    
                    <div className="flex justify-between items-start mb-2 relative z-10">
                        <div>
                            <p className="text-sm text-green-800 dark:text-green-300 font-medium mb-1">{selectedCrop} {t('Price')}</p>
                            <h2 className="text-3xl font-bold text-green-900 dark:text-green-100">
                                ₹{Math.round((data.current_price || 0) / 100)}<span className="text-lg font-normal opacity-70">/kg</span>
                            </h2>
                        </div>
                        <div className="bg-white/80 dark:bg-slate-800/80 p-2 rounded-xl backdrop-blur-sm shadow-sm">
                            {getTrendIcon(data.trend)}
                        </div>
                    </div>
                    
                    <div className="flex items-center space-x-4 text-sm text-green-700 dark:text-green-400 relative z-10">
                        <span className="flex items-center">
                            <span className="opacity-70 mr-1">Min:</span> ₹{Math.round((data.current_price_range?.[0] || 0) / 100)}
                        </span>
                        <span className="w-1 h-1 bg-green-300 rounded-full"></span>
                        <span className="flex items-center">
                            <span className="opacity-70 mr-1">Max:</span> ₹{Math.round((data.current_price_range?.[1] || 0) / 100)}
                        </span>
                    </div>

                    <div className="mt-4 pt-4 border-t border-green-200 dark:border-green-800/30 flex justify-between items-center relative z-10">
                        <span className="text-xs text-green-800 dark:text-green-300 opacity-80">{data.market_name || 'Local Market'}</span>
                        <a 
                            href="https://agmarknet.ceda.ashoka.edu.in/" 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-xs flex items-center text-green-700 dark:text-green-400 font-medium hover:underline"
                        >
                            {t('source_agmarknet') || 'Source: Agmarknet'} <ExternalLink className="w-3 h-3 ml-1" />
                        </a>
                    </div>
                </div>

                {/* Price Chart */}
                <div>
                    <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-3">{t('price_trend') || 'Price Trend (30 Days)'} <span className="text-sm font-normal text-slate-500">(₹/kg)</span></h3>
                    <div className="bg-white dark:bg-slate-800 p-4 rounded-2xl border border-slate-100 dark:border-slate-700 h-64 w-full">
                        {data.price_history && data.price_history.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={data.price_history.map(item => ({
                                    ...item,
                                    price_per_kg: Math.round(item.modal_price / 100)
                                }))}>
                                    <defs>
                                        <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#16a34a" stopOpacity={0.3}/>
                                            <stop offset="95%" stopColor="#16a34a" stopOpacity={0}/>
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                    <XAxis 
                                        dataKey="date" 
                                        tick={{fontSize: 10}} 
                                        tickFormatter={(val) => val.split('-').slice(1).join('/')}
                                        interval="preserveStartEnd"
                                        stroke="#94a3b8"
                                    />
                                    <YAxis 
                                        domain={['auto', 'auto']} 
                                        tick={{fontSize: 10}} 
                                        width={30}
                                        stroke="#94a3b8"
                                    />
                                    <Tooltip 
                                        contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}}
                                        formatter={(value) => [`₹${value}/kg`, 'Price']}
                                    />
                                    <Area 
                                        type="monotone" 
                                        dataKey="price_per_kg" 
                                        stroke="#16a34a" 
                                        fillOpacity={1} 
                                        fill="url(#colorPrice)" 
                                        strokeWidth={2}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        ) : (
                             <div className="h-full flex items-center justify-center text-slate-400 text-sm">
                                 No history data available
                             </div>
                        )}
                    </div>
                </div>

                {/* Nearby Mandis */}
                <div>
                    <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-3 flex items-center">
                        <Store className="w-5 h-5 mr-2 text-green-600" />
                        {t('nearby_mandis') || 'Nearby Mandis'}
                    </h3>
                    
                    {data.nearby_mandis && data.nearby_mandis.length > 0 ? (
                        <div className="space-y-3">
                            {data.nearby_mandis.map((mandi, idx) => (
                                <div key={idx} className="bg-white dark:bg-slate-800 p-4 rounded-xl border border-slate-100 dark:border-slate-700 shadow-sm flex justify-between items-center">
                                    <div>
                                        <p className="font-bold text-slate-800 dark:text-white">{mandi.name}</p>
                                        <p className="text-xs text-slate-500 dark:text-slate-400">{mandi.distance_km || mandi.distance || '10'} km • {mandi.district || selectedLocation.split(',')[0]}</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="font-bold text-green-600 dark:text-green-400">₹{Math.round((mandi.price_min || mandi.price || data.current_price) / 100)}/kg</p>
                                        <p className="text-[10px] text-slate-400">{t('updated')}: {mandi.date || 'Today'}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8 bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 border-dashed">
                            <p className="text-slate-400 text-sm">No specific mandi data available for this location.</p>
                            <p className="text-xs text-slate-300 mt-1">Showing state average above.</p>
                        </div>
                    )}
                </div>

                {/* Nearby Farms (Selling Options) */}
                <div>
                    <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-3 flex items-center">
                        <Tractor className="w-5 h-5 mr-2 text-orange-500" />
                        {t('nearby_farms') || 'Nearby Farms'}
                    </h3>
                    
                    <div className="space-y-3">
                        {nearbyFarms.map((farm, idx) => (
                            <div key={idx} className="bg-white dark:bg-slate-800 p-4 rounded-xl border border-slate-100 dark:border-slate-700 shadow-sm flex justify-between items-center">
                                <div>
                                    <p className="font-bold text-slate-800 dark:text-white">{farm.name}</p>
                                    <p className="text-xs text-slate-500 dark:text-slate-400">{farm.distance} • {farm.crop}</p>
                                </div>
                                <div className="text-right">
                                    <p className="font-bold text-orange-600 dark:text-orange-400">₹{farm.price}/{farm.unit}</p>
                                    <button className="text-[10px] bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 px-2 py-1 rounded-full mt-1">
                                        {t('contact') || 'Contact'}
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        ) : (
            <div className="text-center py-20">
                <p className="text-slate-400">Failed to load data.</p>
            </div>
        )}
      </div>
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

export default MarketPrices;