import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Tractor,
  Plus,
  Play,
  Pause,
  MapPin,
  AlertCircle,
  Loader2,
  FileText,
  DollarSign,
  ArrowLeft,
} from 'lucide-react';
import { useAuth } from '../features/auth/AuthContext';
import {
  EquipmentCreateInput,
  EquipmentItem,
  EquipmentType,
  PriceUnit,
} from '../features/equipment/types';
import {
  createEquipmentApi,
  getMyEquipmentApi,
  updateEquipmentApi,
} from '../features/equipment/api';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export const MyEquipment: React.FC = () => {
  const { token, isAuthenticated } = useAuth();

  const [equipmentList, setEquipmentList] = useState<EquipmentItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // New Equipment Form Modal
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  // Form fields
  const [name, setName] = useState('');
  const [equipmentType, setEquipmentType] = useState<EquipmentType>('tractor');
  const [description, setDescription] = useState('');
  const [priceAmount, setPriceAmount] = useState<number>(1500);
  const [priceUnit, setPriceUnit] = useState<PriceUnit>('per_hour');
  const [district, setDistrict] = useState('বগুড়া');
  const [upazila, setUpazila] = useState('সদর');
  const [latitude, setLatitude] = useState<number>(24.85);
  const [longitude, setLongitude] = useState<number>(89.37);
  const [serviceRadiusKm, setServiceRadiusKm] = useState<number>(20);

  const fetchMyEquipment = async () => {
    if (!token) return;
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await getMyEquipmentApi(token);
      setEquipmentList(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'যন্ত্র তালিকা লোড করা যায়নি।');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMyEquipment();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const payload: EquipmentCreateInput = {
        name,
        equipmentType,
        description: description.trim() || undefined,
        priceAmount,
        priceUnit,
        district,
        upazila,
        latitude,
        longitude,
        serviceRadiusKm,
      };

      await createEquipmentApi(token, payload);
      setShowAddModal(false);
      // Reset form
      setName('');
      setDescription('');
      await fetchMyEquipment();
    } catch (err: any) {
      setErrorMsg(err.message || 'যন্ত্র নিবন্ধন ব্যর্থ হয়েছে।');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTogglePause = async (item: EquipmentItem) => {
    if (!token) return;
    try {
      await updateEquipmentApi(token, item.id, {
        isPaused: !item.isPaused,
      });
      await fetchMyEquipment();
    } catch (err: any) {
      alert(err.message || 'হালনাগাদ ব্যর্থ হয়েছে।');
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="max-w-md mx-auto py-16 px-4 text-center space-y-4">
        <h2 className="text-xl font-bold text-forest-900">লগ ইন প্রয়োজন</h2>
        <p className="text-xs text-ink-600">আপনার যন্ত্র পরিচালনা করতে প্রথমে অ্যাকাউন্টে প্রবেশ করুন।</p>
        <Link to="/login">
          <Button variant="primary" fullWidth size="md">লগ ইন পৃষ্ঠায় যান</Button>
        </Link>
      </div>
    );
  }

  const typeLabels: Record<string, string> = {
    tractor: 'ট্রাক্টর',
    harvester: 'হার্ভেস্টার',
    pump: 'সেচ পাম্প',
    sprayer: 'স্প্রেয়ার',
    power_tiller: 'পাওয়ার টিলার',
  };

  const unitLabels: Record<string, string> = {
    per_hour: 'ঘণ্টা',
    per_day: 'দিন',
    per_acre: 'একর',
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-line-200">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Link to="/app" className="text-ink-600 hover:text-forest-900">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <h1 className="text-2xl font-bold text-forest-900">আমার কৃষিযন্ত্র ব্যবস্থাপনা</h1>
          </div>
          <p className="text-xs text-ink-600">
            আপনার নিবন্ধিত যন্ত্রপাতি পরিচালনা করুন, ভাড়া সাময়িক স্থগিত করুন অথবা নতুন যন্ত্র যোগ করুন
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link to="/app/rental-requests">
            <Button variant="outline" size="sm" className="text-xs">
              <FileText className="w-3.5 h-3.5 mr-1 text-forest-700" />
              <span>ভাড়ার অনুরোধসমূহ</span>
            </Button>
          </Link>

          <Button
            variant="primary"
            size="sm"
            onClick={() => setShowAddModal(true)}
            className="text-xs"
          >
            <Plus className="w-4 h-4 mr-1" />
            <span>নতুন যন্ত্র যুক্ত করুন</span>
          </Button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 bg-danger-600/10 border border-danger-600/20 rounded-card text-xs text-danger-600 flex items-start gap-2.5">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Equipment List */}
      {isLoading ? (
        <div className="py-16 text-center space-y-3">
          <Loader2 className="w-8 h-8 text-forest-700 animate-spin mx-auto" />
          <p className="text-sm text-ink-600">যন্ত্রের তথ্য লোড করা হচ্ছে...</p>
        </div>
      ) : equipmentList.length === 0 ? (
        <div className="py-16 text-center space-y-4 bg-canvas border border-line-200 rounded-card p-8">
          <Tractor className="w-12 h-12 text-ink-400 mx-auto" />
          <div className="space-y-1">
            <h3 className="text-base font-bold text-forest-900">কোনো যন্ত্র তালিকাভুক্ত নেই</h3>
            <p className="text-xs text-ink-600 max-w-md mx-auto">
              আপনার ট্রাক্টর, পাওয়ার টিলার বা সেচ পাম্প যুক্ত করে স্থানীয় কৃষকদের কাছে ভাড়া দিন।
            </p>
          </div>
          <Button variant="primary" size="md" onClick={() => setShowAddModal(true)}>
            <Plus className="w-4 h-4 mr-1" />
            <span>প্রথম যন্ত্র যুক্ত করুন</span>
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {equipmentList.map((item) => (
            <Card key={item.id} className="p-5 border-line-200 bg-canvas space-y-4">
              <div className="flex items-center justify-between">
                <Badge variant="success">
                  {typeLabels[item.equipmentType] || item.equipmentType}
                </Badge>
                {item.isPaused ? (
                  <span className="text-[11px] font-semibold text-danger-600 bg-danger-600/10 px-2 py-0.5 rounded-full">
                    ভাড়া স্থগিত
                  </span>
                ) : (
                  <span className="text-[11px] font-semibold text-forest-700 bg-leaf-100 px-2 py-0.5 rounded-full">
                    সক্রিয়
                  </span>
                )}
              </div>

              <div>
                <h3 className="text-base font-bold text-forest-900">{item.name}</h3>
                {item.description && (
                  <p className="text-xs text-ink-600 line-clamp-2 mt-1 leading-relaxed">
                    {item.description}
                  </p>
                )}
              </div>

              <div className="space-y-1 text-xs text-ink-600">
                <div className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-forest-700 shrink-0" />
                  <span>
                    {item.district}, {item.upazila} (ব্যাসার্ধ {item.serviceRadiusKm} কিমি)
                  </span>
                </div>
                <div className="flex items-center gap-1.5 text-forest-900 font-medium">
                  <DollarSign className="w-3.5 h-3.5 text-forest-700 shrink-0" />
                  <span>
                    {item.priceAmount.toLocaleString('bn-BD')} ৳ / {unitLabels[item.priceUnit] || item.priceUnit}
                  </span>
                </div>
              </div>

              <div className="pt-3 border-t border-line-200 flex items-center justify-between">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleTogglePause(item)}
                  className="text-xs min-h-[38px]"
                >
                  {item.isPaused ? (
                    <>
                      <Play className="w-3.5 h-3.5 mr-1 text-forest-700" />
                      <span>চালু করুন</span>
                    </>
                  ) : (
                    <>
                      <Pause className="w-3.5 h-3.5 mr-1 text-paddy-400" />
                      <span>স্থগিত রাখুন</span>
                    </>
                  )}
                </Button>

                <span className="text-[11px] text-ink-600">
                  নিবন্ধন: {new Date(item.createdAt).toLocaleDateString('bn-BD')}
                </span>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Add New Equipment Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-900/60 backdrop-blur-sm animate-fadeIn">
          <div className="bg-canvas border border-line-200 rounded-card max-w-lg w-full p-6 shadow-float space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-line-200">
              <h3 className="text-lg font-bold text-forest-900">নতুন কৃষিযন্ত্র যুক্ত করুন</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-ink-600 hover:text-ink-900 min-w-[36px] min-h-[36px]"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-ink-900 mb-1">যন্ত্রের নাম / মডেল *</label>
                <input
                  type="text"
                  required
                  placeholder="যেমন: মাহিন্দ্রা ৫৭৫ ডিআই ট্রাক্টর"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-btn border border-line-200 bg-surface min-h-[44px]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-ink-900 mb-1">যন্ত্রের ধরন *</label>
                  <select
                    value={equipmentType}
                    onChange={(e) => setEquipmentType(e.target.value as EquipmentType)}
                    className="w-full px-3 py-2 text-sm rounded-btn border border-line-200 bg-surface min-h-[44px]"
                  >
                    <option value="tractor">ট্রাক্টর</option>
                    <option value="harvester">হার্ভেস্টার</option>
                    <option value="power_tiller">পাওয়ার টিলার</option>
                    <option value="pump">সেচ পাম্প</option>
                    <option value="sprayer">স্প্রেয়ার</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-ink-900 mb-1">মূল্যের একক *</label>
                  <select
                    value={priceUnit}
                    onChange={(e) => setPriceUnit(e.target.value as PriceUnit)}
                    className="w-full px-3 py-2 text-sm rounded-btn border border-line-200 bg-surface min-h-[44px]"
                  >
                    <option value="per_hour">প্রতি ঘণ্টা</option>
                    <option value="per_day">প্রতি দিন</option>
                    <option value="per_acre">প্রতি একর</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-ink-900 mb-1">ভাড়ার হার (টাকায়) *</label>
                  <input
                    type="number"
                    required
                    min={50}
                    value={priceAmount}
                    onChange={(e) => setPriceAmount(Number(e.target.value))}
                    className="w-full px-3 py-2 text-sm rounded-btn border border-line-200 bg-surface min-h-[44px]"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-ink-900 mb-1">সার্ভিস ব্যাসার্ধ (কিমি) *</label>
                  <input
                    type="number"
                    required
                    min={1}
                    max={100}
                    value={serviceRadiusKm}
                    onChange={(e) => setServiceRadiusKm(Number(e.target.value))}
                    className="w-full px-3 py-2 text-sm rounded-btn border border-line-200 bg-surface min-h-[44px]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-ink-900 mb-1">জেলা *</label>
                  <input
                    type="text"
                    required
                    value={district}
                    onChange={(e) => setDistrict(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-btn border border-line-200 bg-surface min-h-[44px]"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-ink-900 mb-1">উপজেলা *</label>
                  <input
                    type="text"
                    required
                    value={upazila}
                    onChange={(e) => setUpazila(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-btn border border-line-200 bg-surface min-h-[44px]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-ink-900 mb-1">অক্ষাংশ (Latitude)</label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    value={latitude}
                    onChange={(e) => setLatitude(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 text-sm rounded-btn border border-line-200 bg-surface min-h-[44px]"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-ink-900 mb-1">দ্রাঘিমাংশ (Longitude)</label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    value={longitude}
                    onChange={(e) => setLongitude(parseFloat(e.target.value) || 0)}
                    className="w-full px-3 py-2 text-sm rounded-btn border border-line-200 bg-surface min-h-[44px]"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-ink-900 mb-1">বিবরণ (ঐচ্ছিক)</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="যন্ত্রের বর্তমান অবস্থা ও অন্যান্য শর্তাবলী..."
                  className="w-full px-3 py-2 text-sm rounded-btn border border-line-200 bg-surface min-h-[70px]"
                />
              </div>

              <div className="p-3 bg-field-wash rounded border border-line-200 text-ink-600">
                <p>
                  <strong>নোট:</strong> অনুসন্ধানের সময় আপনার সঠিক বাড়ির অবস্থান প্রকাশ করা হবে না; কৃষকরা আনুমানিক ১.১ কিমি গ্রিড ও দূরত্ব দেখতে পাবেন।
                </p>
              </div>

              <div className="pt-2 flex items-center gap-3">
                <Button
                  type="button"
                  variant="outline"
                  fullWidth
                  onClick={() => setShowAddModal(false)}
                >
                  বাতিল
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  fullWidth
                  isLoading={isSubmitting}
                >
                  নিবন্ধন সম্পন্ন করুন
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
