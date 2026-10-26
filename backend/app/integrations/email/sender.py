"""SMTP Email adapter for Shikhor AI.

Dispatches transactional emails (e.g. OTP verification, password reset) via SMTP.
Uses Python standard library smtplib asynchronously without blocking the event loop.
"""

import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import smtplib
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("shikhor.integrations.email")


def _send_smtp_sync(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> bool:
    """Synchronous SMTP delivery helper executed in worker thread."""
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.info(
            "SMTP is not configured in settings. Skipping outbound email dispatch to %s.",
            to_email,
        )
        return False

    smtp_user = settings.SMTP_USER.strip()
    smtp_pass = settings.SMTP_PASSWORD.strip().replace(" ", "") if "gmail" in settings.SMTP_HOST.lower() else settings.SMTP_PASSWORD.strip()
    sender_email = (settings.SMTP_FROM_EMAIL or settings.SMTP_USER).strip()
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{sender_email}>"
    msg["To"] = to_email.strip()
    msg["Subject"] = subject

    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=12)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=12)
            if settings.SMTP_TLS:
                server.starttls()

        server.login(smtp_user, smtp_pass)
        server.sendmail(sender_email, [to_email.strip()], msg.as_string())
        server.quit()
        logger.info("Successfully dispatched email to %s (Subject: %s)", to_email, subject)
        return True
    except Exception as exc:
        logger.error(
            "Failed to send email to %s via SMTP (%s:%s): %s",
            to_email,
            settings.SMTP_HOST,
            settings.SMTP_PORT,
            str(exc),
        )
        return False


async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> bool:
    """Asynchronously sends an email via SMTP off the main event loop."""
    return await asyncio.to_thread(_send_smtp_sync, to_email, subject, html_body, text_body)


def get_signup_otp_html(otp_code: str) -> str:
    """Returns a styled HTML template for signup email verification."""
    return f"""<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>শিখড় এআই - ইমেইল ওটিপি যাচাই</title>
</head>
<body style="margin: 0; padding: 24px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f1f5f9; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
    <tr>
      <td style="background: linear-gradient(135deg, #1b5e20, #2e7d32); padding: 32px 24px; text-align: center; color: #ffffff;">
        <h1 style="margin: 0; font-size: 26px; font-weight: bold; letter-spacing: 0.5px;">শিখড় এআই (Shikhor AI)</h1>
        <p style="margin: 8px 0 0; font-size: 14px; opacity: 0.92;">বাংলাদেশের কৃষকদের নির্ভরযোগ্য ডিজিটাল প্ল্যাটফর্ম</p>
      </td>
    </tr>
    <tr>
      <td style="padding: 32px 28px;">
        <h2 style="margin: 0 0 16px; font-size: 18px; color: #0f172a;">ইমেইল ঠিকানা যাচাইকরণ কোড</h2>
        <p style="margin: 0 0 20px; font-size: 15px; line-height: 1.6; color: #334155;">
          শিখড় এআই প্ল্যাটফর্মে একাউন্ট নিবন্ধন সম্পন্ন করতে নিচের ৬-সংখ্যার ওটিপি (OTP) কোডটি ব্যবহার করুন:
        </p>
        
        <div style="background-color: #f0fdf4; border: 2px dashed #86efac; border-radius: 10px; padding: 22px; text-align: center; margin: 24px 0;">
          <div style="font-size: 38px; font-weight: 800; letter-spacing: 8px; color: #15803d; font-family: monospace;">
            {otp_code}
          </div>
          <div style="font-size: 13px; color: #166534; font-weight: 500; margin-top: 8px;">
            ⏱️ কোডটির মেয়াদ ১০ মিনিট
          </div>
        </div>

        <p style="margin: 0 0 16px; font-size: 14px; line-height: 1.6; color: #475569;">
          রেজিস্ট্রেশন ফর্মে এই কোডটি দিয়ে "ওটিপি যাচাই সম্পন্ন করুন" বাটনে ক্লিক করুন।
        </p>
        <div style="border-top: 1px solid #f1f5f9; padding-top: 16px; font-size: 13px; color: #64748b; line-height: 1.5;">
          <strong>নিরাপত্তা সতর্কতা:</strong> এই ওটিপি কোডটি কারো সাথে শেয়ার করবেন না। আপনি যদি শিখড় এআই-তে সাইন-আপ করার অনুরোধ না করে থাকেন, তবে এই ইমেইলটি এড়িয়ে চলুন।
        </div>
      </td>
    </tr>
    <tr>
      <td style="background-color: #f8fafc; padding: 20px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9;">
        © {settings.APP_NAME} — স্মার্ট প্রযুক্তিতে সমৃদ্ধ কৃষি
      </td>
    </tr>
  </table>
</body>
</html>
"""


