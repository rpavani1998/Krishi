import React, { useState } from 'react';
import { User, MapPin, Sprout, Ruler, Phone, ArrowRight, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const ManualOnboardingForm = ({ profile, onSubmit, isProcessing, onBack }) => {
  const { t } = useTranslation();
  const [draftData, setDraftData] = useState({});
  const formData = {
    name: draftData.name ?? profile?.name ?? '',
    location: draftData.location ?? profile?.location ?? '',
    primary_crop: draftData.primary_crop ?? profile?.primary_crop ?? '',
    farm_size_acres: draftData.farm_size_acres ?? profile?.farm_size_acres ?? '',
    mobile_number: draftData.mobile_number ?? profile?.mobile_number ?? ''
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setDraftData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="w-full h-full flex flex-col bg-white dark:bg-slate-800">
      <div className="p-6 border-b border-slate-100 dark:border-slate-700 bg-green-50/50 dark:bg-slate-900/50">
        <div className="flex items-center gap-3 mb-2">
            {onBack && (
                <button 
                    onClick={onBack}
                    className="p-1 -ml-2 rounded-full hover:bg-slate-200/50 dark:hover:bg-slate-700/50 text-slate-600 dark:text-slate-400 transition-colors"
                    aria-label={t('back')}
                >
                    <ArrowRight className="w-6 h-6 rotate-180" />
                </button>
            )}
            <h2 className="text-xl font-bold text-slate-800 dark:text-white">
            {t('farmer_profile')}
            </h2>
        </div>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          {t('fill_details_below')}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-5">
        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300 flex items-center gap-2">
            <User className="w-4 h-4 text-green-600" /> {t('name')}
          </label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            className="w-full p-3 rounded-xl bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 focus:ring-2 focus:ring-green-500 outline-none transition-all"
            placeholder={t('enter_name')}
            required
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300 flex items-center gap-2">
            <MapPin className="w-4 h-4 text-green-600" /> {t('location')}
          </label>
          <input
            type="text"
            name="location"
            value={formData.location}
            onChange={handleChange}
            className="w-full p-3 rounded-xl bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 focus:ring-2 focus:ring-green-500 outline-none transition-all"
            placeholder={t('city_district')}
            required
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300 flex items-center gap-2">
            <Sprout className="w-4 h-4 text-green-600" /> {t('primary_crop')}
          </label>
          <input
            type="text"
            name="primary_crop"
            value={formData.primary_crop}
            onChange={handleChange}
            className="w-full p-3 rounded-xl bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 focus:ring-2 focus:ring-green-500 outline-none transition-all"
            placeholder={t('crop_example')}
            required
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300 flex items-center gap-2">
            <Ruler className="w-4 h-4 text-green-600" /> {t('farm_size_acres')}
          </label>
          <input
            type="number"
            name="farm_size_acres"
            value={formData.farm_size_acres}
            onChange={handleChange}
            className="w-full p-3 rounded-xl bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 focus:ring-2 focus:ring-green-500 outline-none transition-all"
            placeholder="0.0"
            step="0.1"
            required
          />
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-slate-700 dark:text-slate-300 flex items-center gap-2">
            <Phone className="w-4 h-4 text-green-600" /> {t('mobile_number')}
          </label>
          <input
            type="tel"
            name="mobile_number"
            value={formData.mobile_number}
            onChange={handleChange}
            className="w-full p-3 rounded-xl bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 focus:ring-2 focus:ring-green-500 outline-none transition-all"
            placeholder="9876543210"
            pattern="[0-9]{10}"
            title={t('ten_digit_mobile')}
            required
          />
        </div>

        <div className="pt-4 pb-8">
            <button 
                type="submit"
                disabled={isProcessing}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-4 px-6 rounded-xl shadow-lg shadow-green-200 dark:shadow-none flex items-center justify-center gap-2 transition-all transform active:scale-95 disabled:opacity-70 disabled:scale-100"
            >
                {isProcessing ? (
                    <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        {t('processing')}
                    </>
                ) : (
                    <>
                        {t('continue')} <ArrowRight className="w-5 h-5" />
                    </>
                )}
            </button>
        </div>
      </form>
    </div>
  );
};

export default ManualOnboardingForm;
