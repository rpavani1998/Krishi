import React, { useState } from 'react';
import { motion as Motion } from 'framer-motion';
import { Check, Edit2, MapPin, Wheat, Ruler, Phone, Save } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const ConfirmDetails = ({ profile, onConfirm, onEdit }) => {
  const { t } = useTranslation();
  const [isEditing, setIsEditing] = useState(false);
  const [editedProfile, setEditedProfile] = useState(profile);

  const details = [
    { icon: <MapPin className="w-5 h-5 text-green-600" />, label: t('location'), value: editedProfile.location, key: 'location' },
    { icon: <Wheat className="w-5 h-5 text-green-600" />, label: t('crop'), value: editedProfile.primary_crop, key: 'primary_crop' },
    { icon: <Ruler className="w-5 h-5 text-green-600" />, label: t('farm_size'), value: `${editedProfile.farm_size_acres} ${t('acres')}`, key: 'farm_size_acres' },
    { icon: <Phone className="w-5 h-5 text-green-600" />, label: t('mobile'), value: editedProfile.mobile_number, key: 'mobile_number' },
  ];

  const handleEdit = () => {
    setIsEditing(true);
    onEdit();
  };

  const handleSave = () => {
    setIsEditing(false);
    onConfirm(editedProfile);
  };

  const handleChange = (key, value) => {
    setEditedProfile(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6 py-12 bg-white dark:bg-slate-900 h-full transition-colors duration-300">
      <Motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="w-full max-w-sm flex flex-col items-center"
      >
        <div className="w-20 h-20 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mb-6">
          {isEditing ? <Edit2 className="w-10 h-10 text-green-600 dark:text-green-400" /> : <Check className="w-10 h-10 text-green-600 dark:text-green-400" />}
        </div>

        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2 text-center">
          {isEditing ? t('edit_details') : t('confirm_details_title')}
        </h2>
        <p className="text-slate-500 dark:text-slate-400 mb-8 text-center">
          {isEditing ? t('update_your_information') : t('check_correct')}
        </p>

        <div className="w-full bg-slate-50 dark:bg-slate-800 rounded-2xl p-6 mb-8 border border-slate-200 dark:border-slate-700">
          <div className="flex items-center justify-between mb-6 border-b border-slate-200 dark:border-slate-700 pb-4">
            <h3 className="text-xl font-semibold text-slate-900 dark:text-white">
              {editedProfile.name}
            </h3>
            <button 
              onClick={isEditing ? handleSave : handleEdit}
              className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-green-600 bg-green-50 hover:bg-green-100 dark:bg-slate-700 dark:text-green-400 dark:hover:bg-slate-600 rounded-full transition-colors"
            >
              {isEditing ? <Save className="w-4 h-4" /> : <Edit2 className="w-4 h-4" />}
              {isEditing ? t('save') : t('edit')}
            </button>
          </div>

          <div className="space-y-4">
            {details.map((item, index) => (
              <div key={index} className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-white dark:bg-slate-700 flex items-center justify-center shadow-sm">
                  {item.icon}
                </div>
                <div className='w-full'>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{item.label}</p>
                  {isEditing ? (
                    <input
                      type="text"
                      value={item.value}
                      onChange={(e) => handleChange(item.key, e.target.value)}
                      className="w-full bg-transparent text-sm font-medium text-slate-900 dark:text-white focus:outline-none"
                    />
                  ) : (
                    <p className="text-sm font-medium text-slate-900 dark:text-white">{item.value || '-'}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <button
          onClick={isEditing ? handleSave : onConfirm}
          className="w-full py-4 bg-green-600 hover:bg-green-700 text-white font-bold rounded-xl shadow-lg shadow-green-200 dark:shadow-none transition-all duration-200 transform active:scale-95"
        >
          {isEditing ? t('save_and_continue') : t('confirm_set_pin')}
        </button>
      </Motion.div>
    </div>
  );
};

export default ConfirmDetails;