def get_password_reset_otp_html(otp_code: str) -> str:
    """Returns a styled HTML template for password reset OTP."""
    return f"""<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>শিখড় এআই - পাসওয়ার্ড রিসেট কোড</title>
</head>
<body style="margin: 0; padding: 24px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f1f5f9; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 540px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
    <tr>
      <td style="background: linear-gradient(135deg, #1e3a8a, #2563eb); padding: 32px 24px; text-align: center; color: #ffffff;">
        <h1 style="margin: 0; font-size: 26px; font-weight: bold; letter-spacing: 0.5px;">শিখড় এআই (Shikhor AI)</h1>
        <p style="margin: 8px 0 0; font-size: 14px; opacity: 0.92;">পাসওয়ার্ড রিসেট অনুরোধ</p>
      </td>
    </tr>
    <tr>
      <td style="padding: 32px 28px;">
        <h2 style="margin: 0 0 16px; font-size: 18px; color: #0f172a;">আপনার পাসওয়ার্ড রিসেট ওটিপি</h2>
        <p style="margin: 0 0 20px; font-size: 15px; line-height: 1.6; color: #334155;">
          আপনার শিখড় এআই অ্যাকাউন্টের পাসওয়ার্ড পরিবর্তন করার জন্য নিচের ওটিপি কোডটি ব্যবহার করুন:
        </p>
        
        <div style="background-color: #eff6ff; border: 2px dashed #93c5fd; border-radius: 10px; padding: 22px; text-align: center; margin: 24px 0;">
          <div style="font-size: 38px; font-weight: 800; letter-spacing: 8px; color: #1d4ed8; font-family: monospace;">
            {otp_code}
          </div>
          <div style="font-size: 13px; color: #1e40af; font-weight: 500; margin-top: 8px;">
            ⏱️ কোডটির মেয়াদ ১০ মিনিট
          </div>
        </div>

        <div style="border-top: 1px solid #f1f5f9; padding-top: 16px; font-size: 13px; color: #64748b; line-height: 1.5;">
          নিরাপত্তা সতর্কতা: আপনি যদি এই অনুরোধটি না করে থাকেন, তবে অবিলম্বে আপনার পাসওয়ার্ড পরিবর্তন করুন এবং কারো সাথে এই ওটিপি কোড শেয়ার করবেন না।
        </div>
      </td>
    </tr>
    <tr>
      <td style="background-color: #f8fafc; padding: 20px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9;">
        © {settings.APP_NAME} — স্মার্ট প্রযুক্তিতে সমৃদ্ধ কৃষি
      </td>
    </tr>
  </table>
</body>
</html>
"""


