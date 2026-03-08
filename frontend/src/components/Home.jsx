import React, { useState, useEffect } from 'react';
import { Mic, Phone, MessageCircle, User, BarChart2, Search, Home as HomeIcon, TrendingUp, TrendingDown, Minus, Store } from 'lucide-react';
import { motion as Motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import axios from 'axios';

const Home = ({ onStart, onOpenNews, onOpenProfile, onOpenHarvest, onOpenMarket, onOpenCollectiveSale, darkMode, toggleDarkMode, hasOnboarded, userProfile }) => {
  const { t, i18n } = useTranslation();
  const [cropPrice, setCropPrice] = useState(null);
  const [priceLoading, setPriceLoading] = useState(true);
  const [priceTrend, setPriceTrend] = useState('stable');
  const [weather, setWeather] = useState(null);
  const [weatherLoading, setWeatherLoading] = useState(true);

  // Parse location from profile
  const getLocationParams = () => {
    if (!userProfile?.location) return { state: 'Andhra Pradesh', district: 'Krishna' };
    
    // Simple heuristic: assume "District, State" or just "District"
    const parts = userProfile.location.split(',').map(p => p.trim());
    if (parts.length > 1) {
        return { district: parts[0], state: parts[1] };
    }
    return { district: parts[0], state: 'Andhra Pradesh' }; // Default state if not provided
  };

  useEffect(() => {
    const fetchWeather = async () => {
      try {
        setWeatherLoading(true);
        
        const { district } = getLocationParams();
        const locationQuery = district || 'Madanapalle';

        const response = await axios.get('/api/v1/weather/forecast', {
          params: {
            location: locationQuery
          }
        });

        if (response.data) {
          setWeather(response.data);
        }
      } catch (error) {
        console.error("Error fetching weather:", error);
      } finally {
        setWeatherLoading(false);
      }
    };

    fetchWeather();
  }, [userProfile]);

  useEffect(() => {
    const fetchCropPrice = async () => {
      try {
        setPriceLoading(true);
        
        const { state, district } = getLocationParams();
        const commodity = userProfile?.primary_crop || 'Tomato';
        
        // Fetch crop prices from CEDA service
        const response = await axios.get('/api/v1/market/prices', {
          params: {
            commodity: commodity,
            state: state,
            district: district,
            language: i18n.language
          }
        });
        
        if (response.data) {
          const priceData = response.data;
          
          // CEDA returns price per quintal, convert to per kg (1 quintal = 100 kg)
          const pricePerQuintal = priceData.current_price || 0;
          const pricePerKg = Math.round(pricePerQuintal / 100);
          
          const [minPrice, maxPrice] = priceData.current_price_range || [0, 0];
          
          setCropPrice({
            name: commodity,
            price: pricePerKg,
            min: Math.round(minPrice / 100),
            max: Math.round(maxPrice / 100),
            market: priceData.market_name || `${district} Market`,
            date: priceData.date,
            dataSource: priceData.data_source || 'live'
          });
          
          // Determine trend based on data
          if (priceData.trend) {
            setPriceTrend(priceData.trend.toLowerCase());
          }
        }
      } catch (error) {
        console.error("Error fetching price:", error);
        // Set fallback data
        setCropPrice({
          name: userProfile?.primary_crop || 'Tomato',
          price: 24,
          min: 20,
          max: 28,
          market: 'Local Market',
          dataSource: 'fallback'
        });
        setPriceTrend('stable');
      } finally {
        setPriceLoading(false);
      }
    };

    fetchCropPrice();
    
    // Refresh prices every 5 minutes
    const interval = setInterval(fetchCropPrice, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [i18n.language, userProfile]);

  const getTrendIcon = () => {
    if (priceTrend === 'rising' || priceTrend === 'up') {
      return <TrendingUp className="w-3 h-3" />;
    } else if (priceTrend === 'falling' || priceTrend === 'down') {
      return <TrendingDown className="w-3 h-3" />;
    }
    return <Minus className="w-3 h-3" />;
  };

  const getTrendColor = () => {
    if (priceTrend === 'rising' || priceTrend === 'up') {
      return 'text-green-600 dark:text-green-400';
    } else if (priceTrend === 'falling' || priceTrend === 'down') {
      return 'text-red-600 dark:text-red-400';
    }
    return 'text-slate-500 dark:text-slate-400';
  };

  const getTrendText = () => {
    if (priceTrend === 'rising' || priceTrend === 'up') {
      return t('up_price') || '↑ Rising';
    } else if (priceTrend === 'falling' || priceTrend === 'down') {
      return t('down_price') || '↓ Falling';
    }
    return t('stable_price') || '→ Stable';
  };

  const getWeatherDescription = (code) => {
    if (code === undefined || code === null) return t('cloudy') || 'Partly Cloudy';
    if (code === 0) return t('clear_sky');
    if (code >= 1 && code <= 3) return t('cloudy');
    if (code >= 45 && code <= 48) return t('foggy');
    if (code >= 51 && code <= 67) return t('rainy');
    if (code >= 71 && code <= 77) return t('snowy');
    if (code >= 80 && code <= 82) return t('rain_showers');
    if (code >= 95) return t('thunderstorm');
    return t('cloudy');
  };

  return (
    <div className="flex-1 flex flex-col bg-slate-50 dark:bg-slate-900 h-full relative transition-colors duration-300">
      {/* Header */}
      <div className="px-5 py-3 flex justify-between items-center bg-white dark:bg-slate-800 border-b border-gray-50 dark:border-slate-700 shrink-0 transition-colors duration-300">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center text-green-700 dark:text-green-400 font-bold">K</div>
          <span className="font-bold text-gray-800 dark:text-gray-100">{t('app_name')}</span>
        </div>
        <div className="flex items-center space-x-2">
            <button onClick={toggleDarkMode} className="p-2 rounded-full bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300">
                {darkMode ? '🌙' : '☀️'}
            </button>
            <div className="flex items-center bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded-full border border-green-100 dark:border-green-800">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full mr-1.5 animate-pulse"></div>
            <span className="text-[10px] font-bold text-green-700 dark:text-green-400">Online</span>
            </div>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 p-5 overflow-y-auto hide-scrollbar">
        <h2 className="text-xl font-bold text-slate-800 dark:text-white mb-1">
             {userProfile?.name ? `${t('welcome') || 'Welcome'}, ${userProfile.name}` : (t('welcome_user') || 'Welcome, Farmer')}
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-6">{userProfile?.location || t('location_status')}</p>

        {/* Mic Button Card */}
        <Motion.div 
          whileTap={{ scale: 0.95 }}
          onClick={onStart}
          className="bg-white dark:bg-slate-800 rounded-3xl p-6 shadow-sm border border-green-100 dark:border-slate-700 text-center mb-4 relative overflow-hidden group cursor-pointer transition-colors duration-300"
        >
          <div className="absolute inset-0 bg-gradient-to-b from-transparent to-green-50/50 dark:to-green-900/20 pointer-events-none"></div>
          <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-4 relative z-10">{t('need_advice')}</h3>
          <div className="w-24 h-24 bg-green-600 rounded-full flex items-center justify-center mx-auto shadow-green-200 dark:shadow-green-900/50 shadow-xl relative z-10">
            <div className="absolute inset-0 rounded-full border-2 border-green-500 animate-ping opacity-20"></div>
            <Mic className="text-white w-10 h-10" />
          </div>
          <p className="text-green-700 dark:text-green-400 text-sm font-medium mt-4 relative z-10">{t('tap_speak')}</p>
        </Motion.div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <button className="bg-blue-600 text-white p-3 rounded-xl flex flex-col items-center justify-center shadow-lg active:scale-95 transition-transform">
            <Phone className="w-6 h-6 mb-2" />
            <span className="text-xs font-bold">{t('call_help')}</span>
            <span className="text-[10px] opacity-80">{t('toll_free')}</span>
          </button>
          <button onClick={onOpenMarket} className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 p-3 rounded-xl flex flex-col items-center justify-center shadow-sm active:scale-95 transition-transform">
            <Store className="w-6 h-6 mb-2 text-green-600 dark:text-green-400" />
            <span className="text-xs font-bold">{t('selling_options')}</span>
            <span className="text-[10px] text-slate-400">{t('mandis_farms')}</span>
          </button>
          <button onClick={onOpenNews} className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 p-3 rounded-xl flex flex-col items-center justify-center shadow-sm active:scale-95 transition-transform">
            <Store className="w-6 h-6 mb-2 text-blue-500 dark:text-blue-400" />
            <span className="text-xs font-bold">{t('market_news') || 'Market News'}</span>
            <span className="text-[10px] text-slate-400">{t('latest_updates') || 'Latest Updates'}</span>
          </button>
          <button onClick={onOpenCollectiveSale} className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 p-3 rounded-xl flex flex-col items-center justify-center shadow-sm active:scale-95 transition-transform relative overflow-hidden">
            <div className="absolute top-0 right-0 bg-amber-500 text-white text-[8px] font-bold px-1.5 py-0.5 rounded-bl-lg">MOCK</div>
            <User className="w-6 h-6 mb-2 text-amber-500 dark:text-amber-400" />
            <span className="text-xs font-bold">{t('collective_sale') || 'Collective Sale'}</span>
            <span className="text-[10px] text-slate-400">{t('group_save') || 'Group & Save'}</span>
          </button>
        </div>

        {/* Info Cards */}
        <div className="grid grid-cols-2 gap-3 pb-20">
          <div onClick={onOpenMarket} className="bg-white dark:bg-slate-800 p-4 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 transition-colors duration-300 relative cursor-pointer active:scale-95">
            <p className="text-[10px] text-slate-400 uppercase font-bold">{cropPrice?.name || 'Crop'} {t('price')}</p>
            {priceLoading ? (
              <div className="flex items-center space-x-2 mt-2">
                <div className="w-4 h-4 border-2 border-green-500 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-xs text-slate-400">{t('loading')}</span>
              </div>
            ) : cropPrice ? (
              <>
                <div className="flex justify-between items-end">
                    <div>
                        <p className="text-lg font-bold text-slate-800 dark:text-white mt-1">
                          ₹{cropPrice.price}
                          <span className="text-xs text-slate-400 font-normal">{t('price_per_kg_suffix')}</span>
                        </p>
                        <p className={`text-[10px] mt-1 flex items-center space-x-1 ${getTrendColor()}`}>
                          {getTrendIcon()}
                          <span>{getTrendText()}</span>
                        </p>
                    </div>
                </div>
                <div className="flex justify-between items-center mt-2">
                    <p className="text-[10px] text-slate-400 truncate max-w-[70px]">{cropPrice.market}</p>
                    <span className="text-[10px] text-blue-500 font-medium underline">{t('explore')}</span>
                </div>
                {cropPrice.dataSource === 'fallback' && (
                  <p className="text-[9px] text-amber-600 dark:text-amber-400 mt-1">{t('estimated')}</p>
                )}
              </>
            ) : (
              <p className="text-sm text-slate-400 mt-1">{t('na')}</p>
            )}
          </div>
          <div className="bg-white dark:bg-slate-800 p-4 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 transition-colors duration-300">
            <p className="text-[10px] text-slate-400 uppercase font-bold">{t('weather') || 'Weather'}</p>
            {weatherLoading ? (
               <div className="flex items-center space-x-2 mt-2">
                 <div className="w-4 h-4 border-2 border-green-500 border-t-transparent rounded-full animate-spin"></div>
                 <span className="text-xs text-slate-400">{t('loading')}</span>
               </div>
            ) : weather ? (
              <>
                <p className="text-lg font-bold text-slate-800 dark:text-white mt-1">
                  {weather.current ? Math.round(weather.current.temperature) : 28}°C
                </p>
                <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">
                  {weather.current ? getWeatherDescription(weather.current.weathercode) : (t('cloudy') || 'Partly Cloudy')}
                </p>
                {weather.data_source === 'fallback' && (
                  <p className="text-[9px] text-amber-600 dark:text-amber-400 mt-1">{t('estimated')}</p>
                )}
              </>
            ) : (
              <p className="text-sm text-slate-400 mt-1">{t('na')}</p>
            )}
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="bg-white dark:bg-slate-800 border-t border-slate-100 dark:border-slate-700 px-6 py-3 flex justify-between absolute bottom-0 left-0 right-0 z-50 transition-colors duration-300">
        <HomeIcon className="text-green-600 dark:text-green-400 w-6 h-6" />
        <button 
            onClick={onOpenHarvest}
            className={`transition-colors ${!hasOnboarded ? 'opacity-40 cursor-not-allowed' : ''}`}
        >
          <BarChart2 className="text-slate-300 dark:text-slate-600 w-6 h-6 hover:text-green-600 dark:hover:text-green-400 transition-colors" />
        </button>
        <button className={`${!hasOnboarded ? 'opacity-40' : ''}`}>
             <Search className="text-slate-300 dark:text-slate-600 w-6 h-6" />
        </button>
        <button 
            onClick={onOpenProfile}
            className={`transition-colors ${!hasOnboarded ? 'opacity-40 cursor-not-allowed' : ''}`}
        >
            <User className="text-slate-300 dark:text-slate-600 w-6 h-6 hover:text-green-600 dark:hover:text-green-400 transition-colors" />
        </button>
      </div>
    </div>
  );
};

export default Home;
