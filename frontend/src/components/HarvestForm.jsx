import React, { useState } from 'react';
import { ArrowLeft, MapPin, Calendar, Box, TrendingUp, CloudRain, Archive, Mic } from 'lucide-react';
import { motion as Motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';

const HarvestForm = ({ userProfile, onSubmit, onCancel, onVoice }) => {
  const { t } = useTranslation();
  const [formData, setFormData] = useState({
    crop: userProfile?.primary_crop || 'Tomato',
    quantity: '50',
    location: userProfile?.location || 'Madanapalle',
    harvest_date: new Date().toISOString().split('T')[0],
    storage_condition: 'open'
  });

  const defaultCrops = ['Tomato', 'Onion', 'Chillies', 'Paddy'];
  const crops = userProfile?.primary_crop && !defaultCrops.includes(userProfile.primary_crop) 
    ? [userProfile.primary_crop, ...defaultCrops] 
    : defaultCrops;

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="flex-1 bg-slate-50 dark:bg-slate-900 flex flex-col h-full relative z-50 transition-colors duration-300">
      {/* Header */}
      <div className="px-5 py-3 flex items-center bg-white dark:bg-slate-800 border-b border-slate-100 dark:border-slate-700 shadow-sm sticky top-0 z-10 transition-colors duration-300">
        <button onClick={onCancel} className="mr-3 p-2 -ml-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
          <ArrowLeft className="w-5 h-5 text-slate-600 dark:text-slate-300" />
        </button>
        <h2 className="text-lg font-bold text-slate-800 dark:text-white">{t('crop_details')}</h2>
      </div>

      <form onSubmit={handleSubmit} className="flex-1 p-5 overflow-y-auto space-y-6 pb-24">
        {/* Crop Selection */}
        <div className="bg-white dark:bg-slate-800 p-5 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 transition-colors duration-300">
          <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">{t('crop_type')}</label>
          <div className="grid grid-cols-2 gap-3">
            {crops.map((crop) => (
              <button
                key={crop}
                type="button"
                onClick={() => setFormData({ ...formData, crop })}
                className={`p-3 rounded-xl border text-sm font-medium transition-all shadow-sm ${
                  formData.crop === crop
                    ? 'bg-green-600 border-green-600 text-white shadow-green-200 dark:shadow-green-900/50'
                    : 'bg-white dark:bg-slate-700 border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-300 hover:border-green-200 dark:hover:border-green-700 hover:bg-green-50 dark:hover:bg-green-900/20'
                }`}
              >
                {crop}
              </button>
            ))}
          </div>
        </div>

        {/* Quantity */}
        <div className="bg-white dark:bg-slate-800 p-5 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 transition-colors duration-300">
          <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">{t('quantity_quintals')}</label>
          <div className="relative">
            <Box className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="number"
              name="quantity"
              value={formData.quantity}
              onChange={handleChange}
              className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-600 focus:border-green-500 dark:focus:border-green-500 focus:ring-2 focus:ring-green-100 dark:focus:ring-green-900/30 outline-none transition-all font-medium text-slate-800 dark:text-white placeholder-slate-400"
              placeholder="Ex: 50"
            />
          </div>
        </div>

        {/* Location */}
        <div className="bg-white dark:bg-slate-800 p-5 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 transition-colors duration-300">
          <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">{t('location')}</label>
          <div className="relative">
            <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              name="location"
              value={formData.location}
              onChange={handleChange}
              className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-600 focus:border-green-500 dark:focus:border-green-500 focus:ring-2 focus:ring-green-100 dark:focus:ring-green-900/30 outline-none transition-all font-medium text-slate-800 dark:text-white placeholder-slate-400"
              placeholder="Ex: Madanapalle"
            />
          </div>
        </div>

        {/* Harvest Date */}
        <div className="bg-white dark:bg-slate-800 p-5 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 transition-colors duration-300">
          <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">{t('harvest_date')}</label>
          <div className="relative">
            <Calendar className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="date"
              name="harvest_date"
              value={formData.harvest_date}
              onChange={handleChange}
              className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-600 focus:border-green-500 dark:focus:border-green-500 focus:ring-2 focus:ring-green-100 dark:focus:ring-green-900/30 outline-none transition-all font-medium text-slate-800 dark:text-white"
            />
          </div>
        </div>

        {/* Storage Condition */}
        <div className="bg-white dark:bg-slate-800 p-5 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 transition-colors duration-300">
          <label className="block text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">{t('storage_condition')}</label>
          <div className="relative">
             <Archive className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
             <select
                name="storage_condition"
                value={formData.storage_condition}
                onChange={handleChange}
                className="w-full pl-12 pr-4 py-3.5 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-600 focus:border-green-500 dark:focus:border-green-500 focus:ring-2 focus:ring-green-100 dark:focus:ring-green-900/30 outline-none transition-all font-medium text-slate-800 dark:text-white appearance-none"
             >
                <option value="open">{t('storage_open')}</option>
                <option value="covered">{t('storage_covered')}</option>
                <option value="cold_storage">{t('storage_cold')}</option>
             </select>
          </div>
        </div>
        
        {/* Submit Button */}
        <div className="pt-2">
            <Motion.button
                whileTap={{ scale: 0.98 }}
                type="submit"
                className="w-full bg-green-600 hover:bg-green-700 text-white p-4 rounded-2xl font-bold text-lg shadow-lg shadow-green-200 dark:shadow-green-900/50 flex items-center justify-center space-x-2 transition-colors"
            >
                <span>{t('analyze')}</span>
                <TrendingUp className="w-5 h-5" />
            </Motion.button>
        </div>
      </form>

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

export default HarvestForm;