def get_nid_approval_email_html(user_name: str) -> str:
    """Returns a styled HTML template notifying the user of account approval."""
    return f"""<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>শিখড় এআই - অ্যাকাউন্ট অনুমোদিত হয়েছে</title>
</head>
<body style="margin: 0; padding: 24px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f1f5f9; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 16px rgba(0,0,0,0.06);">
    <tr>
      <td style="background: linear-gradient(135deg, #15803d, #166534); padding: 36px 28px; text-align: center; color: #ffffff;">
        <h1 style="margin: 0; font-size: 26px; font-weight: 800; letter-spacing: 0.5px;">শিখড় এআই (Shikhor AI)</h1>
        <p style="margin: 8px 0 0; font-size: 14px; opacity: 0.95;">অ্যাকাউন্ট ভেরিফিকেশন ও অনুমোদন বিজ্ঞপ্তি</p>
      </td>
    </tr>
    <tr>
      <td style="padding: 32px 28px;">
        <div style="background-color: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 12px; padding: 18px; margin-bottom: 24px; text-align: center;">
          <span style="font-size: 28px; display: block; margin-bottom: 6px;">🎉</span>
          <h2 style="margin: 0; font-size: 18px; color: #065f46; font-weight: bold;">অভিনন্দন! আপনার অ্যাকাউন্ট অনুমোদিত হয়েছে</h2>
        </div>

        <p style="margin: 0 0 16px; font-size: 15px; line-height: 1.6; color: #334155;">
          প্রিয় <strong>{user_name}</strong>,
        </p>
        <p style="margin: 0 0 20px; font-size: 14px; line-height: 1.7; color: #475569;">
          আনন্দের সাথে জানাচ্ছি যে আপনার প্রদত্ত জাতীয় পরিচয়পত্র (NID) ও তথ্যাবলি শিখড় এআই অ্যাডমিন প্যানেল কর্তৃক সফলভাবে যাচাই ও <strong>অনুমোদিত (Approved)</strong> হয়েছে।
        </p>

        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 24px;">
          <h3 style="margin: 0 0 12px; font-size: 14px; font-weight: bold; color: #0f172a;">আপনার জন্য উন্মুক্ত সেবাসমূহ:</h3>
          <ul style="margin: 0; padding-left: 20px; font-size: 13px; line-height: 1.8; color: #334155;">
            <li>🌿 <strong>এআই ফসল ডাক্তার:</strong> ফসলের পাতার ছবি তুলে রোগ সনাক্তকরণ ও চিকিৎসা</li>
            <li>🚜 <strong>যন্ত্রপাতি ভাড়া:</strong> ট্রাক্টর, হারভেস্টার ইত্যাদি সহজে ভাড়া নেওয়া বা দেওয়া</li>
            <li>🌾 <strong>ফসল মার্কেটপ্লেস:</strong> মধ্যস্বত্বভোগী ছাড়া সরাসরি পাইকারদের কাছে বিক্রয়</li>
            <li>⛅ <strong>আবহাওয়া সতর্কতা:</strong> লাইভ পূর্বাভাস ও স্প্রে করার নিরাপদ সময়সূচি</li>
            <li>💬 <strong>যোগাযোগ:</strong> কৃষি বিশেষজ্ঞ ও ক্রেতাদের সাথে মেসেজিং সুবিধা</li>
          </ul>
        </div>

        <p style="margin: 0 0 24px; font-size: 14px; line-height: 1.6; color: #475569;">
          আপনার অ্যাকাউন্টে <strong>ভেরিফাইড ব্যাজ (✓ Verified Badge)</strong> সক্রিয় করা হয়েছে। এখনই লগইন করে সকল সেবা গ্রহণ করুন।
        </p>

        <div style="text-align: center; margin: 28px 0 10px;">
          <a href="http://localhost:5174/app" style="background: #15803d; color: #ffffff; text-decoration: none; padding: 14px 28px; border-radius: 10px; font-weight: bold; font-size: 15px; display: inline-block; box-shadow: 0 2px 8px rgba(21,128,61,0.3);">
            ড্যাশবোর্ডে প্রবেশ করুন →
          </a>
        </div>
      </td>
    </tr>
    <tr>
      <td style="background-color: #f8fafc; padding: 20px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9;">
        © {settings.APP_NAME} — স্মার্ট প্রযুক্তিতে সমৃদ্ধ কৃষি
      </td>
    </tr>
  </table>
</body>
</html>
"""


