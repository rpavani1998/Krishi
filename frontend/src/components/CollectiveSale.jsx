import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, MapPin, User, ChevronRight, Phone, MessageSquare, Check, Truck, TrendingUp, Info, Store } from 'lucide-react';

const CollectiveSale = ({ onBack, darkMode }) => {
  const { t } = useTranslation();
  const [view, setView] = useState('map'); // map, options, groups, detail, join, success
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [quantity, setQuantity] = useState('');

  // Mock Data
  const groups = [
    {
      id: 12,
      name: "Green Valley Farmers",
      location: "Vijayawada (12 km)",
      distance: "12 km",
      totalCapacity: 5000,
      current: 3500,
      price: 26,
      daysLeft: 2,
      minQuantity: 500,
      crop: "Cotton",
      image: "https://images.unsplash.com/photo-1595841696677-6489ff3f8cd1?auto=format&fit=crop&q=80&w=300&h=200"
    },
    {
      id: 13,
      name: "Organic Co-op #13",
      location: "Guntur (28 km)",
      distance: "28 km",
      totalCapacity: 10000,
      current: 2100,
      price: 28,
      daysLeft: 5,
      minQuantity: 1000,
      crop: "Cotton",
      image: "https://images.unsplash.com/photo-1627920769842-6887c6df0d50?auto=format&fit=crop&q=80&w=300&h=200"
    }
  ];

  const handleGroupClick = (group) => {
    setSelectedGroup(group);
    setView('detail');
  };

  const handleJoinClick = () => {
    setView('join');
  };

  const handleSubmitJoin = () => {
    setView('success');
  };

  // --- Views ---

  const MapView = () => (
    <div className="flex flex-col h-full bg-slate-50 dark:bg-slate-900">
      <div className="relative flex-1 bg-slate-200 dark:bg-slate-800 overflow-hidden">
        {/* Mock Map Background */}
        <div className="absolute inset-0 opacity-20" 
             style={{ backgroundImage: 'radial-gradient(circle, #94a3b8 1px, transparent 1px)', backgroundSize: '20px 20px' }}>
        </div>
        
        {/* Pins */}
        <div className="absolute top-1/4 left-1/4 flex flex-col items-center animate-bounce" style={{ animationDuration: '2s' }}>
            <div className="bg-blue-500 text-white text-[10px] px-2 py-1 rounded-full shadow-md mb-1 whitespace-nowrap">You</div>
            <div className="w-4 h-4 bg-blue-500 rounded-full border-2 border-white shadow-lg"></div>
        </div>

        <div className="absolute top-1/2 left-1/2 flex flex-col items-center cursor-pointer" onClick={() => setView('options')}>
             <div className="bg-green-600 text-white text-[10px] px-2 py-1 rounded-full shadow-md mb-1 whitespace-nowrap">Collection Center (5 km)</div>
             <MapPin className="text-green-600 w-8 h-8 drop-shadow-lg fill-green-100" />
        </div>
        
        {/* Map Controls */}
        <div className="absolute top-4 right-4 flex flex-col gap-2">
            <button className="bg-white dark:bg-slate-800 p-2 rounded-lg shadow-md border border-slate-100 dark:border-slate-700">
                <MapPin className="w-5 h-5 text-slate-600 dark:text-slate-300" />
            </button>
        </div>
      </div>
      
      {/* Bottom Sheet Preview */}
      <div className="bg-white dark:bg-slate-800 p-5 rounded-t-3xl shadow-[0_-5px_20px_rgba(0,0,0,0.05)] z-10">
        <div className="w-12 h-1 bg-slate-200 dark:bg-slate-700 rounded-full mx-auto mb-4"></div>
        <div className="flex justify-between items-center mb-4">
            <div>
                <h3 className="font-bold text-slate-800 dark:text-white">{t('nearby_centers')}</h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">2 active groups found</p>
            </div>
            <button onClick={() => setView('options')} className="bg-green-600 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-green-200 dark:shadow-green-900/20 shadow-lg">
                {t('view_list')}
            </button>
        </div>
      </div>
    </div>
  );

  const OptionsView = () => (
    <div className="p-5 space-y-4">
        <div className="bg-white dark:bg-slate-800 p-4 rounded-2xl border border-green-100 dark:border-green-900/30 shadow-sm">
            <div className="flex justify-between items-start mb-2">
                <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                    <User className="w-6 h-6 text-green-700 dark:text-green-400" />
                </div>
                <span className="bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 text-[10px] font-bold px-2 py-1 rounded-full">{t('recommended_tag')}</span>
            </div>
            <h3 className="font-bold text-lg text-slate-800 dark:text-white mb-1">{t('collective_sale')}</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">Join other farmers to get better prices. Current bulk rate: ₹26-28/kg</p>
            <button onClick={() => setView('groups')} className="w-full bg-green-600 text-white py-3 rounded-xl font-bold shadow-lg shadow-green-200 dark:shadow-green-900/20 flex items-center justify-center gap-2">
                {t('find_groups')} <ChevronRight className="w-4 h-4" />
            </button>
        </div>

        <div className="bg-white dark:bg-slate-800 p-4 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm opacity-60">
            <div className="flex justify-between items-start mb-2">
                <div className="p-2 bg-slate-100 dark:bg-slate-700 rounded-lg">
                    <User className="w-6 h-6 text-slate-700 dark:text-slate-300" />
                </div>
            </div>
            <h3 className="font-bold text-lg text-slate-800 dark:text-white mb-1">{t('individual_sale')}</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">Sell directly to mandi. Current rate: ₹22-24/kg</p>
            <button className="w-full bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 py-3 rounded-xl font-bold flex items-center justify-center gap-2">
                {t('sell_alone')}
            </button>
        </div>
    </div>
  );

  const GroupsView = () => (
    <div className="p-5 space-y-4">
        <h2 className="font-bold text-lg text-slate-800 dark:text-white">{t('active_groups')}</h2>
        {groups.map(group => (
            <div key={group.id} onClick={() => handleGroupClick(group)} className="bg-white dark:bg-slate-800 p-4 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm cursor-pointer hover:border-green-500 transition-colors">
                <div className="flex justify-between items-start mb-3">
                    <div>
                        <h3 className="font-bold text-slate-800 dark:text-white">{group.name}</h3>
                        <p className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1">
                            <MapPin className="w-3 h-3" /> {group.location}
                        </p>
                    </div>
                    <span className="text-green-600 dark:text-green-400 font-bold text-sm bg-green-50 dark:bg-green-900/20 px-2 py-1 rounded-lg">
                        ₹{group.price}/kg
                    </span>
                </div>
                
                {/* Progress Bar */}
                <div className="mb-2">
                    <div className="flex justify-between text-xs mb-1">
                        <span className="text-slate-600 dark:text-slate-300 font-medium">{group.current} kg</span>
                        <span className="text-slate-400">{group.totalCapacity} kg goal</span>
                    </div>
                    <div className="h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                        <div 
                            className="h-full bg-green-500 rounded-full" 
                            style={{ width: `${(group.current / group.totalCapacity) * 100}%` }}
                        ></div>
                    </div>
                </div>
                
                <div className="flex justify-between items-center mt-3 pt-3 border-t border-slate-50 dark:border-slate-700">
                    <div className="flex -space-x-2">
                        {[1,2,3].map(i => (
                            <div key={i} className="w-6 h-6 rounded-full bg-slate-200 border-2 border-white dark:border-slate-800 flex items-center justify-center text-[8px] font-bold text-slate-600">
                                {String.fromCharCode(64+i)}
                            </div>
                        ))}
                        <div className="w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-700 border-2 border-white dark:border-slate-800 flex items-center justify-center text-[8px] text-slate-500">
                            +12
                        </div>
                    </div>
                    <button className="text-xs font-bold text-blue-600 dark:text-blue-400">View Details &rarr;</button>
                </div>
            </div>
        ))}
        <button className="w-full py-3 border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-xl text-slate-500 dark:text-slate-400 text-sm font-bold flex items-center justify-center gap-2">
            + Create New Group
        </button>
    </div>
  );

  const DetailView = () => {
    if (!selectedGroup) return null;
    const percentage = Math.round((selectedGroup.current / selectedGroup.totalCapacity) * 100);
    
    return (
        <div className="flex flex-col h-full">
            <div className="flex-1 overflow-y-auto p-5 pb-24">
                <div className="bg-white dark:bg-slate-800 rounded-3xl p-6 shadow-sm border border-slate-100 dark:border-slate-700 mb-6 text-center relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-green-400 to-blue-500"></div>
                    <h2 className="text-2xl font-bold text-slate-800 dark:text-white mb-1">{percentage}%</h2>
                    <p className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide font-bold mb-6">Capacity Filled</p>
                    
                    {/* Circular Progress Placeholder */}
                    <div className="relative w-40 h-40 mx-auto mb-6">
                        <svg className="w-full h-full transform -rotate-90">
                            <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="12" fill="transparent" className="text-slate-100 dark:text-slate-700" />
                            <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="12" fill="transparent" strokeDasharray={440} strokeDashoffset={440 - (440 * percentage) / 100} className="text-green-500 transition-all duration-1000 ease-out" strokeLinecap="round" />
                        </svg>
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                            <span className="text-xs text-slate-400">Remaining</span>
                            <span className="text-lg font-bold text-slate-800 dark:text-white">{selectedGroup.totalCapacity - selectedGroup.current} kg</span>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-left">
                        <div className="bg-slate-50 dark:bg-slate-900 p-3 rounded-xl">
                            <p className="text-[10px] text-slate-400 uppercase font-bold">Price</p>
                            <p className="text-lg font-bold text-green-600 dark:text-green-400">₹{selectedGroup.price}<span className="text-xs text-slate-500 font-normal">/kg</span></p>
                        </div>
                        <div className="bg-slate-50 dark:bg-slate-900 p-3 rounded-xl">
                            <p className="text-[10px] text-slate-400 uppercase font-bold">Ends In</p>
                            <p className="text-lg font-bold text-slate-800 dark:text-white">{selectedGroup.daysLeft} days</p>
                        </div>
                    </div>
                </div>

                <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700 mb-4">
                    <h3 className="font-bold text-slate-800 dark:text-white mb-3">Buyer Information</h3>
                    <div className="flex items-center gap-3 mb-3">
                        <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
                            <Store className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                        </div>
                        <div>
                            <p className="font-bold text-sm text-slate-800 dark:text-white">Global Exports Ltd.</p>
                            <p className="text-xs text-slate-500 dark:text-slate-400">Verified Buyer • 4.8 ★</p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button className="flex-1 bg-slate-50 dark:bg-slate-700 py-2 rounded-lg text-xs font-bold text-slate-600 dark:text-slate-300 flex items-center justify-center gap-2">
                            <Phone className="w-3 h-3" /> Call
                        </button>
                        <button className="flex-1 bg-slate-50 dark:bg-slate-700 py-2 rounded-lg text-xs font-bold text-slate-600 dark:text-slate-300 flex items-center justify-center gap-2">
                            <MessageSquare className="w-3 h-3" /> Message
                        </button>
                    </div>
                </div>
            </div>

            <div className="absolute bottom-0 left-0 right-0 p-5 bg-white dark:bg-slate-800 border-t border-slate-100 dark:border-slate-700 z-10">
                <button onClick={handleJoinClick} className="w-full bg-blue-600 hover:bg-blue-700 text-white py-4 rounded-xl font-bold shadow-lg shadow-blue-200 dark:shadow-blue-900/20 text-lg transition-colors">
                    {t('join_group')}
                </button>
            </div>
        </div>
    );
  };

  const JoinView = () => (
    <div className="p-5 flex flex-col h-full">
        <h2 className="text-xl font-bold text-slate-800 dark:text-white mb-6">Add Your Harvest</h2>
        
        <div className="bg-white dark:bg-slate-800 p-5 rounded-2xl border border-slate-100 dark:border-slate-700 mb-6">
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Quantity (kg)</label>
            <div className="relative">
                <input 
                    type="number" 
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-3 text-lg font-bold text-slate-800 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="e.g. 500"
                />
                <span className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 font-bold">kg</span>
            </div>
            <p className="text-xs text-slate-500 mt-2">Minimum required: {selectedGroup?.minQuantity} kg</p>
        </div>

        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-xl border border-blue-100 dark:border-blue-800 mb-6">
            <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-slate-600 dark:text-slate-300">Your Earnings</span>
                <span className="font-bold text-lg text-slate-800 dark:text-white">₹{(quantity || 0) * (selectedGroup?.price || 0)}</span>
            </div>
            <p className="text-[10px] text-blue-600 dark:text-blue-400 flex items-center gap-1">
                <Info className="w-3 h-3" /> Based on current rate of ₹{selectedGroup?.price}/kg
            </p>
        </div>

        <div className="flex items-start gap-3 mb-8">
             <div className="mt-1">
                <input type="checkbox" className="w-5 h-5 rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
             </div>
             <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                I agree to the terms of collective sale. I understand that the final pickup date may vary by ±1 day.
             </p>
        </div>

        <button 
            onClick={handleSubmitJoin} 
            disabled={!quantity}
            className={`w-full py-4 rounded-xl font-bold shadow-lg text-lg transition-all ${
                quantity 
                ? 'bg-blue-600 text-white shadow-blue-200 dark:shadow-blue-900/20' 
                : 'bg-slate-200 dark:bg-slate-700 text-slate-400 cursor-not-allowed'
            }`}
        >
            {t('confirm_join')}
        </button>
    </div>
  );

  const SuccessView = () => (
    <div className="flex flex-col items-center justify-center h-full p-5 text-center">
        <div className="w-24 h-24 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mb-6">
            <Check className="w-12 h-12 text-green-600 dark:text-green-400" />
        </div>
        <h2 className="text-2xl font-bold text-slate-800 dark:text-white mb-2">Success!</h2>
        <p className="text-slate-500 dark:text-slate-400 mb-8 max-w-[200px]">
            You have successfully joined <b>{selectedGroup?.name}</b> with {quantity} kg.
        </p>
        
        <div className="bg-white dark:bg-slate-800 p-4 rounded-2xl w-full border border-slate-100 dark:border-slate-700 mb-8">
            <div className="flex items-center gap-4 mb-4">
                <div className="bg-blue-100 dark:bg-blue-900/30 p-3 rounded-full">
                    <Truck className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
                <div className="text-left">
                    <p className="text-xs text-slate-500 dark:text-slate-400 uppercase font-bold">Pickup Scheduled</p>
                    <p className="font-bold text-slate-800 dark:text-white">Oct 24, 2024 • 10:00 AM</p>
                </div>
            </div>
            <div className="h-px bg-slate-100 dark:bg-slate-700 mb-4"></div>
            <button className="text-blue-600 dark:text-blue-400 text-sm font-bold">View Receipt</button>
        </div>

        <button onClick={onBack} className="bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-8 py-3 rounded-xl font-bold">
            Back to Home
        </button>
    </div>
  );

  // --- Main Render ---
  return (
    <div className="flex flex-col h-full bg-slate-50 dark:bg-slate-900 transition-colors duration-300">
      {/* Header */}
      <div className="px-5 py-4 flex items-center gap-3 bg-white dark:bg-slate-800 border-b border-slate-100 dark:border-slate-700 shrink-0">
        <button onClick={() => {
            if (view === 'map') onBack();
            else if (view === 'options') setView('map');
            else if (view === 'groups') setView('options');
            else if (view === 'detail') setView('groups');
            else if (view === 'join') setView('detail');
            else if (view === 'success') onBack();
        }} className="p-2 -ml-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
            <ArrowLeft className="w-6 h-6 text-slate-700 dark:text-slate-200" />
        </button>
        <h1 className="text-lg font-bold text-slate-800 dark:text-white">
            {view === 'map' && 'Nearby Markets'}
            {view === 'options' && 'Select Type'}
            {view === 'groups' && 'Community Sales'}
            {view === 'detail' && 'Group Details'}
            {view === 'join' && 'Join Group'}
            {view === 'success' && 'Confirmation'}
        </h1>
        {/* Mockup Badge */}
        <div className="ml-auto bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 text-[10px] font-bold px-2 py-1 rounded border border-amber-200 dark:border-amber-800">
            MOCKUP
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-hidden relative">
        {view === 'map' && <MapView />}
        {view === 'options' && <OptionsView />}
        {view === 'groups' && <GroupsView />}
        {view === 'detail' && <DetailView />}
        {view === 'join' && <JoinView />}
        {view === 'success' && <SuccessView />}
      </div>
    </div>
  );
};

export default CollectiveSale;
