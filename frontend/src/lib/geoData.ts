export interface DistrictData {
  nameBn: string;
  nameEn: string;
  upazilasBn: string[];
}

export const BD_DISTRICTS: Record<string, DistrictData> = {
  dhaka: {
    nameBn: 'ঢাকা',
    nameEn: 'Dhaka',
    upazilasBn: ['ধামরাই', 'দোহার', 'কেরানীগঞ্জ', 'নবাবগঞ্জ', 'সাভার'],
  },
  bogura: {
    nameBn: 'বগুড়া',
    nameEn: 'Bogura',
    upazilasBn: ['শেরপুর', 'শিবগঞ্জ', 'সারিয়াকান্দি', 'কাহালু', 'দুপচাঁচিয়া', 'গাবতলী'],
  },
  rangpur: {
    nameBn: 'রংপুর',
    nameEn: 'Rangpur',
    upazilasBn: ['বদরগঞ্জ', 'গঙ্গাচড়া', 'কাউনিয়া', 'মিঠাপুকুর', 'পীরগাছা', 'পীরগঞ্জ'],
  },
  dinajpur: {
    nameBn: 'দিনাজপুর',
    nameEn: 'Dinajpur',
    upazilasBn: ['বীরগঞ্জ', 'বোচাগঞ্জ', 'চিরিরবন্দর', 'ফুলবাড়ী', 'ঘোড়াঘাট', 'কাহারোল'],
  },
  rajshahi: {
    nameBn: 'রাজশাহী',
    nameEn: 'Rajshahi',
    upazilasBn: ['বাঘা', 'চারঘাট', 'দুর্গাপুর', 'গোদাগাড়ী', 'মোহনপুর', 'পবা', 'পুঠিয়া'],
  },
  cumilla: {
    nameBn: 'কুমিল্লা',
    nameEn: 'Cumilla',
    upazilasBn: ['বরুড়া', 'চান্দিনা', 'দাউদকান্দি', 'হোমনা', 'লাকসাম', 'মুরাদনগর'],
  },
  jashore: {
    nameBn: 'যশোর',
    nameEn: 'Jashore',
    upazilasBn: ['অভয়নগর', 'বাঘারপাড়া', 'চৌগাছা', 'ঝিকরগাছা', 'কেশবপুর', 'মণিরামপুর'],
  },
  mymensingh: {
    nameBn: 'ময়মনসিংহ',
    nameEn: 'Mymensingh',
    upazilasBn: ['ত্রিশাল', 'মুক্তাগাছা', 'ভালুকা', 'গফরগাঁও', 'ফুলবাড়িয়া', 'ঈশ্বরগঞ্জ'],
  },
};