def get_nid_rejection_email_html(user_name: str, reason: str) -> str:
    """Returns a styled HTML template notifying the user of account rejection."""
    return f"""<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>শিখড় এআই - অ্যাকাউন্ট ভেরিফিকেশন সংক্রান্ত বিজ্ঞপ্তি</title>
</head>
<body style="margin: 0; padding: 24px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f1f5f9; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 16px rgba(0,0,0,0.06);">
    <tr>
      <td style="background: linear-gradient(135deg, #be123c, #9f1239); padding: 36px 28px; text-align: center; color: #ffffff;">
        <h1 style="margin: 0; font-size: 26px; font-weight: 800; letter-spacing: 0.5px;">শিখড় এআই (Shikhor AI)</h1>
        <p style="margin: 8px 0 0; font-size: 14px; opacity: 0.95;">অ্যাকাউন্ট ভেরিফিকেশন সংক্রান্ত জরুরি নোটিশ</p>
      </td>
    </tr>
    <tr>
      <td style="padding: 32px 28px;">
        <p style="margin: 0 0 16px; font-size: 15px; line-height: 1.6; color: #334155;">
          প্রিয় <strong>{user_name}</strong>,
        </p>
        <p style="margin: 0 0 20px; font-size: 14px; line-height: 1.7; color: #475569;">
          শিখড় এআই প্ল্যাটফর্মে আপনার দেওয়া জাতীয় পরিচয়পত্র (NID) ও তথ্য অ্যাডমিন কর্তৃক পর্যালোচনা করা হয়েছে। কৃষকদের তথ্য সুরক্ষা ও প্ল্যাটফর্মের নিরাপত্তা নীতি অনুযায়ী আপনার বর্তমান আবেদনটি অনুমোদন করা সম্ভব হয়নি।
        </p>

        <div style="background-color: #fff1f2; border: 1px solid #fecdd3; border-radius: 12px; padding: 18px; margin-bottom: 24px;">
          <h3 style="margin: 0 0 6px; font-size: 13px; font-weight: bold; color: #9f1239; text-transform: uppercase;">পর্যালোচনা মতামত / বাতিলের কারণ:</h3>
          <p style="margin: 0; font-size: 14px; font-weight: 600; color: #881337; line-height: 1.5;">
            {reason}
          </p>
        </div>

        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px 20px; margin-bottom: 24px;">
          <h4 style="margin: 0 0 8px; font-size: 13px; font-weight: bold; color: #0f172a;">পরবর্তী করণীয়:</h4>
          <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #64748b;">
            আপনার অ্যাকাউন্টে লগইন করে সঠিক ও সুস্পষ্ট NID কার্ডের ছবি আপলোড করুন অথবা জরুরি সহায়তার জন্য আমাদের সাপোর্ট হেল্পলাইনে যোগাযোগ করুন।
          </p>
        </div>

        <div style="text-align: center; margin: 24px 0 10px;">
          <a href="http://localhost:5174/contact" style="background: #be123c; color: #ffffff; text-decoration: none; padding: 13px 26px; border-radius: 10px; font-weight: bold; font-size: 14px; display: inline-block;">
            সাপোর্ট সেন্টারে যোগাযোগ করুন →
          </a>
        </div>
      </td>
    </tr>
    <tr>
      <td style="background-color: #f8fafc; padding: 20px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9;">
        © {settings.APP_NAME} — স্মার্ট প্রযুক্তিতে সমৃদ্ধ কৃষি
      </td>
    </tr>
  </table>
</body>
</html>
"""


