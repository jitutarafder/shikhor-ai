import React, { useState, useEffect } from 'react';
import { Camera, ZoomIn, X, AlertCircle } from 'lucide-react';

interface CropLeafImageProps {
  caseId: string;
  imageFilename: string;
  cropType: string;
  token?: string | null;
  className?: string;
  allowZoom?: boolean;
}

const getFastCloudinaryUrl = (url: string, width = 600): string => {
  if (url.includes('res.cloudinary.com') && url.includes('/image/upload/')) {
    const transform = `f_auto,q_auto,w_${width},c_limit`;
    if (!url.includes(transform)) {
      return url.replace('/image/upload/', `/image/upload/${transform}/`);
    }
  }
  return url;
};

export const CropLeafImage: React.FC<CropLeafImageProps> = ({
  caseId,
  imageFilename,
  cropType,
  token,
  className = 'w-full h-48 object-cover rounded-btn',
  allowZoom = true,
}) => {
  const [imgSrc, setImgSrc] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isZoomed, setIsZoomed] = useState(false);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    let active = true;
    setIsLoading(true);
    setHasError(false);

    // 1. Direct Cloudinary URL: instant optimized fast load
    if (imageFilename && (imageFilename.startsWith('http://') || imageFilename.startsWith('https://'))) {
      setImgSrc(getFastCloudinaryUrl(imageFilename, 600));
      setIsLoading(false);
      return;
    }

    // 2. If filename matches demo crops, use local static asset directly
    if (imageFilename.includes('rice') || imageFilename === 'demo_rice_leaf.jpg') {
      setImgSrc('/demo-crops/demo_rice_leaf.jpg');
      setIsLoading(false);
      return;
    }
    if (imageFilename.includes('potato') || imageFilename === 'demo_potato_leaf.jpg') {
      setImgSrc('/demo-crops/demo_potato_leaf.jpg');
      setIsLoading(false);
      return;
    }
    if (imageFilename.includes('tomato') || imageFilename === 'demo_tomato_leaf.jpg') {
      setImgSrc('/demo-crops/demo_tomato_leaf.jpg');
      setIsLoading(false);
      return;
    }

    // 3. Fetch authenticated derivative from API
    if (token) {
      fetch(`/api/v1/crop-cases/${caseId}/image`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
        .then((res) => {
          if (!res.ok) throw new Error('Image fetch failed');
          return res.blob();
        })
        .then((blob) => {
          if (active) {
            const url = URL.createObjectURL(blob);
            setImgSrc(url);
            setIsLoading(false);
          }
        })
        .catch(() => {
          if (active) {
            // Fallback based on crop type
            if (cropType === 'আলু') {
              setImgSrc('/demo-crops/demo_potato_leaf.jpg');
            } else if (cropType === 'টমেটো') {
              setImgSrc('/demo-crops/demo_tomato_leaf.jpg');
            } else {
              setImgSrc('/demo-crops/demo_rice_leaf.jpg');
            }
            setIsLoading(false);
          }
        });
    } else {
      // Fallback based on crop type
      if (cropType === 'আলু') {
        setImgSrc('/demo-crops/demo_potato_leaf.jpg');
      } else if (cropType === 'টমেটো') {
        setImgSrc('/demo-crops/demo_tomato_leaf.jpg');
      } else {
        setImgSrc('/demo-crops/demo_rice_leaf.jpg');
      }
      setIsLoading(false);
    }

    return () => {
      active = false;
    };
  }, [caseId, imageFilename, cropType, token]);

  return (
    <div className="relative group overflow-hidden rounded-btn bg-surface border border-line-200">
      {isLoading ? (
        <div className="w-full h-48 flex flex-col items-center justify-center bg-leaf-100/30 text-ink-600 animate-pulse text-xs">
          <Camera className="w-6 h-6 mb-1 text-forest-700/60" />
          <span>আক্রান্ত পাতার ছবি লোড হচ্ছে…</span>
        </div>
      ) : hasError || !imgSrc ? (
        <div className="w-full h-48 flex flex-col items-center justify-center bg-surface text-ink-600 text-xs p-4 text-center">
          <AlertCircle className="w-6 h-6 mb-1 text-paddy-400" />
          <span>ছবি প্রদর্শন সম্ভব হয়নি</span>
        </div>
      ) : (
        <div className="relative">
          <img
            src={imgSrc}
            alt={`${cropType} আক্রান্ত পাতা`}
            className={`${className} transition-transform duration-300 group-hover:scale-102 cursor-pointer`}
            onClick={() => allowZoom && setIsZoomed(true)}
            onError={() => {
              // On error, fallback to demo rice leaf
              if (imgSrc !== '/demo-crops/demo_rice_leaf.jpg') {
                setImgSrc('/demo-crops/demo_rice_leaf.jpg');
              } else {
                setHasError(true);
              }
            }}
          />

          {allowZoom && (
            <button
              type="button"
              onClick={() => setIsZoomed(true)}
              className="absolute bottom-2 right-2 p-1.5 bg-forest-900/80 hover:bg-forest-900 text-white rounded-full opacity-80 group-hover:opacity-100 transition-opacity shadow-xs"
              title="বড় করে দেখুন (Zoom)"
              aria-label="ছবি বড় করে দেখুন"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
          )}

          <div className="absolute top-2 left-2 px-2 py-0.5 rounded-full bg-ink-900/70 text-canvas text-[10px] font-semibold backdrop-blur-xs">
            {cropType} নমুনা ছবি
          </div>
        </div>
      )}

      {/* Lightbox Modal for High-Resolution Inspection */}
      {isZoomed && imgSrc && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-900/80 backdrop-blur-sm animate-in fade-in"
          onClick={() => setIsZoomed(false)}
        >
          <div
            className="relative max-w-4xl max-h-[90vh] bg-surface rounded-card p-3 shadow-2xl border border-line-200"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              onClick={() => setIsZoomed(false)}
              className="absolute top-4 right-4 p-2 bg-ink-900/80 hover:bg-ink-900 text-white rounded-full z-10 transition-colors"
              aria-label="বন্ধ করুন"
            >
              <X className="w-5 h-5" />
            </button>
            <div className="space-y-2">
              <div className="text-xs font-semibold text-forest-900 px-1">
                {cropType} আক্রান্ত পাতার উচ্চ রেজোলিউশন মাইক্রোস্কোপিক/ম্যাক্রো ভিউ
              </div>
              <img
                src={imgSrc}
                alt={`${cropType} বিশদ ছবি`}
                className="max-h-[75vh] w-auto max-w-full object-contain rounded-btn mx-auto"
              />
              <div className="text-[11px] text-ink-600 text-center italic">
                ছবির দাগ, মার্জিন ও ক্ষত দেখে সঠিক রোগ নিশ্চিত করুন
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
