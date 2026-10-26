import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CROP_CATEGORY_LABELS,
  CropCategory,
  CropFilterParams,
  CropListingItem,
  SavedBuyerSearchItem,
} from '../features/crop-marketplace/types';
import {
  createSavedSearchApi,
  deleteSavedSearchApi,
  getCropListingsApi,
  getSavedSearchesApi,
} from '../features/crop-marketplace/api';
import { createConversationApi } from '../features/messaging/api';
import { CropListingCard } from '../features/crop-marketplace/components/CropListingCard';
import { Button } from '../components/ui/Button';
import {
  Search,
  ShieldCheck,
  ShoppingBag,
  PlusCircle,
  MessageCircle,
  X,
  Bookmark,
  BookmarkCheck,
  Bell,
  CheckCircle2,
  Loader2,
} from 'lucide-react';

export const CropMarketplace: React.FC = () => {
  const navigate = useNavigate();
  const token = localStorage.getItem('shikhor_token');
  const [listings, setListings] = useState<CropListingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [selectedCategory, setSelectedCategory] = useState<CropCategory | ''>('');
  const [searchDistrict, setSearchDistrict] = useState('');
  const [minPrice, setMinPrice] = useState<string>('');
  const [maxPrice, setMaxPrice] = useState<string>('');

  // Saved Searches state
  const [savedSearches, setSavedSearches] = useState<SavedBuyerSearchItem[]>([]);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [saveSearchName, setSaveSearchName] = useState('');
  const [savingSearch, setSavingSearch] = useState(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // Contact Modal state
  const [contactTarget, setContactTarget] = useState<CropListingItem | null>(null);
  const [initialMessage, setInitialMessage] = useState('');
  const [sendingMsg, setSendingMsg] = useState(false);
  const [contactError, setContactError] = useState<string | null>(null);

  const fetchSavedSearches = async () => {
    if (!token) return;
    try {
      const items = await getSavedSearchesApi(token);
      setSavedSearches(items);
    } catch {
      // silently ignore
    }
  };

  useEffect(() => {
    fetchSavedSearches();
  }, [token]);

  const handleApplySavedSearch = (s: SavedBuyerSearchItem) => {
    setSelectedCategory((s.category as CropCategory) || '');
    setSearchDistrict(s.district || '');
    setMaxPrice(s.maxPrice ? s.maxPrice.toString() : '');
    setMinPrice('');

    const filters: CropFilterParams = {};
    if (s.category) filters.category = s.category;
    if (s.district) filters.district = s.district;
    if (s.maxPrice) filters.maxPrice = s.maxPrice;
    setLoading(true);
    getCropListingsApi(filters)
      .then((data) => setListings(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  const handleSaveCurrentSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      navigate('/login');
      return;
    }
    if (!saveSearchName.trim()) return;

    try {
      setSavingSearch(true);
      await createSavedSearchApi(token, {
        name: saveSearchName.trim(),
        category: selectedCategory || undefined,
        district: searchDistrict.trim() || undefined,
        maxPrice: maxPrice ? parseInt(maxPrice, 10) : undefined,
      });
      setSaveSuccessMsg('অনুসন্ধান সফলভাবে সংরক্ষিত হয়েছে! নতুন মিল এলে নোটিফিকেশন পাবেন।');
      fetchSavedSearches();
      setTimeout(() => {
        setShowSaveModal(false);
        setSaveSuccessMsg(null);
        setSaveSearchName('');
      }, 1500);
    } catch (err: any) {
      alert(err.message || 'সংরক্ষণ ব্যর্থ হয়েছে।');
    } finally {
      setSavingSearch(false);
    }
  };

  const handleDeleteSavedSearch = async (searchId: string) => {
    if (!token) return;
    try {
      await deleteSavedSearchApi(token, searchId);
      setSavedSearches((prev) => prev.filter((s) => s.id !== searchId));
    } catch (err: any) {
      alert(err.message || 'মুছে ফেলা যায়নি।');
    }
  };

  const fetchListings = async () => {
    try {
      setLoading(true);
      setError(null);
      const filters: CropFilterParams = {};
      if (selectedCategory) filters.category = selectedCategory as CropCategory;
      if (searchDistrict.trim()) filters.district = searchDistrict.trim();
      if (minPrice) filters.minPrice = parseInt(minPrice, 10);
      if (maxPrice) filters.maxPrice = parseInt(maxPrice, 10);

      const data = await getCropListingsApi(filters);
      setListings(data);
    } catch (err: any) {
      setError(err?.message || 'ফসলের তালিকা লোড করা যায়নি।');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchListings();
  }, [selectedCategory]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchListings();
  };

  const handleStartContact = (listing: CropListingItem) => {
    if (!token) {
      navigate('/login');
      return;
    }
    setContactTarget(listing);
    setInitialMessage(
      `আসসালামু আলাইকুম, আমি আপনার "${listing.cropName}" (${listing.district}) ক্রয়ে আগ্রহী। বিস্তারিত আলোচনা করতে চাই।`
    );
    setContactError(null);
  };

  const handleSendInitialMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !contactTarget || !initialMessage.trim()) return;

    try {
      setSendingMsg(true);
      setContactError(null);
      const conv = await createConversationApi(token, {
        recipientId: contactTarget.farmerId,
        contextType: 'crop_listing',
        contextId: contactTarget.id,
        initialMessage: initialMessage.trim(),
      });
      setContactTarget(null);
      navigate(`/app/messages?convId=${conv.id}`);
    } catch (err: any) {
      setContactError(err?.message || 'বার্তা শুরু করা যায়নি।');
    } finally {
      setSendingMsg(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-emerald-900 to-forest-800 rounded-3xl p-8 mb-8 text-white relative overflow-hidden shadow-lg">
        <div className="relative z-10 max-w-2xl">
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-700/60 text-emerald-200 border border-emerald-500/30 inline-block mb-3">
            সরাসরি কৃষক-পাইকার সংযোগ
          </span>
          <h1 className="text-3xl font-extrabold sm:text-4xl tracking-tight">
            কৃষি ফসল বাজার ও ক্রয়-বিক্রয়
          </h1>
          <p className="mt-3 text-emerald-100 text-sm sm:text-base leading-relaxed">
            মধ্যস্বত্বভোগী ছাড়া সরাসরি কৃষকদের কাছ থেকে সেরা মূল্যে ফসল সংগ্রহ করুন। কৃষক ও ক্রেতা উভয়ের নিরাপত্তা ও গোপনীয়তা নিশ্চিত।
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Button
              variant="outline"
              className="bg-white/10 hover:bg-white/20 text-white border-white/20 text-xs sm:text-sm"
              onClick={() => navigate('/app/my-crops')}
            >
              <PlusCircle className="w-4 h-4 mr-1.5" />
              আমার ফসলের তালিকা
            </Button>
            <Button
              variant="outline"
              className="bg-white/10 hover:bg-white/20 text-white border-white/20 text-xs sm:text-sm"
              onClick={() => navigate('/app/messages')}
            >
              <MessageCircle className="w-4 h-4 mr-1.5" />
              ইনবক্স ও বার্তা
            </Button>
          </div>
        </div>
      </div>

      {/* Privacy Notice Banner (Rule 17) */}
      <div className="bg-emerald-50 border border-emerald-200/80 rounded-2xl p-4 mb-8 flex items-center gap-3 text-emerald-900 text-xs sm:text-sm">
        <ShieldCheck className="w-6 h-6 text-emerald-600 shrink-0" />
        <div>
          <strong className="font-bold">গোপনীয়তা সুরক্ষা নীতি:</strong> কৃষকদের ব্যক্তিগত ফোন নম্বর এবং বাড়ির সঠিক অবস্থান প্ল্যাটফর্মে গোপন রাখা হয়। নিরাপদ লেনদেন ও যোগাযোগের জন্য আমাদের সুরক্ষিত চ্যাট ব্যবহার করুন।
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-5 mb-8">
        <form onSubmit={handleSearchSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">ফসলের বিভাগ</label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value as CropCategory | '')}
                className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white"
              >
                <option value="">সব ফসল</option>
                {Object.entries(CROP_CATEGORY_LABELS).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">জেলা দিয়ে খুঁজুন</label>
              <input
                type="text"
                placeholder="যেমন: দিনাজপুর, বগুড়া"
                value={searchDistrict}
                onChange={(e) => setSearchDistrict(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">সর্বনিম্ন মূল্য (৳)</label>
              <input
                type="number"
                placeholder="0"
                value={minPrice}
                onChange={(e) => setMinPrice(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">সর্বোচ্চ মূল্য (৳)</label>
              <input
                type="number"
                placeholder="10000"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>
          </div>

          <div className="flex items-center justify-between gap-2 pt-2 flex-wrap">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                type="button"
                className="text-xs text-forest-800 border-leaf-300 hover:bg-leaf-50 flex items-center gap-1.5"
                onClick={() => {
                  const defaultName = [
                    selectedCategory ? CROP_CATEGORY_LABELS[selectedCategory as CropCategory] : '',
                    searchDistrict ? searchDistrict : '',
                    maxPrice ? `(সর্বোচ্চ ৳${maxPrice})` : '',
                  ].filter(Boolean).join(' - ') || 'আমার অনুসন্ধান';
                  setSaveSearchName(defaultName);
                  setShowSaveModal(true);
                }}
                title="নতুন ফসল এলেই নোটিফিকেশন পেতে এই ফিল্টারটি সংরক্ষণ করুন"
              >
                <Bookmark className="w-3.5 h-3.5 text-forest-700" />
                <span>এই অনুসন্ধান সংরক্ষণ করুন</span>
              </Button>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                type="button"
                className="text-xs"
                onClick={() => {
                  setSelectedCategory('');
                  setSearchDistrict('');
                  setMinPrice('');
                  setMaxPrice('');
                }}
              >
                ফিল্টার মুছুন
              </Button>
              <Button variant="primary" type="submit" className="text-xs flex items-center gap-1.5">
                <Search className="w-3.5 h-3.5" />
                অনুসন্ধান করুন
              </Button>
            </div>
          </div>

          {/* Saved Buyer Searches Section */}
          {savedSearches.length > 0 && (
            <div className="pt-3 border-t border-slate-100 mt-2 space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className="flex items-center gap-1.5 text-forest-900">
                  <BookmarkCheck className="w-3.5 h-3.5 text-forest-700" />
                  <span>আপনার সংরক্ষিত অনুসন্ধানসমূহ ({savedSearches.length.toLocaleString('bn-BD')} টি):</span>
                </span>
                <span className="text-[11px] text-ink-500 font-normal">
                  ক্লিক করে ফিল্টার সক্রিয় করুন
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {savedSearches.map((s) => (
                  <div
                    key={s.id}
                    className="inline-flex items-center gap-1.5 pl-3 pr-1.5 py-1 rounded-full text-xs bg-leaf-50 border border-leaf-200 text-forest-900 font-medium hover:bg-leaf-100 transition-colors"
                  >
                    <button
                      type="button"
                      onClick={() => handleApplySavedSearch(s)}
                      className="flex items-center gap-1 text-left"
                    >
                      <Bell className="w-3 h-3 text-forest-700" />
                      <span className="font-bold">{s.name}</span>
                      {s.district && <span className="text-ink-500 text-[11px]">({s.district})</span>}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeleteSavedSearch(s.id)}
                      className="p-0.5 rounded-full hover:bg-rose-100 hover:text-rose-700 text-ink-400 ml-1"
                      title="সংরক্ষিত সন্ধান মুছুন"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </form>
      </div>

      {/* Content Section */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 text-sm">
          ফসলের তালিকা খোঁজা হচ্ছে...
        </div>
      ) : error ? (
        <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-rose-700 text-center text-sm">
          {error}
        </div>
      ) : listings.length === 0 ? (
        <div className="py-20 text-center bg-white rounded-3xl border border-slate-200/80 p-8 shadow-xs">
          <ShoppingBag className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-slate-800">কোনো ফসল পাওয়া যায়নি</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            আপনার নির্বাচিত ফিল্টার বা জেলায় বর্তমানে বিক্রয়ের জন্য কোনো ফসল তালিকাভুক্ত নেই। ফিল্টার পরিবর্তন করে আবার চেষ্টা করুন।
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {listings.map((item) => (
            <CropListingCard
              key={item.id}
              listing={item}
              onContact={handleStartContact}
            />
          ))}
        </div>
      )}

      {/* Start Contact Modal */}
      {contactTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-3xl max-w-md w-full shadow-2xl border border-slate-100 p-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <div className="flex items-center gap-2">
                <MessageCircle className="w-5 h-5 text-emerald-600" />
                <h3 className="text-lg font-bold text-slate-900">কৃষকের সাথে বার্তা শুরু করুন</h3>
              </div>
              <button
                onClick={() => setContactTarget(null)}
                className="p-1 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-slate-50 rounded-xl p-3 border border-slate-100 mb-4 text-xs">
              <span className="font-bold text-slate-800 block text-sm">{contactTarget.cropName}</span>
              <span className="text-slate-500">
                {contactTarget.quantity} {contactTarget.quantityUnit} • ৳{contactTarget.pricePerUnit} / একক
              </span>
            </div>

            {contactError && (
              <div className="mb-3 p-2.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs">
                {contactError}
              </div>
            )}

            <form onSubmit={handleSendInitialMessage} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  প্রাথমিক বার্তা
                </label>
                <textarea
                  rows={4}
                  required
                  value={initialMessage}
                  onChange={(e) => setInitialMessage(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <Button
                  variant="outline"
                  type="button"
                  onClick={() => setContactTarget(null)}
                  disabled={sendingMsg}
                >
                  বাতিল
                </Button>
                <Button variant="primary" type="submit" disabled={sendingMsg}>
                  {sendingMsg ? 'পাঠানো হচ্ছে...' : 'ইনবক্সে যান'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Save Search Modal */}
      {showSaveModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-900/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-canvas border border-line-200 rounded-card max-w-md w-full p-6 shadow-float space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-line-200">
              <div className="flex items-center gap-2">
                <Bookmark className="w-5 h-5 text-forest-700" />
                <h3 className="text-base font-bold text-forest-900">অনুসন্ধান সংরক্ষণ করুন</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowSaveModal(false)}
                className="p-1 rounded-btn text-ink-600 hover:bg-surface"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {saveSuccessMsg ? (
              <div className="py-6 text-center space-y-2">
                <CheckCircle2 className="w-10 h-10 text-forest-700 mx-auto" />
                <p className="text-sm font-bold text-forest-900">{saveSuccessMsg}</p>
              </div>
            ) : (
              <form onSubmit={handleSaveCurrentSearch} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-ink-900 mb-1">
                    সংরক্ষণের নাম বা শিরোনাম
                  </label>
                  <input
                    type="text"
                    required
                    value={saveSearchName}
                    onChange={(e) => setSaveSearchName(e.target.value)}
                    placeholder="যেমন: বগুড়ার ডায়মন্ড আলু, আমন ধান"
                    className="w-full px-3 py-2 text-sm rounded-btn border border-line-200 bg-surface focus:outline-none focus:ring-2 focus:ring-leaf-500/50 min-h-[44px]"
                  />
                </div>

                <div className="p-3 bg-surface rounded-btn border border-line-200 text-xs text-ink-600 space-y-1">
                  <div className="font-semibold text-forest-900">সক্রিয় ফিল্টারসমূহ:</div>
                  <div>• বিভাগ: {selectedCategory ? CROP_CATEGORY_LABELS[selectedCategory as CropCategory] : 'যেকোনো বিভাগ'}</div>
                  <div>• জেলা: {searchDistrict || 'যেকোনো জেলা'}</div>
                  {maxPrice && <div>• সর্বোচ্চ মূল্য: ৳{maxPrice}</div>}
                  <p className="text-[11px] text-forest-800 pt-1">
                    🔔 এই ক্রাইটেরিয়ার সাথে মিলে কোনো কৃষক নতুন ফসল পোস্ট করলেই আপনার নোটিফিকেশনে স্বয়ংক্রিয় এলার্ট পৌঁছে যাবে।
                  </p>
                </div>

                <div className="flex items-center justify-end gap-2 pt-2 border-t border-line-200">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowSaveModal(false)}
                    disabled={savingSearch}
                  >
                    বাতিল
                  </Button>
                  <Button
                    type="submit"
                    variant="primary"
                    disabled={savingSearch || !saveSearchName.trim()}
                  >
                    {savingSearch ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin mr-1.5" />
                        <span>সংরক্ষণ হচ্ছে...</span>
                      </>
                    ) : (
                      'সংরক্ষণ নিশ্চিত করুন'
                    )}
                  </Button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