def get_rental_request_email_html(
    owner_name: str,
    renter_name: str,
    renter_phone: str,
    equipment_name: str,
    dates_str: str,
    duration_units: int,
    price_unit: str,
    total_price: float,
) -> str:
    """Returns a styled HTML email notifying the machinery owner of a new booking request."""
    unit_bn = "দিন" if price_unit == "per_day" else ("ঘণ্টা" if price_unit == "per_hour" else "একর")
    return f"""<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>নতুন যন্ত্রপাতি ভাড়ার অনুরোধ</title>
</head>
<body style="margin: 0; padding: 24px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f1f5f9; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 16px rgba(0,0,0,0.06);">
    <tr>
      <td style="background: linear-gradient(135deg, #0284c7, #0369a1); padding: 32px 28px; text-align: center; color: #ffffff;">
        <h1 style="margin: 0; font-size: 24px; font-weight: 800;">শিখড় এআই (Shikhor AI)</h1>
        <p style="margin: 6px 0 0; font-size: 14px; opacity: 0.95;">নতুন যন্ত্রপাতি ভাড়ার অনুরোধ বিজ্ঞপ্তি</p>
      </td>
    </tr>
    <tr>
      <td style="padding: 32px 28px;">
        <p style="margin: 0 0 16px; font-size: 15px; line-height: 1.6; color: #334155;">
          প্রিয় <strong>{owner_name}</strong>,
        </p>
        <p style="margin: 0 0 20px; font-size: 14px; line-height: 1.7; color: #475569;">
          আপনার তালিকাভুক্ত কৃষি যন্ত্রপাতি <strong>"{equipment_name}"</strong> ভাড়ার জন্য একজন কৃষক নতুন অনুরোধ পাঠিয়েছেন।
        </p>

        <div style="background-color: #f0f9ff; border: 1px solid #bae6fd; border-radius: 12px; padding: 18px 20px; margin-bottom: 24px;">
          <h3 style="margin: 0 0 12px; font-size: 14px; font-weight: bold; color: #0369a1;">অনুরোধের বিবরণ:</h3>
          <table style="width: 100%; font-size: 13px; line-height: 1.8; color: #334155;">
            <tr>
              <td style="color: #64748b; width: 40%;">আবেদনকারী কৃষক:</td>
              <td style="font-weight: bold;">{renter_name}</td>
            </tr>
            <tr>
              <td style="color: #64748b;">যোগাযোগের নম্বর:</td>
              <td style="font-weight: bold;">{renter_phone}</td>
            </tr>
            <tr>
              <td style="color: #64748b;">অনুরোধকৃত তারিখ:</td>
              <td style="font-weight: bold; color: #0284c7;">{dates_str}</td>
            </tr>
            <tr>
              <td style="color: #64748b;">ভাড়ার পরিমাণ/সময়:</td>
              <td style="font-weight: bold;">{duration_units} {unit_bn}</td>
            </tr>
            <tr>
              <td style="color: #64748b;">সম্ভাব্য মোট ভাড়া:</td>
              <td style="font-weight: bold; color: #15803d; font-size: 15px;">৳ {total_price:,.0f} BDT</td>
            </tr>
          </table>
        </div>

        <p style="margin: 0 0 24px; font-size: 13px; line-height: 1.6; color: #64748b;">
          অনুগ্রহ করে আপনার ড্যাশবোর্ডে প্রবেশ করে কৃষকের আবেদনটি পর্যালোচনাপূর্বক গ্রহণ (Accept) অথবা বাতিল (Reject) করুন।
        </p>

        <div style="text-align: center; margin: 24px 0 10px;">
          <a href="http://localhost:5174/equipment" style="background: #0284c7; color: #ffffff; text-decoration: none; padding: 13px 26px; border-radius: 10px; font-weight: bold; font-size: 14px; display: inline-block; box-shadow: 0 2px 8px rgba(2,132,199,0.3);">
            আবেদন পর্যালোচনা করুন →
          </a>
        </div>
      </td>
    </tr>
    <tr>
      <td style="background-color: #f8fafc; padding: 20px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9;">
        © {settings.APP_NAME} — স্মার্ট প্রযুক্তিতে সমৃদ্ধ কৃষি
      </td>
    </tr>
  </table>
</body>
</html>
"""


