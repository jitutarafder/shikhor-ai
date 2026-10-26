import React from 'react';
import { X, Scale, Info, CheckCircle2 } from 'lucide-react';
import { RankingBreakdown } from '../types';

interface EquipmentRankingExplainerProps {
  ranking: RankingBreakdown;
  equipmentName: string;
  onClose: () => void;
}

export const EquipmentRankingExplainer: React.FC<EquipmentRankingExplainerProps> = ({
  ranking,
  equipmentName,
  onClose,
}) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-canvas border border-line-200 rounded-card max-w-lg w-full p-6 shadow-float space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-line-200">
          <div className="flex items-center gap-2 text-forest-900 font-bold text-lg">
            <Scale className="w-5 h-5 text-forest-700" />
            <span>স্বচ্ছ র‍্যাঙ্কিং হিসাবের বিবরণ</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-btn text-ink-600 hover:text-ink-900 hover:bg-surface min-w-[36px] min-h-[36px] flex items-center justify-center"
            aria-label="বন্ধ করুন"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4 text-sm text-ink-900">
          <p className="text-ink-600 leading-relaxed">
            <strong className="text-forest-900">{equipmentName}</strong>-এর জন্য নির্ধারিত র‍্যাঙ্কিং স্কোর:{' '}
            <span className="font-mono font-bold text-forest-700 bg-leaf-100 px-2 py-0.5 rounded">
              {ranking.rankingScore.toFixed(4)}
            </span>{' '}
            (কম স্কোর মানে অধিক অগ্রাধিকার ও উপযুক্ততা)।
          </p>

          <div className="bg-surface rounded-card p-4 space-y-3 border border-line-200">
            <h4 className="font-semibold text-xs text-ink-600 uppercase tracking-wider flex items-center gap-1.5">
              <Info className="w-4 h-4 text-forest-700" />
              <span>অনুমোদিত স্কোরিং সূত্র (নিয়ম ১৫)</span>
            </h4>
            <div className="p-3 bg-canvas border border-line-200 rounded text-xs font-mono text-ink-900 text-center">
              স্কোর = (০.৬৫ × মূল্যের স্কোর) + (০.৩৫ × দূরত্বের স্কোর)
            </div>

            <div className="grid grid-cols-2 gap-3 pt-2 text-xs">
              <div className="p-2.5 rounded bg-leaf-100/50 border border-leaf-500/20">
                <span className="text-ink-600 block">মূল্যের ওজন (৬৫%)</span>
                <span className="font-bold text-forest-900 text-base">
                  {(ranking.priceScore * 0.65).toFixed(4)}
                </span>
                <span className="text-[11px] text-ink-600 block mt-0.5">
                  (নর্মালাইজড: {ranking.priceScore.toFixed(2)})
                </span>
              </div>
              <div className="p-2.5 rounded bg-paddy-400/10 border border-paddy-400/20">
                <span className="text-ink-600 block">দূরত্বের ওজন (৩৫%)</span>
                <span className="font-bold text-forest-900 text-base">
                  {(ranking.distanceScore * 0.35).toFixed(4)}
                </span>
                <span className="text-[11px] text-ink-600 block mt-0.5">
                  (আনুমানিক দূরত্ব: {ranking.distanceKm} কিমি)
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-start gap-2.5 text-xs text-ink-600 bg-field-wash p-3 rounded border border-line-200">
            <CheckCircle2 className="w-4 h-4 text-forest-700 shrink-0 mt-0.5" />
            <p>
              শিখড় এআই কোনো স্পন্সরড বা পেইড র‍্যাঙ্কিং প্রচার করে না। শুধুমাত্র একই ক্যাটাগরি ও একই মূল্যের এককের (ঘণ্টা/দিন/একর) মধ্যে শতভাগ নিরপেক্ষভাবে এই তালিকা সাজানো হয়।
            </p>
          </div>
        </div>

        <div className="pt-2 text-right">
          <button
            onClick={onClose}
            className="px-5 py-2.5 bg-forest-700 text-canvas font-medium rounded-btn hover:bg-forest-900 transition-colors min-h-[44px]"
          >
            বুঝেছি
          </button>
        </div>
      </div>
    </div>
  );
};
