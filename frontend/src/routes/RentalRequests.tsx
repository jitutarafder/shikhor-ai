import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Calendar,
  Clock,
  DollarSign,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  ArrowLeft,
  Check,
  Ban,
  ArrowRight,
  Star,
} from 'lucide-react';
import { useAuth } from '../features/auth/AuthContext';
import { RentalRequestItem, RentalStatus } from '../features/rentals/types';
import { getMyRentalsApi, updateRentalStatusApi } from '../features/rentals/api';
import { EquipmentReviewModal } from '../features/rentals/components/EquipmentReviewModal';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export const RentalRequests: React.FC = () => {
  const { user, token, isAuthenticated } = useAuth();

  const [rentals, setRentals] = useState<RentalRequestItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [reviewingRental, setReviewingRental] = useState<RentalRequestItem | null>(null);

  const fetchRentals = async () => {
    if (!token) return;
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const data = await getMyRentalsApi(token);
      setRentals(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'ভাড়ার তালিকা লোড করা যায়নি।');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRentals();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const handleStatusTransition = async (rentalId: string, targetStatus: RentalStatus) => {
    if (!token) return;
    setUpdatingId(rentalId);
    try {
      await updateRentalStatusApi(token, rentalId, targetStatus);
      await fetchRentals();
    } catch (err: any) {
      alert(err.message || 'অবস্থা পরিবর্তন ব্যর্থ হয়েছে।');
    } finally {
      setUpdatingId(null);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="max-w-md mx-auto py-16 px-4 text-center space-y-4">
        <h2 className="text-xl font-bold text-forest-900">লগ ইন প্রয়োজন</h2>
        <p className="text-xs text-ink-600">ভাড়ার অনুরোধ দেখতে অনুগ্রহ করে লগ ইন করুন।</p>
        <Link to="/login">
          <Button variant="primary" fullWidth size="md">লগ ইন পৃষ্ঠায় যান</Button>
        </Link>
      </div>
    );
  }

  const statusConfig: Record<
    RentalStatus,
    { label: string; variant: 'warning' | 'success' | 'danger' | 'info' | 'neutral' }
  > = {
    pending: { label: 'মালিকের সম্মতির অপেক্ষায়', variant: 'warning' },
    accepted: { label: 'গৃহীত / বুকিং নিশ্চিত', variant: 'success' },
    rejected: { label: 'প্রত্যাখ্যাত', variant: 'danger' },
    cancelled: { label: 'বাতিলকৃত', variant: 'neutral' },
    completed: { label: 'কাজ সম্পন্ন', variant: 'info' },
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
            <h1 className="text-2xl font-bold text-forest-900">ভাড়ার অনুরোধ ও বুকিং ট্র্যাকার</h1>
          </div>
          <p className="text-xs text-ink-600">
            আপনার প্রেরিত ও প্রাপ্ত কৃষিযন্ত্র ভাড়ার সব অনুরোধ এবং কাজের সার্বিক অগ্রগতি পর্যবেক্ষণ করুন
          </p>
        </div>

        <Link to="/app/equipment">
          <Button variant="outline" size="sm" className="text-xs">
            <span>নতুন যন্ত্র খুঁজুন</span>
            <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Button>
        </Link>
      </div>

      {errorMsg && (
        <div className="p-4 bg-danger-600/10 border border-danger-600/20 rounded-card text-xs text-danger-600 flex items-start gap-2.5">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Main Content */}
      {isLoading ? (
        <div className="py-16 text-center space-y-3">
          <Loader2 className="w-8 h-8 text-forest-700 animate-spin mx-auto" />
          <p className="text-sm text-ink-600">ভাড়ার অনুরোধসমূহ লোড করা হচ্ছে...</p>
        </div>
      ) : rentals.length === 0 ? (
        <div className="py-16 text-center space-y-4 bg-canvas border border-line-200 rounded-card p-8">
          <FileText className="w-12 h-12 text-ink-400 mx-auto" />
          <div className="space-y-1">
            <h3 className="text-base font-bold text-forest-900">কোনো ভাড়ার অনুরোধ নেই</h3>
            <p className="text-xs text-ink-600 max-w-md mx-auto">
              আপনি এখনো কোনো কৃষিযন্ত্র ভাড়ার অনুরোধ পাঠাননি অথবা আপনার যন্ত্রের জন্য কোনো অনুরোধ আসেনি।
            </p>
          </div>
          <Link to="/app/equipment">
            <Button variant="primary" size="md">যন্ত্র অনুসন্ধান শুরু করুন</Button>
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {rentals.map((r) => {
            const isRenter = user?.id === r.renterId;
            const config = statusConfig[r.status] || { label: r.status, variant: 'neutral' };
            const isBusy = updatingId === r.id;

            return (
              <Card key={r.id} className="p-5 border-line-200 bg-canvas space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-line-200">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-surface border border-line-200 text-ink-600">
                      {isRenter ? 'আমার প্রেরিত অনুরোধ' : 'যন্ত্রের জন্য প্রাপ্ত অনুরোধ'}
                    </span>
                    <Badge variant={config.variant}>{config.label}</Badge>
                    <span className="text-[11px] text-ink-600">আইডি: {r.id.substring(0, 8)}</span>
                  </div>
                  <span className="text-[11px] text-ink-600">
                    তারিখ: {new Date(r.createdAt).toLocaleDateString('bn-BD')}
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                  <div className="space-y-1">
                    <span className="text-ink-600 flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-forest-700" />
                      <span>ভাড়ার নির্ধারিত তারিখ:</span>
                    </span>
                    {r.selectedDates ? (
                      <div className="flex flex-wrap gap-1 pt-0.5">
                        {(typeof r.selectedDates === 'string'
                          ? r.selectedDates.split(',')
                          : r.selectedDates
                        ).map((d) => (
                          <span
                            key={d}
                            className="inline-block px-1.5 py-0.5 rounded bg-leaf-100 text-forest-900 font-semibold text-[11px] border border-leaf-200"
                          >
                            {new Date(d.trim()).toLocaleDateString('bn-BD', { day: 'numeric', month: 'short' })}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="font-bold text-forest-900 text-sm block">{r.rentalDate}</span>
                    )}
                  </div>

                  <div className="space-y-1">
                    <span className="text-ink-600 flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-forest-700" />
                      <span>কাজের মেয়াদ / পরিমাণ:</span>
                    </span>
                    <span className="font-bold text-forest-900 text-sm block">
                      {r.durationUnits} একক
                    </span>
                  </div>

                  <div className="space-y-1">
                    <span className="text-ink-600 flex items-center gap-1.5">
                      <DollarSign className="w-3.5 h-3.5 text-forest-700" />
                      <span>আনুমানিক মোট খরচ:</span>
                    </span>
                    <span className="font-bold text-forest-900 text-sm block">
                      {r.totalEstimatedPrice.toLocaleString('bn-BD')} ৳
                    </span>
                  </div>
                </div>

                {r.note && (
                  <div className="p-3 bg-surface rounded text-xs text-ink-900 border border-line-200">
                    <span className="font-semibold block mb-0.5 text-forest-900">কৃষকের বার্তা:</span>
                    <p className="leading-relaxed">{r.note}</p>
                  </div>
                )}

                {/* State Machine Transition Actions (AGENTS.md Rule 14) */}
                <div className="pt-2 flex items-center justify-end gap-2 flex-wrap">
                  {/* When Pending: Owner can Accept or Reject. Renter can Cancel. */}
                  {r.status === 'pending' && (
                    <>
                      {!isRenter && (
                        <>
                          <Button
                            variant="primary"
                            size="sm"
                            disabled={isBusy}
                            onClick={() => handleStatusTransition(r.id, 'accepted')}
                            className="text-xs"
                          >
                            <Check className="w-3.5 h-3.5 mr-1" />
                            <span>অনুরোধ গ্রহণ করুন</span>
                          </Button>
                          <Button
                            variant="danger"
                            size="sm"
                            disabled={isBusy}
                            onClick={() => handleStatusTransition(r.id, 'rejected')}
                            className="text-xs"
                          >
                            <XCircle className="w-3.5 h-3.5 mr-1" />
                            <span>প্রত্যাখ্যান</span>
                          </Button>
                        </>
                      )}

                      {isRenter && (
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={isBusy}
                          onClick={() => handleStatusTransition(r.id, 'cancelled')}
                          className="text-xs text-danger-600 hover:border-danger-600"
                        >
                          <Ban className="w-3.5 h-3.5 mr-1" />
                          <span>অনুরোধ বাতিল করুন</span>
                        </Button>
                      )}
                    </>
                  )}

                  {/* When Accepted: Either party can Complete or Cancel */}
                  {r.status === 'accepted' && (
                    <>
                      <Button
                        variant="primary"
                        size="sm"
                        disabled={isBusy}
                        onClick={() => handleStatusTransition(r.id, 'completed')}
                        className="text-xs"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                        <span>কাজ সম্পন্ন হয়েছে</span>
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={isBusy}
                        onClick={() => handleStatusTransition(r.id, 'cancelled')}
                        className="text-xs text-danger-600"
                      >
                        <Ban className="w-3.5 h-3.5 mr-1" />
                        <span>বুকিং বাতিল</span>
                      </Button>
                    </>
                  )}

                  {/* When Completed: Renter can leave a review */}
                  {r.status === 'completed' && isRenter && (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => setReviewingRental(r)}
                      className="text-xs bg-amber-600 hover:bg-amber-700 text-white"
                    >
                      <Star className="w-3.5 h-3.5 mr-1 fill-amber-300 text-amber-300" />
                      <span>⭐ রেটিং ও রিভিউ দিন</span>
                    </Button>
                  )}

                  {/* Terminal states: rejected, cancelled, or completed for owner */}
                  {(['rejected', 'cancelled'].includes(r.status) || (r.status === 'completed' && !isRenter)) && (
                    <span className="text-xs text-ink-600 italic">
                      এই অনুরোধের চূড়ান্ত প্রক্রিয়া সম্পন্ন হয়েছে।
                    </span>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {reviewingRental && (
        <EquipmentReviewModal
          rental={reviewingRental}
          onClose={() => setReviewingRental(null)}
          onSuccess={() => {
            setReviewingRental(null);
            fetchRentals();
          }}
        />
      )}
    </div>
  );
};