def get_rental_accepted_email_html(
    renter_name: str,
    owner_name: str,
    owner_phone: str,
    equipment_name: str,
    dates_str: str,
    total_price: float,
) -> str:
    """Returns a styled HTML email notifying the farmer that their booking request was accepted."""
    return f"""<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ভাড়ার অনুরোধ অনুমোদিত হয়েছে</title>
</head>
<body style="margin: 0; padding: 24px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f1f5f9; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 16px rgba(0,0,0,0.06);">
    <tr>
      <td style="background: linear-gradient(135deg, #15803d, #166534); padding: 32px 28px; text-align: center; color: #ffffff;">
        <h1 style="margin: 0; font-size: 24px; font-weight: 800;">শিখড় এআই (Shikhor AI)</h1>
        <p style="margin: 6px 0 0; font-size: 14px; opacity: 0.95;">যন্ত্রপাতি বুকিং নিশ্চিতকরণ বিজ্ঞপ্তি</p>
      </td>
    </tr>
    <tr>
      <td style="padding: 32px 28px;">
        <div style="background-color: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 12px; padding: 16px; margin-bottom: 24px; text-align: center;">
          <span style="font-size: 26px; display: block; margin-bottom: 4px;">✅</span>
          <h2 style="margin: 0; font-size: 17px; color: #065f46; font-weight: bold;">অভিনন্দন! আপনার ভাড়ার অনুরোধ গৃহীত হয়েছে</h2>
        </div>

        <p style="margin: 0 0 16px; font-size: 15px; line-height: 1.6; color: #334155;">
          প্রিয় <strong>{renter_name}</strong>,
        </p>
        <p style="margin: 0 0 20px; font-size: 14px; line-height: 1.7; color: #475569;">
          আনন্দের সাথে জানাচ্ছি যে <strong>"{equipment_name}"</strong> ভাড়ার জন্য আপনার আবেদনটি যন্ত্রের মালিক কর্তৃক অনুমোদিত হয়েছে।
        </p>

        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 18px 20px; margin-bottom: 24px;">
          <h3 style="margin: 0 0 12px; font-size: 14px; font-weight: bold; color: #0f172a;">অনুমোদিত বুকিং তথ্য:</h3>
          <table style="width: 100%; font-size: 13px; line-height: 1.8; color: #334155;">
            <tr>
              <td style="color: #64748b; width: 40%;">যন্ত্রপাতির নাম:</td>
              <td style="font-weight: bold;">{equipment_name}</td>
            </tr>
            <tr>
              <td style="color: #64748b;">মালিকের নাম:</td>
              <td style="font-weight: bold;">{owner_name}</td>
            </tr>
            <tr>
              <td style="color: #64748b;">মালিকের ফোন নম্বর:</td>
              <td style="font-weight: bold; color: #0284c7;">{owner_phone}</td>
            </tr>
            <tr>
              <td style="color: #64748b;">বুকিংয়ের তারিখ:</td>
              <td style="font-weight: bold; color: #15803d;">{dates_str}</td>
            </tr>
            <tr>
              <td style="color: #64748b;">নির্ধারিত মোট ভাড়া:</td>
              <td style="font-weight: bold; color: #15803d; font-size: 15px;">৳ {total_price:,.0f} BDT</td>
            </tr>
          </table>
        </div>

        <p style="margin: 0 0 24px; font-size: 13px; line-height: 1.6; color: #64748b;">
          মাঠে কাজ শুরু করার সুবিধার্থে মালিকের নম্বরে সরাসরি ফোন করে সময় ও জমি সংক্রান্ত বিস্তারিত কথা বলে নিন।
        </p>

        <div style="text-align: center; margin: 24px 0 10px;">
          <a href="http://localhost:5174/equipment" style="background: #15803d; color: #ffffff; text-decoration: none; padding: 13px 26px; border-radius: 10px; font-weight: bold; font-size: 14px; display: inline-block; box-shadow: 0 2px 8px rgba(21,128,61,0.3);">
            আমার বুকিং দেখুন →
          </a>
        </div>
      </td>
    </tr>
    <tr>
      <td style="background-color: #f8fafc; padding: 20px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9;">
        © {settings.APP_NAME} — স্মার্ট প্রযুক্তিতে সমৃদ্ধ কৃষি
      </td>
    </tr>
  </table>
</body>
</html>
"""


def get_rental_rejected_email_html(
    renter_name: str,
    equipment_name: str,
    dates_str: str,
) -> str:
    """Returns a styled HTML email notifying the farmer that their booking request was declined."""
    return f"""<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ভাড়ার অনুরোধ সংক্রান্ত বিজ্ঞপ্তি</title>
</head>
<body style="margin: 0; padding: 24px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f1f5f9; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 16px rgba(0,0,0,0.06);">
    <tr>
      <td style="background: linear-gradient(135deg, #64748b, #475569); padding: 32px 28px; text-align: center; color: #ffffff;">
        <h1 style="margin: 0; font-size: 24px; font-weight: 800;">শিখড় এআই (Shikhor AI)</h1>
        <p style="margin: 6px 0 0; font-size: 14px; opacity: 0.95;">যন্ত্রপাতি বুকিং সংক্রান্ত নোটিশ</p>
      </td>
    </tr>
    <tr>
      <td style="padding: 32px 28px;">
        <p style="margin: 0 0 16px; font-size: 15px; line-height: 1.6; color: #334155;">
          প্রিয় <strong>{renter_name}</strong>,
        </p>
        <p style="margin: 0 0 20px; font-size: 14px; line-height: 1.7; color: #475569;">
          আপনার অনুরোধকৃত <strong>"{equipment_name}"</strong> যন্ত্রটির মালিক নির্ধারিত তারিখে ({dates_str}) ব্যক্তিগত বা কারিগরি কারণে আবেদনটি গ্রহণ করতে পারেননি।
        </p>

        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px 20px; margin-bottom: 24px;">
          <h4 style="margin: 0 0 8px; font-size: 13px; font-weight: bold; color: #0f172a;">বিকল্প পরামর্শ:</h4>
          <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #64748b;">
            আপনার নিকটস্থ এলাকার অন্যান্য মালিকদের তালিকাভুক্ত পাওয়ার টিলার, হারভেস্টার বা ট্রাক্টর ভাড়ার জন্য প্ল্যাটফর্মে সার্চ করুন।
          </p>
        </div>

        <div style="text-align: center; margin: 24px 0 10px;">
          <a href="http://localhost:5174/equipment" style="background: #0284c7; color: #ffffff; text-decoration: none; padding: 13px 26px; border-radius: 10px; font-weight: bold; font-size: 14px; display: inline-block;">
            অন্যান্য যন্ত্রপাতি খুঁজুন →
          </a>
        </div>
      </td>
    </tr>
    <tr>
      <td style="background-color: #f8fafc; padding: 20px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9;">
        © {settings.APP_NAME} — স্মার্ট প্রযুক্তিতে সমৃদ্ধ কৃষি
      </td>
    </tr>
  </table>
</body>
</html>
"""


