import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CropListingCreateInput,
  CropListingItem,
  CropListingStatus,
} from '../features/crop-marketplace/types';
import {
  createCropListingApi,
  getMyCropListingsApi,
  updateCropListingApi,
} from '../features/crop-marketplace/api';
import { CropListingCard } from '../features/crop-marketplace/components/CropListingCard';
import { CreateCropListingModal } from '../features/crop-marketplace/components/CreateCropListingModal';
import { Button } from '../components/ui/Button';
import { PlusCircle, ShoppingBag, ArrowLeft, X } from 'lucide-react';

export const MyCropListings: React.FC = () => {
  const navigate = useNavigate();
  const token = localStorage.getItem('shikhor_token');
  const [listings, setListings] = useState<CropListingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Creation Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  // Status/Edit Modal
  const [editTarget, setEditTarget] = useState<CropListingItem | null>(null);
  const [editStatus, setEditStatus] = useState<CropListingStatus>('active');
  const [editPrice, setEditPrice] = useState<number>(0);
  const [editQuantity, setEditQuantity] = useState<number>(0);
  const [updating, setUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }
    fetchMyListings();
  }, [token]);

  const fetchMyListings = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setError(null);
      const data = await getMyCropListingsApi(token);
      setListings(data);
    } catch (err: any) {
      setError(err?.message || 'আপনার ফসলের তালিকা লোড করা যায়নি।');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSubmit = async (input: CropListingCreateInput) => {
    if (!token) return;
    await createCropListingApi(token, input);
    await fetchMyListings();
  };

  const handleOpenEdit = (listing: CropListingItem) => {
    setEditTarget(listing);
    setEditStatus(listing.status);
    setEditPrice(listing.pricePerUnit);
    setEditQuantity(listing.quantity);
    setUpdateError(null);
  };

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !editTarget) return;

    try {
      setUpdating(true);
      setUpdateError(null);
      await updateCropListingApi(token, editTarget.id, {
        status: editStatus,
        pricePerUnit: Math.round(Number(editPrice)),
        quantity: Number(editQuantity),
      });
      setEditTarget(null);
      await fetchMyListings();
    } catch (err: any) {
      setUpdateError(err?.message || 'হালনাগাদ করা যায়নি।');
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <button
            onClick={() => navigate('/app/crops')}
            className="text-xs text-slate-500 hover:text-emerald-700 flex items-center gap-1.5 mb-2 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            ফসল বাজারে ফিরে যান
          </button>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
            আমার ফসলের তালিকা ও পরিচালনা
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            আপনার বিক্রয়যোগ্য ফসলের তালিকা পরিচালনা করুন, দাম বা অবস্থা হালনাগাদ করুন
          </p>
        </div>

        <Button
          variant="primary"
          className="flex items-center gap-2 self-start sm:self-auto"
          onClick={() => setIsCreateOpen(true)}
        >
          <PlusCircle className="w-4 h-4" />
          নতুন ফসল যোগ করুন
        </Button>
      </div>

      {/* Content */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 text-sm">লোড হচ্ছে...</div>
      ) : error ? (
        <div className="p-6 bg-rose-50 border border-rose-200 rounded-2xl text-rose-700 text-center text-sm">
          {error}
        </div>
      ) : listings.length === 0 ? (
        <div className="py-20 text-center bg-white rounded-3xl border border-slate-200/80 p-8 shadow-xs">
          <ShoppingBag className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-slate-800">আপনি এখনো কোনো ফসল যোগ করেননি</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto mb-6">
            আপনার খেত বা গুদামে থাকা ফসলের তথ্য দিয়ে নতুন তালিকা প্রকাশ করুন যাতে পাইকাররা আপনার সাথে যোগাযোগ করতে পারেন।
          </p>
          <Button variant="primary" onClick={() => setIsCreateOpen(true)}>
            প্রথম ফসল যোগ করুন
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {listings.map((item) => (
            <CropListingCard
              key={item.id}
              listing={item}
              isOwner={true}
              onEdit={handleOpenEdit}
            />
          ))}
        </div>
      )}

      {/* Creation Modal */}
      <CreateCropListingModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSubmit={handleCreateSubmit}
      />

      {/* Edit Status & Price Modal */}
      {editTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-3xl max-w-md w-full shadow-2xl border border-slate-100 p-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <div>
                <h3 className="text-lg font-bold text-slate-900">ফসলের তথ্য পরিবর্তন</h3>
                <span className="text-xs text-slate-500">{editTarget.cropName}</span>
              </div>
              <button
                onClick={() => setEditTarget(null)}
                className="p-1 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {updateError && (
              <div className="mb-3 p-2.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs">
                {updateError}
              </div>
            )}

            <form onSubmit={handleSaveEdit} className="space-y-4 text-sm">
              <div>
                <label className="block text-slate-700 font-semibold mb-1 text-xs">
                  বিক্রয় অবস্থা
                </label>
                <select
                  value={editStatus}
                  onChange={(e) => setEditStatus(e.target.value as CropListingStatus)}
                  className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white"
                >
                  <option value="active">সক্রিয় (বিক্রয়ের জন্য উন্মুক্ত)</option>
                  <option value="paused">স্থগিত (সাময়িক বন্ধ)</option>
                  <option value="closed">সম্পন্ন (বিক্রয় শেষ)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1 text-xs">
                  অবশিষ্ট পরিমাণ ({editTarget.quantityUnit})
                </label>
                <input
                  type="number"
                  step="any"
                  min="0"
                  required
                  value={editQuantity}
                  onChange={(e) => setEditQuantity(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1 text-xs">
                  একক প্রতি মূল্য (টাকা)
                </label>
                <input
                  type="number"
                  min="1"
                  required
                  value={editPrice}
                  onChange={(e) => setEditPrice(parseInt(e.target.value, 10) || 0)}
                  className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <Button
                  variant="outline"
                  type="button"
                  onClick={() => setEditTarget(null)}
                  disabled={updating}
                >
                  বাতিল
                </Button>
                <Button variant="primary" type="submit" disabled={updating}>
                  {updating ? 'সংরক্ষণ হচ্ছে...' : 'হালনাগাদ করুন'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
