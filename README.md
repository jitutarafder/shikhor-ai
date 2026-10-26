# Shikhor AI (শিখড় এআই) 🌾

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5+-3178C6.svg?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248.svg?style=flat&logo=mongodb&logoColor=white)](https://www.mongodb.com/atlas)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4+-38B2AC.svg?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Shikhor AI** হলো বাংলাদেশের কৃষকদের জন্য তৈরি একটি এআই-চালিত, বাংলা-প্রথম সমন্বিত কৃষি সহায়তা ও মার্কেটপ্লেস প্ল্যাটফর্ম (AI-Powered, Bangla-First Agricultural Decision Support & Marketplace Platform)।

এটি কৃষকদের আধুনিক কৃষি প্রযুক্তি, ফসলের রোগ নির্ণয়, বিশ্বস্ত কৃষি সরঞ্জাম ভাড়া, আবহাওয়া ভিত্তিক চাষাবাদ পরিকল্পনা এবং মধ্যস্বত্বভোগী ছাড়া সরাসরি ফসল বিক্রয়ের সুবিধা প্রদান করে।

---

## 🌟 প্রধান বৈশিষ্ঠ্যসমূহ (Key Features)

### ১. 🌿 ফসলের রোগ নির্ণয় ও পরামর্শ (AI Crop Health Assistant)
- মোবাইল বা ক্যামেরা দিয়ে ফসলের পাতার ছবি আপলোড করে সম্ভাব্য রোগ ও সমস্যা শনাক্তকরণ।
- অনুমোদিত কৃষি নির্দেশিকা (Reviewed Advisory) অনুযায়ী নিরাপদ প্রতিকার ও ব্যবস্থাপনা পরামর্শ।
- কম রেজোলিউশন বা অস্পষ্ট ছবির ক্ষেত্রে বিশেষজ্ঞদের পরামর্শ গ্রহণের স্বচ্ছ নির্দেশনা।

### ২. 🚜 কৃষি সরঞ্জাম ভাড়া মার্কেটপ্লেস (Equipment Rental Marketplace)
- পাওয়ার টিলার, হারভেস্টার, ট্রাক্টর এবং সেচ পাম্পের মতো প্রয়োজনীয় কৃষি সরঞ্জাম এলাকাভিত্তিক অনুসন্ধান।
- **স্বচ্ছ র‍্যাংকিং অ্যালগরিদম**: `৬৫% সাশ্রয়ী মূল্য + ৩৫% নিকটবর্তী দূরত্ব` সূত্রের ভিত্তিতে সম্পূর্ণ নিরপেক্ষ সার্চ ফলাফল।
- সরঞ্জাম মালিকদের সাথে সরাসরি বুকিং ও শিডিউলিং।

### ৩. 🌦️ কৃষি-আবহাওয়া ভিত্তিক পরিকল্পনা (Agro-Weather Decision Support)
- আগামী ৫ দিনের রিয়েল-টাইম আবহাওয়া পূর্বাভাস এবং সতর্কবার্তা।
- কীটনাশক স্প্রে, ফসল কাটা বা সেচ দেওয়ার জন্য স্বয়ংক্রিয় "উপযুক্ত কাজের সময়" (Activity Windows) বিশ্লেষণ।

### ৪. 🤝 ফসল ক্রয়-বিক্রয় ও চ্যাট (Crop Marketplace & Direct Messaging)
- কৃষকদের উৎপাদিত ধান, আলু, গম, পাট ইত্যাদি ফসলের সরাসরি তালিকাভুক্তি (Listings)।
- ক্রেতা ও কৃষকের মধ্যে ইন-প্ল্যাটফর্ম সুরক্ষিত মেসেজিং ও ফসলের নমুনা ছবি পাঠানো।
- অপব্যবহার রোধে ব্লক ও রিপোর্ট সুবিধা (Abuse Prevention & Moderation)।

### ৫. 📶 অফলাইন ফার্স্ট ও সিঙ্ক ইঞ্জিন (Offline Knowledge & Sync)
- দুর্বল বা ইন্টারনেটহীন নেটওয়ার্কে প্রয়োজনীয় কৃষি পরামর্শ ও ডাটা ব্রাউজ করার জন্য IndexedDB (Dexie.js) ক্যাশ।
- ইন্টারনেট সংযোগ ফিরে আসার পর স্বয়ংক্রিয় আইডেমপোটেন্ট মিউটেশন সিঙ্ক্রোনাইজেশন।

---

## 🛠️ প্রযুক্তি কাঠামো (Technology Stack)

| স্তর (Layer) | প্রযুক্তি (Technology) | বিবরণ (Details) |
| :--- | :--- | :--- |
| **Frontend** | React 18, TypeScript, Vite | আধুনিক SPA আর্কিটেকচার |
| **Styling** | Tailwind CSS, Framer Motion | বাংলা ফন্ট সাপোর্ট ও রেসপনসিভ ডিজাইন |
| **Client Storage** | Dexie.js (IndexedDB) | অফলাইন ডাটা ক্যাশিং ও মিউটেশন কিউ |
| **Backend** | Python 3.12+, FastAPI | উচ্চ পারফরম্যান্সের RESTful API ও মডুলার মনোলিথ |
| **Database** | MongoDB Atlas / SQLite | নমনীয় ডেটা লেয়ার ও পোস্টজিআইএস জিও-কোয়েরি সাপোর্ট |
| **Authentication** | JWT, Argon2id, Firebase Phone OTP | নিরাপদ সেশন ও মাল্টি-রোল অথোরাইজেশন |
| **Storage & Image Safety** | Cloudinary & Pillow | EXIF স্ট্রিপিং ও স্যানিটাইজড WebP ডেরিভেটিভ |
| **Testing** | Pytest, Vitest | ইউনিট ও এন্ড-টু-এন্ড সিকিউরিটি টেস্ট |

---

## 🚀 লোকাল সেটআপ ও রান নির্দেশিকা (Getting Started)

### ১. রিপোজিটরি ক্লোন করুন
```bash
git clone https://github.com/jitutarafder/shikhor-ai.git
cd shikhor-ai
```

---

### ২. ব্যাকএন্ড সেটআপ (Backend Setup)

```bash
cd backend

# পাইথন ভার্চুয়াল এনভায়রনমেন্ট তৈরি করুন
python -m venv .venv

# এনভায়রনমেন্ট সক্রিয় করুন (Windows)
.venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

# ডিপেনডেন্সি ইনস্টল করুন
pip install -r requirements.txt

# এনভায়রনমেন্ট ভ্যারিয়েবল কনফিগার করুন
copy .env.example .env
# .env ফাইলে আপনার MongoDB Atlas URI বা ডাটাবেজ তথ্য কনফিগার করুন

# ব্যাকএন্ড সার্ভার চালু করুন
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
> ব্যাকএন্ড এপিআই ডক্স দেখুন: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### ৩. ফ্রন্টএন্ড সেটআপ (Frontend Setup)

```bash
cd ../frontend

# নোড প্যাকেজ ইনস্টল করুন
npm install

# এনভায়রনমেন্ট ফাইল তৈরি করুন
copy .env.example .env

# ফ্রন্টএন্ড ডেভ সার্ভার চালু করুন
npm run dev
```
> ব্রাউজারে অ্যাপ্লিকেশন ওপেন করুন: [http://localhost:5173](http://localhost:5173)

---

### ৪. টেস্ট রান করা (Running Tests)

**ব্যাকএন্ড টেস্ট:**
```bash
cd backend
pytest
```

**ফ্রন্টএন্ড বিল্ড টেস্ট:**
```bash
cd frontend
npm run build
```

---

## 🔒 নিরাপত্তা ও নীতিগত মানদণ্ড (Security & Ethics)

- **অবজেক্ট-লেভেল অনুমোদন (Role + Object Authorization)**: ব্যবহারকারী কেবল নিজের রিসোর্স বা অ্যাক্টিভ কথোপকথন অ্যাক্সেস করতে পারেন।
- **ছবি স্যানিটাইজেশন**: আপলোডকৃত যেকোনো ছবি সার্ভার-সাইডে ডিকোড করে EXIF মেটাডাটা ও জিও-ট্যাগ মুছে ফেলে নিরাপদ ফর্মে সংরক্ষণ করা হয়।
- **স্বচ্ছ এআই গাইডেন্স**: কৃত্রিম বুদ্ধিমত্তার ফলাফলকে সম্ভাব্য পরামর্শ হিসেবে উপস্থাপন করা হয় এবং কখনোই রাসায়নিক কীটনাশকের ঝুঁকিপূর্ণ ডোজ নিজে থেকে তৈরি করে না।

---

## 📄 লাইসেন্স (License)

এই প্রজেক্টটি [MIT License](LICENSE)-এর অধীনে উন্মুক্ত ও লাইসেন্সপ্রাপ্ত।

---

## 👨‍💻 অবদানকারী (Contributor)

- **Jitu Tarafder** — [GitHub Profile](https://github.com/jitutarafder)
- **Shikhor AI Team**

*🌾 কৃষকের সমৃদ্ধি, প্রযুক্তির শিখরে — শিখড় এআই (Shikhor AI)*