def get_expert_review_email_html(
    farmer_name: str,
    crop_name: str,
    diagnosis: str,
    treatment: str,
    severity: str,
    expert_name: str,
    notes: Optional[str] = None,
    case_id: Optional[str] = None,
) -> str:
    """Returns a styled HTML email delivering official agricultural expert diagnosis and prescription."""
    severity_map = {
        "high": ("উচ্চ তীব্রতা (জরুরি ব্যবস্থা নিন)", "#dc2626", "#fef2f2"),
        "medium": ("মাঝারি তীব্রতা", "#d97706", "#fffbeb"),
        "low": ("প্রাথমিক পর্যায়", "#16a34a", "#f0fdf4"),
    }
    sev_text, sev_color, sev_bg = severity_map.get(
        severity.lower() if severity else "medium",
        ("পর্যবেক্ষণাধীন", "#2563eb", "#eff6ff")
    )

    notes_section = ""
    if notes and notes.strip():
        notes_section = f"""
        <div style="margin-top: 20px; padding: 16px 20px; background-color: #f8fafc; border-left: 4px solid #64748b; border-radius: 6px;">
          <h4 style="margin: 0 0 6px; font-size: 13px; font-weight: bold; color: #334155;">বিশেষজ্ঞের অতিরিক্ত পরামর্শ:</h4>
          <p style="margin: 0; font-size: 13px; line-height: 1.6; color: #475569;">{notes.strip()}</p>
        </div>
        """

    case_url = "http://localhost:5173/crop-assistant"

    return f"""<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>বিশেষজ্ঞের ফসলের রোগ যাচাই ও প্রেসক্রিপশন রিপোর্ট</title>
</head>
<body style="margin: 0; padding: 24px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f1f5f9; color: #1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 18px rgba(0,0,0,0.06);">
    <!-- Header -->
    <tr>
      <td style="background: linear-gradient(135deg, #15803d, #14532d); padding: 32px 28px; text-align: center; color: #ffffff;">
        <h1 style="margin: 0; font-size: 24px; font-weight: 800; letter-spacing: 0.5px;">শিখড় এআই (Shikhor AI)</h1>
        <p style="margin: 6px 0 0; font-size: 14px; opacity: 0.95;">🌿 কৃষি বিশেষজ্ঞের রোগ যাচাই ও প্রেসক্রিপশন রিপোর্ট</p>
      </td>
    </tr>

    <!-- Body Content -->
    <tr>
      <td style="padding: 32px 28px;">
        <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 12px; padding: 16px 20px; margin-bottom: 24px;">
          <span style="font-size: 13px; font-weight: 700; color: #166534; display: inline-block; background-color: #dcfce7; padding: 3px 10px; border-radius: 20px; margin-bottom: 6px;">✓ কৃষিবিদ দ্বারা যাচাইকৃত</span>
          <h2 style="margin: 0; font-size: 18px; color: #14532d; font-weight: bold;">আপনার ফসলের সমস্যার সমাধান দেওয়া হয়েছে</h2>
        </div>

        <p style="margin: 0 0 16px; font-size: 15px; line-height: 1.6; color: #334155;">
          প্রিয় <strong>{farmer_name}</strong>,
        </p>
        <p style="margin: 0 0 20px; font-size: 14px; line-height: 1.7; color: #475569;">
          আপনার জমাকৃত <strong>{crop_name}</strong> ফসলের নমুনা ছবি ও লক্ষণ কৃষি কর্মকর্তা / বিশেষজ্ঞ <strong>{expert_name}</strong> কর্তৃক নিবিড়ভাবে পর্যবেক্ষণ ও যাচাই করা হয়েছে। বিস্তারিত প্রতিবেদন নিচে দেওয়া হলো:
        </p>

        <!-- Diagnosis Summary Table -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse: collapse; margin-bottom: 24px; background-color: #fafaf9; border-radius: 10px; overflow: hidden; border: 1px solid #e7e5e4;">
          <tr>
            <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #57534e; border-bottom: 1px solid #e7e5e4; width: 35%;">নির্বাচিত ফসল:</td>
            <td style="padding: 12px 16px; font-size: 14px; font-weight: bold; color: #1c1917; border-bottom: 1px solid #e7e5e4;">{crop_name}</td>
          </tr>
          <tr>
            <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #57534e; border-bottom: 1px solid #e7e5e4;">শনাক্তকৃত রোগ:</td>
            <td style="padding: 12px 16px; font-size: 15px; font-weight: bold; color: #047857; border-bottom: 1px solid #e7e5e4;">{diagnosis}</td>
          </tr>
          <tr>
            <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #57534e; border-bottom: 1px solid #e7e5e4;">রোগের তীব্রতা:</td>
            <td style="padding: 12px 16px; font-size: 13px; font-weight: bold; border-bottom: 1px solid #e7e5e4;">
              <span style="color: {sev_color}; background-color: {sev_bg}; padding: 2px 10px; border-radius: 6px;">{sev_text}</span>
            </td>
          </tr>
          <tr>
            <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #57534e;">যাচাইকারী বিশেষজ্ঞ:</td>
            <td style="padding: 12px 16px; font-size: 13px; font-weight: 600; color: #1c1917;">{expert_name} (কৃষি বিশেষজ্ঞ)</td>
          </tr>
        </table>

        <!-- Prescribed Treatment Highlight Box -->
        <div style="background-color: #ecfdf5; border: 2px solid #6ee7b7; border-radius: 12px; padding: 22px; margin-bottom: 20px;">
          <h3 style="margin: 0 0 10px; font-size: 15px; font-weight: 800; color: #065f46; text-transform: uppercase; letter-spacing: 0.5px;">
            💊 বিশেষজ্ঞের প্রেসক্রিপশন ও করণীয় (Prescription):
          </h3>
          <div style="font-size: 14px; line-height: 1.8; color: #064e3b; font-weight: 500; white-space: pre-wrap;">
{treatment}
          </div>
        </div>

        {notes_section}

        <div style="margin-top: 24px; padding: 14px; background-color: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; font-size: 12px; line-height: 1.6; color: #92400e;">
          ⚠️ <strong>সতর্কতা:</strong> বালাইনাশক বা রাসায়নিক প্রয়োগের সময় ব্যক্তিগত সুরক্ষামূলক পোশাক (গ্লাভস ও মাস্ক) পরিধান করুন এবং বাতাসের বিপরীত দিকে স্প্রে করা থেকে বিরত থাকুন।
        </div>

        <!-- Call to Action -->
        <div style="text-align: center; margin: 32px 0 12px;">
          <a href="{case_url}" style="background: #15803d; color: #ffffff; text-decoration: none; padding: 14px 30px; border-radius: 10px; font-weight: bold; font-size: 15px; display: inline-block; box-shadow: 0 3px 10px rgba(21,128,61,0.35);">
            শিখড় অ্যাপে প্রেসক্রিপশন দেখুন →
          </a>
        </div>
      </td>
    </tr>

    <!-- Footer -->
    <tr>
      <td style="background-color: #f8fafc; padding: 20px 24px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9;">
        © {settings.APP_NAME} — বাংলাদেশের কৃষকদের স্মার্ট প্রযুক্তি সঙ্গী | প্রয়োজন হলে সরাসরি উপজেলা কৃষি অফিসে যোগাযোগ করুন।
      </td>
    </tr>
  </table>
</body>
</html>
"""

