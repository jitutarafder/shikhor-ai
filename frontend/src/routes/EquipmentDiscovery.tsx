import React, { useEffect, useState, useTransition } from 'react';
import { Link } from 'react-router-dom';
import {
  Tractor,
  MapPin,
  List,
  Map,
  PlusCircle,
  FileText,
  AlertCircle,
  Loader2,
  SlidersHorizontal,
} from 'lucide-react';
import { useAuth } from '../features/auth/AuthContext';
import { EquipmentItem, EquipmentType, PriceUnit } from '../features/equipment/types';
import { searchEquipmentApi } from '../features/equipment/api';
import { EquipmentCard } from '../features/equipment/components/EquipmentCard';
import { RentalModal } from '../features/rentals/components/RentalModal';
import { Button } from '../components/ui/Button';

export const EquipmentDiscovery: React.FC = () => {
  const { user } = useAuth();
  const [, startTransition] = useTransition();

  // Search parameters
  const [equipmentType, setEquipmentType] = useState<EquipmentType>('tractor');
  const [priceUnit, setPriceUnit] = useState<PriceUnit>('per_hour');
  const [maxRadiusKm, setMaxRadiusKm] = useState<number>(25);

  // User location defaults (Bogura farming hub coordinates: 24.85, 89.37)
  const [latitude, setLatitude] = useState<number>(24.85);
  const [longitude, setLongitude] = useState<number>(89.37);
  const [locationName, setLocationName] = useState<string>('বগুড়া সদর');

  // UI state
  const [viewMode, setViewMode] = useState<'list' | 'map'>('list');
  const [equipmentList, setEquipmentList] = useState<EquipmentItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Rental booking modal state
  const [selectedEquipmentForBooking, setSelectedEquipmentForBooking] =
    useState<EquipmentItem | null>(null);

  const fetchEquipment = async () => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const data = await searchEquipmentApi({
        equipmentType,
        priceUnit,
        latitude,
        longitude,
        maxRadiusKm,
      });
      setEquipmentList(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'যন্ত্রের তালিকা অনুসন্ধানে ব্যর্থ হয়েছে।');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEquipment();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [equipmentType, priceUnit, maxRadiusKm, latitude, longitude]);

  // GPS acquisition helper
  const handleAcquireGps = () => {
    if (!navigator.geolocation) {
      alert('আপনার ব্রাউজারে জিপিএস সুবিধা সমর্থিত নয়। ডিফল্ট অবস্থান ব্যবহৃত হচ্ছে।');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        startTransition(() => {
          setLatitude(pos.coords.latitude);
          setLongitude(pos.coords.longitude);
          setLocationName('বর্তমান অবস্থান (জিপিএস)');
        });
      },
      () => {
        alert('জিপিএস লোকেশন পাওয়া যায়নি। ডিফল্ট অবস্থান বজায় রাখা হচ্ছে।');
      }
    );
  };

  const typeTabs: { type: EquipmentType; label: string }[] = [
    { type: 'tractor', label: 'ট্রাক্টর' },
    { type: 'harvester', label: 'হার্ভেস্টার' },
    { type: 'power_tiller', label: 'পাওয়ার টিলার' },
    { type: 'pump', label: 'সেচ পাম্প' },
    { type: 'sprayer', label: 'স্প্রেয়ার' },
  ];

  const unitTabs: { unit: PriceUnit; label: string }[] = [
    { unit: 'per_hour', label: 'প্রতি ঘণ্টা' },
    { unit: 'per_day', label: 'প্রতি দিন' },
    { unit: 'per_acre', label: 'প্রতি একর' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fadeIn">
      {/* Top Header & Navigation Shortcuts */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-line-200">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-btn bg-paddy-400/20 text-soil-700 flex items-center justify-center">
              <Tractor className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-forest-900">কাছের কৃষিযন্ত্র আবিষ্কার</h1>
              <p className="text-xs text-ink-600">
                স্বচ্ছ ৬৫% মূল্য ও ৩৫% দূরত্ব ফর্মুলায় নিকটস্থ যন্ত্রপাতি খুঁজুন
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Link to="/app/rental-requests">
            <Button variant="outline" size="sm" className="text-xs">
              <FileText className="w-3.5 h-3.5 mr-1 text-forest-700" />
              <span>আমার ভাড়ার অনুরোধ</span>
            </Button>
          </Link>

          {user?.role === 'owner' && (
            <Link to="/app/my-equipment">
              <Button variant="secondary" size="sm" className="text-xs">
                <PlusCircle className="w-3.5 h-3.5 mr-1" />
                <span>আমার যন্ত্র তালিকা</span>
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* Search Filters Section */}
      <div className="bg-canvas border border-line-200 rounded-card p-5 space-y-4 shadow-soft">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <h2 className="text-sm font-bold text-forest-900 flex items-center gap-1.5">
            <SlidersHorizontal className="w-4 h-4 text-forest-700" />
            <span>অনুসন্ধান ফিল্টার</span>
          </h2>

          {/* List vs Map view toggle */}
          <div className="flex items-center bg-surface p-1 rounded-btn border border-line-200 text-xs">
            <button
              onClick={() => setViewMode('list')}
              className={`flex items-center gap-1 px-3 py-1.5 rounded min-h-[36px] transition-colors ${
                viewMode === 'list'
                  ? 'bg-canvas text-forest-900 font-bold shadow-sm'
                  : 'text-ink-600 hover:text-ink-900'
              }`}
            >
              <List className="w-3.5 h-3.5" />
              <span>তালিকা</span>
            </button>
            <button
              onClick={() => setViewMode('map')}
              className={`flex items-center gap-1 px-3 py-1.5 rounded min-h-[36px] transition-colors ${
                viewMode === 'map'
                  ? 'bg-canvas text-forest-900 font-bold shadow-sm'
                  : 'text-ink-600 hover:text-ink-900'
              }`}
            >
              <Map className="w-3.5 h-3.5" />
              <span>মানচিত্র</span>
            </button>
          </div>
        </div>

        {/* Equipment Type Selector Tabs */}
        <div>
          <label className="block text-xs font-semibold text-ink-900 mb-2">যন্ত্রের ধরন:</label>
          <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
            {typeTabs.map((tab) => (
              <button
                key={tab.type}
                onClick={() => setEquipmentType(tab.type)}
                className={`px-4 py-2 rounded-btn text-xs font-medium whitespace-nowrap min-h-[44px] transition-colors border ${
                  equipmentType === tab.type
                    ? 'bg-forest-700 text-canvas border-forest-700 shadow-sm'
                    : 'bg-surface text-ink-900 border-line-200 hover:border-forest-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Pricing Unit & Radius Controls */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 border-t border-line-200">
          <div>
            <label className="block text-xs font-semibold text-ink-900 mb-1.5">
              মূল্য হিসাবের একক (নিয়ম ১৫ অনুসারে পৃথক):
            </label>
            <div className="grid grid-cols-3 gap-1.5">
              {unitTabs.map((u) => (
                <button
                  key={u.unit}
                  onClick={() => setPriceUnit(u.unit)}
                  className={`py-2 px-1 text-center text-xs rounded-btn border min-h-[44px] transition-colors ${
                    priceUnit === u.unit
                      ? 'bg-leaf-100 text-forest-900 font-bold border-leaf-500/40'
                      : 'bg-surface text-ink-600 border-line-200 hover:bg-canvas'
                  }`}
                >
                  {u.label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink-900 mb-1.5">
              কভারেজ ব্যাসার্ধ (সর্বোচ্চ দূরত্ব):
            </label>
            <select
              value={maxRadiusKm}
              onChange={(e) => setMaxRadiusKm(Number(e.target.value))}
              className="w-full px-3 py-2 text-sm rounded-btn border border-line-200 bg-surface focus:outline-none focus:ring-2 focus:ring-leaf-500/50 min-h-[44px]"
            >
              <option value={10}>১০ কিলোমিটারের মধ্যে</option>
              <option value={25}>২৫ কিলোমিটারের মধ্যে (প্রস্তাবিত)</option>
              <option value={50}>৫০ কিলোমিটারের মধ্যে</option>
              <option value={100}>১০০ কিলোমিটার পর্যন্ত</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-ink-900 mb-1.5">আপনার অবস্থান:</label>
            <div className="flex items-center gap-2">
              <div className="flex-1 px-3 py-2 text-xs rounded-btn border border-line-200 bg-surface text-ink-900 min-h-[44px] flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-forest-700 shrink-0" />
                <span className="truncate">{locationName}</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleAcquireGps}
                className="shrink-0 text-xs"
                title="জিপিএস দিয়ে অবস্থান নির্ণয়"
              >
                জিপিএস
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Error state banner */}
      {errorMessage && (
        <div className="p-4 bg-danger-600/10 border border-danger-600/20 rounded-card text-xs text-danger-600 flex items-start gap-2.5">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <strong className="block font-semibold">অনুসন্ধানে সমস্যা হয়েছে</strong>
            <span>{errorMessage}</span>
          </div>
        </div>
      )}

      {/* Main Results View */}
      {isLoading ? (
        <div className="py-16 text-center space-y-3">
          <Loader2 className="w-8 h-8 text-forest-700 animate-spin mx-auto" />
          <p className="text-sm text-ink-600">নিকটস্থ যন্ত্রপাতি অনুসন্ধান ও র‍্যাঙ্কিং করা হচ্ছে...</p>
        </div>
      ) : equipmentList.length === 0 ? (
        <div className="py-16 text-center space-y-4 bg-canvas border border-line-200 rounded-card p-8">
          <Tractor className="w-12 h-12 text-ink-400 mx-auto" />
          <div className="space-y-1">
            <h3 className="text-base font-bold text-forest-900">কোনো যন্ত্রপাতি পাওয়া যায়নি</h3>
            <p className="text-xs text-ink-600 max-w-md mx-auto leading-relaxed">
              নির্বাচিত এলাকায় বর্তমানে কোনো সচল যন্ত্রপাতি নেই। অনুসন্ধানের দূরত্ব ব্যাসার্ধ বৃদ্ধি করুন অথবা অন্য একক নির্বাচন করুন।
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={() => setMaxRadiusKm(50)}>
            ব্যাসার্ধ ৫০ কিমি করুন
          </Button>
        </div>
      ) : viewMode === 'list' ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-ink-600">
            <span>
              মোট <strong className="text-forest-900">{equipmentList.length}</strong> টি যন্ত্র পাওয়া গেছে (স্বচ্ছ র‍্যাঙ্কিং অনুযায়ী সাজানো)
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {equipmentList.map((item) => (
              <EquipmentCard
                key={item.id}
                equipment={item}
                onBook={(eq) => setSelectedEquipmentForBooking(eq)}
              />
            ))}
          </div>
        </div>
      ) : (
        /* Map / Area overview placeholder adhering to Rule 17 (Approximate coordinates) */
        <div className="bg-canvas border border-line-200 rounded-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-forest-900 flex items-center gap-2">
              <Map className="w-5 h-5 text-forest-700" />
              <span>আশেপাশের মানচিত্র ভিউ (আনুমানিক অবস্থান)</span>
            </h3>
            <span className="text-xs text-ink-600 bg-field-wash px-2.5 py-1 rounded">
              গোপনীয়তার সুরক্ষায় আনুমানিক ১.১ কিমি গ্রিড প্রদর্শন
            </span>
          </div>

          <div className="bg-field-wash border border-line-200 rounded-card h-[380px] flex flex-col items-center justify-center p-6 text-center space-y-3">
            <MapPin className="w-10 h-10 text-forest-700 animate-bounce" />
            <div className="space-y-1">
              <h4 className="text-sm font-bold text-forest-900">
                মানচিত্র ভিউতে {equipmentList.length} টি সম্ভাব্য যন্ত্র চিহ্নিত
              </h4>
              <p className="text-xs text-ink-600 max-w-md mx-auto">
                সঠিক যোগাযোগ ও বুকিংয়ের জন্য তালিকা ভিউ ব্যবহার করুন। মালিকদের ব্যক্তিগত বাড়ির অবস্থান কখনই মানচিত্রে উন্মুক্ত করা হয় না।
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={() => setViewMode('list')}>
              তালিকায় ফিরে যান
            </Button>
          </div>
        </div>
      )}

      {/* Rental Booking Modal */}
      {selectedEquipmentForBooking && (
        <RentalModal
          equipment={selectedEquipmentForBooking}
          onClose={() => setSelectedEquipmentForBooking(null)}
          onSuccess={() => {
            setSelectedEquipmentForBooking(null);
            alert('ভাড়ার অনুরোধ সফল হয়েছে! আপনি ভাড়ার অনুরোধ পৃষ্ঠায় অগ্রগতি দেখতে পারেন।');
          }}
        />
      )}
    </div>
  );
};
