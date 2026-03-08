import React, { useState, useEffect, useCallback } from 'react';
import { ArrowLeft, Search, Filter, Star, Clock, ChevronRight, Mic, Heart, Share2, TrendingUp, Zap, BookOpen, ShoppingBag } from 'lucide-react';
import { motion as Motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { useTranslation } from 'react-i18next';

const MarketNews = ({ onBack, onVoice, userProfile }) => {
  const { t, i18n } = useTranslation();
  const [activeTab, setActiveTab] = useState('all'); // 'all' | 'trending' | 'personalized' | 'recent'
  const [searchQuery, setSearchQuery] = useState('');
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Mock data for demonstration purposes (since backend API is limited to news)
  const MOCK_RECOMMENDATIONS = [
    {
      id: 'r1',
      type: 'product',
      title: 'Organic Fertilizer Boost',
      description: 'Increase yield by 20% with this new organic mix.',
      image: 'https://images.unsplash.com/photo-1628352081506-83c43123ed6d?w=800&auto=format&fit=crop&q=60',
      rating: 4.8,
      price: '₹450',
      category: 'fertilizer',
      trending: true
    },
    {
      id: 'r2',
      type: 'tip',
      title: 'Monsoon Preparation Guide',
      description: 'Essential steps to protect your crops before the rains hit.',
      image: 'https://images.unsplash.com/photo-1515694346937-94d85e41e6f0?w=800&auto=format&fit=crop&q=60',
      rating: 4.9,
      category: 'farming_tips',
      personalized: true
    },
    {
      id: 'r3',
      type: 'tool',
      title: 'Smart Irrigation Sensor',
      description: 'Save water and automate your irrigation schedule.',
      image: 'https://images.unsplash.com/photo-1563514227146-8930c451a447?w=800&auto=format&fit=crop&q=60',
      rating: 4.5,
      price: '₹1,200',
      category: 'equipment',
      trending: true
    },
    {
      id: 'r4',
      type: 'market',
      title: 'Tomato Price Alert',
      description: 'Prices expected to rise in Madanapalle market next week.',
      image: 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=800&auto=format&fit=crop&q=60',
      rating: 5.0,
      category: 'market_updates',
      personalized: true,
      recent: true
    }
  ];

  const fetchRecommendations = useCallback(async () => {
    try {
      setLoading(true);
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // In a real app, we would fetch from multiple endpoints
      // For now, we'll combine mock data with news if available
      try {
          const params = { 
              language: i18n.language, 
              category: 'agriculture', 
              limit: 5 
          };
          
          if (userProfile?.primary_crop) {
              params.crop = userProfile.primary_crop;
          }
          if (userProfile?.location) {
              params.region = userProfile.location;
          }
          
          const response = await axios.get('/api/v1/news', { params });
          
          const newsItems = (response.data?.articles || []).map((article, idx) => ({
              id: `news-${idx}`,
              type: 'news',
              title: article.title,
              description: article.description,
              image: article.urlToImage || 'https://images.unsplash.com/photo-1500937386664-56d1dfef3854?w=800&auto=format&fit=crop&q=60',
              rating: 4.0 + (Math.random()),
              category: 'news',
              url: article.url,
              personalized: true // Mark news as personalized if we filtered by crop
          }));
          
          setRecommendations([...MOCK_RECOMMENDATIONS, ...newsItems]);
      } catch (e) {
          console.warn("News fetch failed, using mock data only");
          setRecommendations(MOCK_RECOMMENDATIONS);
      }
      
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  }, [i18n.language, userProfile]);

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  // Filter logic
  const filteredItems = recommendations.filter(item => {
      const matchesSearch = item.title.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesTab = activeTab === 'all' || 
                         (activeTab === 'trending' && item.trending) ||
                         (activeTab === 'personalized' && item.personalized) ||
                         (activeTab === 'recent' && item.recent);
      return matchesSearch && matchesTab;
  });

  const categories = [
      { id: 'all', label: t('all') || 'All', icon: Zap },
      { id: 'trending', label: t('trending') || 'Trending', icon: TrendingUp },
      { id: 'personalized', label: t('for_you') || 'For You', icon: Heart },
      { id: 'recent', label: t('recent') || 'Recent', icon: Clock },
  ];

  // Components
  const RecommendationCard = ({ item }) => (
      <Motion.div 
        layout
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="bg-white dark:bg-slate-800 rounded-2xl overflow-hidden shadow-sm border border-slate-100 dark:border-slate-700 flex flex-col h-full group"
      >
          {/* Image Section */}
          <div className="relative h-32 overflow-hidden">
              <img src={item.image} alt={item.title} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
              <div className="absolute top-2 right-2 bg-white/90 dark:bg-black/50 backdrop-blur-sm rounded-full px-2 py-0.5 flex items-center space-x-1 text-xs font-bold shadow-sm">
                  <Star className="w-3 h-3 text-yellow-500 fill-yellow-500" />
                  <span className="text-slate-800 dark:text-white">{item.rating.toFixed(1)}</span>
              </div>
              {item.type === 'product' && item.price && (
                  <div className="absolute bottom-2 left-2 bg-green-500 text-white text-xs font-bold px-2 py-1 rounded-lg shadow-sm">
                      {item.price}
                  </div>
              )}
          </div>
          
          {/* Content Section */}
          <div className="p-4 flex-1 flex flex-col">
              <div className="flex justify-between items-start mb-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 px-2 py-0.5 rounded-md">
                      {item.category.replace('_', ' ')}
                  </span>
              </div>
              
              <h3 className="font-bold text-slate-800 dark:text-white leading-tight mb-2 line-clamp-2">
                  {item.title}
              </h3>
              
              <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 mb-4 flex-1">
                  {item.description}
              </p>
              
              <div className="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-700">
                  <button className="text-slate-400 hover:text-green-500 transition-colors">
                      <Heart className="w-4 h-4" />
                  </button>
                  <button className="bg-slate-900 dark:bg-slate-700 text-white text-xs font-bold px-4 py-2 rounded-xl hover:bg-slate-800 dark:hover:bg-slate-600 transition-colors shadow-sm flex items-center space-x-1">
                      <span>{t('view') || 'View'}</span>
                      <ChevronRight className="w-3 h-3" />
                  </button>
              </div>
          </div>
      </Motion.div>
  );

  return (
    <div className="flex-1 bg-slate-50 dark:bg-slate-900 flex flex-col h-full relative transition-colors duration-300">
      {/* Header */}
      <div className="px-5 py-4 bg-white dark:bg-slate-800 border-b border-slate-100 dark:border-slate-700 sticky top-0 z-20 shadow-sm transition-colors duration-300">
        <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
                <button onClick={onBack} className="mr-3 p-2 -ml-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
                    <ArrowLeft className="text-slate-600 dark:text-slate-300 w-5 h-5" />
                </button>
                <h1 className="font-bold text-xl text-slate-800 dark:text-white">{t('discover') || 'Discover'}</h1>
            </div>
            <div className="flex items-center space-x-2">
                <button className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors relative">
                    <Share2 className="w-5 h-5 text-slate-600 dark:text-slate-300" />
                </button>
                <div className="w-8 h-8 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center text-green-700 dark:text-green-300 font-bold text-xs border border-green-200 dark:border-green-800">
                    K
                </div>
            </div>
        </div>

        {/* Search Bar */}
        <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input 
                type="text" 
                placeholder={t('search_placeholder') || "Search for crops, tips, news..."}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-xl bg-slate-100 dark:bg-slate-700/50 border-none focus:ring-2 focus:ring-green-500/20 text-sm font-medium text-slate-800 dark:text-white placeholder-slate-400 transition-all"
            />
        </div>

        {/* Categories / Tabs */}
        <div className="flex space-x-2 overflow-x-auto pb-1 scrollbar-hide">
            {categories.map(cat => {
                const Icon = cat.icon;
                const isActive = activeTab === cat.id;
                return (
                    <button
                        key={cat.id}
                        onClick={() => setActiveTab(cat.id)}
                        className={`flex items-center space-x-1 px-4 py-2 rounded-full text-xs font-bold whitespace-nowrap transition-all ${
                            isActive 
                            ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 shadow-md transform scale-105' 
                            : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700'
                        }`}
                    >
                        <Icon className="w-3 h-3" />
                        <span>{cat.label}</span>
                    </button>
                );
            })}
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-4 pb-24 space-y-6">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[1, 2, 3, 4].map(i => (
                  <div key={i} className="bg-white dark:bg-slate-800 h-64 rounded-2xl animate-pulse"></div>
              ))}
          </div>
        ) : (
          <AnimatePresence mode="popLayout">
            {/* Featured Section (Only on 'all' tab) */}
            {activeTab === 'all' && !searchQuery && (
                <Motion.div 
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-6"
                >
                    <div className="flex justify-between items-end mb-3">
                        <h2 className="font-bold text-lg text-slate-800 dark:text-white">{t('featured') || 'Featured'}</h2>
                        <button className="text-green-600 dark:text-green-400 text-xs font-bold hover:underline">{t('see_all') || 'See All'}</button>
                    </div>
                    <div className="bg-gradient-to-br from-green-500 to-emerald-700 rounded-2xl p-6 text-white relative overflow-hidden shadow-lg shadow-green-500/20">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-2xl transform translate-x-10 -translate-y-10"></div>
                        <div className="relative z-10">
                            <span className="bg-white/20 backdrop-blur-md text-xs font-bold px-2 py-1 rounded-lg mb-3 inline-block">
                                {t('trending_now') || 'Trending Now'}
                            </span>
                            <h3 className="text-2xl font-bold mb-2">Maximum Yield Strategy 2024</h3>
                            <p className="text-green-50 text-sm mb-4 line-clamp-2 opacity-90">
                                Discover the latest techniques used by top farmers to increase crop output by up to 30%.
                            </p>
                            <button className="bg-white text-green-700 px-5 py-2 rounded-xl text-sm font-bold shadow-sm hover:bg-green-50 transition-colors">
                                {t('read_more') || 'Read More'}
                            </button>
                        </div>
                    </div>
                </Motion.div>
            )}

            {/* Grid of Recommendations */}
            <div>
                <div className="flex justify-between items-end mb-3">
                    <h2 className="font-bold text-lg text-slate-800 dark:text-white">
                        {activeTab === 'all' ? (t('recommended_for_you') || 'Recommended for You') : categories.find(c => c.id === activeTab)?.label}
                    </h2>
                </div>
                
                {filteredItems.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {filteredItems.map(item => (
                            <RecommendationCard key={item.id} item={item} />
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-10 text-slate-400">
                        <Search className="w-12 h-12 mx-auto mb-3 opacity-20" />
                        <p>{t('no_results') || 'No recommendations found'}</p>
                    </div>
                )}
            </div>
          </AnimatePresence>
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

export default MarketNews;
