"""
Localization Module for AI Medicine Assistant.
Provides full bilingual support for Urdu (Default) and English.
Includes UI labels, audio prompts, drug forms, usage instructions, and common indications.
"""

import re

# Supported Languages
LANG_URDU = "ur"
LANG_ENGLISH = "en"
DEFAULT_LANGUAGE = LANG_URDU

TRANSLATIONS = {
    # ----------------- STAGE 1: SETUP WIZARD -----------------
    "wizard_title": {
        "ur": "🛡️ اے آئی میڈیسن اسسٹنٹ سیٹ اپ وزرڈ",
        "en": "🛡️ AI MEDICINE ASSISTANT SETUP WIZARD"
    },
    "input_pill": {
        "ur": "⌨️ ان پٹ",
        "en": "⌨️ INPUT"
    },
    "audio_pill": {
        "ur": "🔊 آڈیو",
        "en": "🔊 AUDIO"
    },
    "camera_pill": {
        "ur": "📷 کیمرا",
        "en": "📷 CAMERA"
    },
    "connected": {
        "ur": "منسلک ہے",
        "en": "CONNECTED"
    },
    "disconnected": {
        "ur": "منقطع ہے",
        "en": "DISCONNECTED"
    },
    "mouse_kb_connected": {
        "ur": "منسلک (کی بورڈ اور ماؤس مل گیا)",
        "en": "CONNECTED (Keyboard/Mouse Detected)"
    },
    "audio_connected": {
        "ur": "منسلک (اسپیکر فعال ہیں)",
        "en": "CONNECTED (SAPI5 Speakers)"
    },
    "audio_missing": {
        "ur": "آڈیو دستیاب نہیں",
        "en": "LOCAL AUDIO MISSING"
    },
    "select_camera_source": {
        "ur": "کیمرا منتخب کریں",
        "en": "SELECT CAMERA SOURCE"
    },
    "sys_diag_title": {
        "ur": " سسٹم کی تشخیصی جانچ ",
        "en": " SYSTEM DIAGNOSTICS CHECKS "
    },
    "tactile_peripherals": {
        "ur": "کی بورڈ اور ماؤس",
        "en": "Tactile Peripherals"
    },
    "sapi_audio": {
        "ur": "صوتی آڈیو سسٹم",
        "en": "SAPI5 Audio System"
    },
    "cam_conn_title": {
        "ur": " کیمرا کنکشن اور ترتیبات ",
        "en": " CAMERA CONNECTION INTEGRATION "
    },
    "cam_conn_prompt": {
        "ur": "آپ اپنا کیمرا کیسے جوڑنا چاہتے ہیں؟",
        "en": "How would you like to connect your camera device?"
    },
    "local_usb_cam": {
        "ur": "🔌 لوکل یو ایس بی ویب کیم",
        "en": "🔌 Local USB Webcam"
    },
    "wireless_ip_cam": {
        "ur": "🌐 وائرلیس آئی پی کیمرا",
        "en": "🌐 Wireless IP Camera"
    },
    "local_webcam_lbl": {
        "ur": "🔌 لوکل ویب کیم: ",
        "en": "🔌 Local Webcam: "
    },
    "ip_stream_url_lbl": {
        "ur": "آئی پی کیمرا لنک: ",
        "en": "IP Camera Stream URL: "
    },
    "scan_wifi_btn": {
        "ur": "🔍 وائی فائی اسکین کریں",
        "en": "🔍 Auto-Scan Wi-Fi"
    },
    "verify_cam_btn": {
        "ur": "⚡ کیمرا کنکشن چیک کریں [V]",
        "en": "⚡ Verify Camera Connection [V]"
    },
    "rescan_local_btn": {
        "ur": "🔄 لوکل کیمرے دوبارہ اسکین کریں [V]",
        "en": "🔄 Rescan Local Hardware Cameras [V]"
    },
    "verify_ip_btn": {
        "ur": "⚡ آئی پی کیمرا جوڑیں اور چیک کریں [V]",
        "en": "⚡ Connect & Verify IP Camera [V]"
    },
    "preview_box_title": {
        "ur": " کیمرا لائیو پیشگی منظر ",
        "en": " HARDWARE LIVE PREVIEW FEED "
    },
    "preview_standby": {
        "ur": "[ پیشگی منظر تیار ہے ]\n\nبائیں جانب سے کیمرا منتخب کریں\nاور 'کیمرا کنکشن چیک کریں' پر کلک کریں۔",
        "en": "[ PREVIEW STANDBY ]\n\nChoose camera source on left\nand click 'Verify Camera Connection'."
    },
    "launch_dashboard_btn": {
        "ur": "🚀 مین ڈیش بورڈ شروع کریں [L]",
        "en": "🚀 Launch Main Accessibility Dashboard [L]"
    },
    "lang_toggle_btn": {
        "ur": "🌐 زبان: اردو (English کے لیے دبائیں)",
        "en": "🌐 Language: English (Switch to اردو)"
    },

    # ----------------- STAGE 2: WORKSPACE DASHBOARD -----------------
    "app_header": {
        "ur": "👁️ اے آئی میڈیسن اسسٹنٹ سسٹم",
        "en": "👁️ AI MEDICINE ASSISTANT SYSTEM"
    },
    "live_feed_title": {
        "ur": "📷 لائیو کیمرا مانیٹرنگ فیڈ",
        "en": "📷 LIVE STREAM ACCESSIBILITY FEED"
    },
    "product_sig_title": {
        "ur": " دوا کی شناخت اور تفصیلات ",
        "en": " DETECTED PRODUCT SIGNATURE "
    },
    "medicine_name": {
        "ur": "💊 دوا کا نام",
        "en": "💊 Medicine Name"
    },
    "product_strength": {
        "ur": "⚡ دوا کی طاقت / مقدار",
        "en": "⚡ Product Strength"
    },
    "dosage_form": {
        "ur": "📋 دوا کی قسم / شکل",
        "en": "📋 Dosage Form"
    },
    "manufacturer": {
        "ur": "🏭 کمپنی / تیار کنندہ",
        "en": "🏭 Manufacturer"
    },
    "therapeutic_class": {
        "ur": "🔬 طبی زمرہ / فارمولا",
        "en": "🔬 Therapeutic Class"
    },
    "indications_title": {
        "ur": "تصدیق شدہ طبی فوائد اور استعمال:",
        "en": "Verified Medical Indications:"
    },
    "precautions_title": {
        "ur": "طبی درجہ بندی / احتیاطی تدابیر اور نقصانات:",
        "en": "Therapeutic Classification / Side Effects:"
    },
    "data_source_standby": {
        "ur": "ڈیٹا کا ذریعہ: [ انتظار جاری ہے ]",
        "en": "Data Source: [ STANDBY ]"
    },
    "data_source_local": {
        "ur": "ڈیٹا کا ذریعہ: مقامی محفوظ ڈیٹا بیس",
        "en": "Data Source: LOCAL DATABASE"
    },
    "data_source_online": {
        "ur": "ڈیٹا کا ذریعہ: لائیو ویب نیٹ ورک",
        "en": "Data Source: SECURE WEB SCRAPER"
    },
    "data_source_failed": {
        "ur": "ڈیٹا کا ذریعہ: ریکارڈ نہیں ملا",
        "en": "Data Source: FAILED MATCH DEFERRAL"
    },
    "status_active": {
        "ur": "سسٹم فعال ہے",
        "en": "System Active"
    },
    "waiting": {
        "ur": "انتظار جاری ہے...",
        "en": "Waiting..."
    },
    "capture_btn": {
        "ur": "📸 دوا کا لیبل اسکین کریں [SPACE / C]",
        "en": "📸 CAPTURE BOTTLE LABEL [SPACE / C]"
    },
    "retry_btn": {
        "ur": "🔄 دوبارہ لائیو کیمرا اسکین کریں [R]",
        "en": "🔄 RETRY LIVE SCANNER FEED [R]"
    },
    "quit_btn": {
        "ur": "🛑 سسٹم بند کریں [Q]",
        "en": "🛑 SHUTDOWN SYSTEM WORKSPACE [Q]"
    },
    "online_search_btn": {
        "ur": "🔮 انٹرنیٹ پر تلاش کریں [I]",
        "en": "🔮 INTERNET SEARCH VERIFICATION [I]"
    },
    "change_lang_btn": {
        "ur": "🌐 زبان تبدیل کریں: English [T]",
        "en": "🌐 زبان تبدیل کریں: اردو [T]"
    },
    "no_accurate_match": {
        "ur": "کوئی درست ریکارڈ نہیں ملا",
        "en": "NO ACCURATE MATCH FOUND"
    },
    "ambiguous_match_text": {
        "ur": "مقامی تلاش میں تسلی بخش نتیجہ نہیں ملا۔ پڑھا گیا متن: '{raw_ocr}'",
        "en": "Offline fuzzy checks returned ambiguous match scores. Extracted text: '{raw_ocr}'"
    },
    "safety_filtered_text": {
        "ur": "مریض کے تحفظ کے لیے غیر یقینی نتائج کو خارج کر دیا گیا ہے۔",
        "en": "Database matches filtered to ensure product identification safety."
    },
    "align_bottle_flat_status": {
        "ur": "حفاظتی جانچ: براہ کرم بوتل یا دوا کو سیدھا رکھیں",
        "en": "SAFETY CHECK PENDING: Please align bottle flat"
    },
    "analyzing_label": {
        "ur": "لیبل کا تجزیہ ہو رہا ہے...",
        "en": "ANALYZING LABEL TEXT..."
    },
    "extracting_text": {
        "ur": "متن نکالا جا رہا ہے...",
        "en": "EXTRACTING TEXT..."
    },
    "match_successful": {
        "ur": "کامیابی سے تصدیق ہو گئی",
        "en": "MATCH SUCCESSFUL"
    },
    "online_cache_sync": {
        "ur": "آن لائن ڈیٹا محفوظ ہو گیا",
        "en": "ONLINE CACHE SYNC SUCCESSFUL"
    },
    "local_lookup_incomplete": {
        "ur": "مقامی فہرست میں نہیں ملا ❌ -> آن لائن تلاش جاری ہے...",
        "en": "LOCAL LOOKUP INCOMPLETE ❌ -> QUERYING LIVE WEB DATA..."
    },
    "offline_bind_failed": {
        "ur": "انٹرنیٹ کنکشن دستیاب نہیں ہے",
        "en": "OFFLINE STATE - INTERNET BIND FAILED"
    },
    "rescan_required": {
        "ur": "حفاظتی انتباہ: دوبارہ اسکین درکار ہے - دوا سیدھی رکھیں",
        "en": "SAFETY ALERT: RESCAN REQUIRED - ADJUST POSITIONING"
    },
    "camera_verified_status": {
        "ur": "کیمرا کامیابی سے منسلک ہو گیا",
        "en": "Camera Verified Successfully"
    },
    "camera_failed_status": {
        "ur": "کیمرا کنکشن ناکام ہو گیا",
        "en": "Camera Verification Failed"
    },
    "verifying_camera_status": {
        "ur": "کیمرا کنکشن کی جانچ ہو رہی ہے...",
        "en": "Verifying camera connection..."
    },
    "simulator_verified_status": {
        "ur": "سمولیٹر کامیابی سے فعال ہو گیا",
        "en": "Simulator Verified Successfully"
    },
    "live_camera_active_status": {
        "ur": "لائیو کیمرا ٹریکنگ فعال ہے",
        "en": "Live Camera Tracking Active"
    },
    "auto_detecting_webcam_status": {
        "ur": "لوکل ویب کیم تلاش ہو رہا ہے...",
        "en": "AUTO-DETECTING LOCAL WEBCAM..."
    },
    "no_webcam_detected_status": {
        "ur": "کوئی ویب کیم نہیں ملا",
        "en": "NO WEBCAM DETECTED"
    },
    "scanning_wifi_status": {
        "ur": "وائی فائی نیٹ ورک پر کیمرے تلاش ہو رہے ہیں...",
        "en": "SCANNING WI-FI NETWORK FOR CAMERAS..."
    },
    "camera_found_wifi_status": {
        "ur": "وائی فائی پر کیمرا مل گیا",
        "en": "CAMERA FOUND ON WI-FI"
    },
    "no_cameras_wifi_status": {
        "ur": "وائی فائی پر کوئی کیمرا نہیں ملا",
        "en": "NO CAMERAS FOUND ON WI-FI"
    },
    "network_scan_error_status": {
        "ur": "نیٹ ورک اسکین میں خرابی",
        "en": "NETWORK SCAN ERROR"
    },
}

# ----------------- SPOKEN VOICE MESSAGES -----------------
SPOKEN_MESSAGES = {
    "welcome_wizard": {
        "ur": "اے آئی میڈیسن اسسٹنٹ سیٹ اپ وزرڈ میں خوش آمدید۔ برائے مہربانی اپنا کیمرا منتخب کریں اور تصدیق کریں۔ لوکل ویب کیم کے لیے یو، وائرلیس کیمرے کے لیے ڈبلیو، تصدیق کے لیے وی، اور مین ڈیش بورڈ شروع کرنے کے لیے ایل دبائیں۔ آپ کسی بھی وقت کیو دبا کر پروگرام بند کر سکتے ہیں۔",
        "en": "Welcome to the AI Medicine Assistant Setup Wizard. Please verify your camera connection. Press U for Local USB Webcam, or W for Wireless IP Camera. Then press V to verify the connection. Once verified, press L to launch the main workspace dashboard. You can press Q to quit the program at any time."
    },
    "welcome_dashboard": {
        "ur": "اے آئی میڈیسن اسسٹنٹ فعال ہے۔ خوش آمدید۔",
        "en": "AI Medicine Assistant active. Welcome."
    },
    "cam_verified": {
        "ur": "کیمرا کنکشن کی تصدیق کامیابی سے ہو گئی۔",
        "en": "Camera connection verified successfully."
    },
    "cam_failed": {
        "ur": "کیمرا کنکشن ناکام ہو گیا۔ براہ کرم ترتیبات چیک کریں اور دوبارہ کوشش کریں۔",
        "en": "Camera connection failed. Please check the camera settings and try again."
    },
    "simulator_verified": {
        "ur": "سمولیٹر کنکشن کی تصدیق کامیابی سے ہو گئی۔",
        "en": "Simulator connection verified successfully."
    },
    "cannot_launch_need_verify": {
        "ur": "ڈیش بورڈ شروع نہیں ہو سکتا۔ براہ کرم پہلے وی دبا کر کیمرا چیک کریں۔",
        "en": "Cannot launch workspace. Please verify your camera connection first by pressing V."
    },
    "auto_detect_cam": {
        "ur": "لوکل کیمرا خودکار طور پر تلاش کیا جا رہا ہے۔",
        "en": "Auto-detecting local hardware camera."
    },
    "selected_ip_cam": {
        "ur": "وائرلیس آئی پی کیمرا منتخب کیا گیا ہے۔",
        "en": "Selected Wireless IP Camera stream input."
    },
    "scanning_wifi": {
        "ur": "موبائل کیمروں کے لیے لوکل نیٹ ورک اسکین کیا جا رہا ہے۔",
        "en": "Scanning local network for mobile cameras."
    },
    "camera_found": {
        "ur": "کیمرا مل گیا ہے، جوڑا جا رہا ہے۔",
        "en": "Camera found. Connecting."
    },
    "no_camera_found": {
        "ur": "آپ کے وائی فائی پر کوئی موبائل کیمرا نہیں ملا۔",
        "en": "No mobile cameras were found on your Wi-Fi network."
    },
    "no_local_camera_detected": {
        "ur": "کوئی لوکل کیمرا نہیں ملا۔ براہ کرم کنکشن چیک کریں۔",
        "en": "No working local camera was detected. Please check connection."
    },
    "guidance_right": {
        "ur": "دائیں",
        "en": "Right"
    },
    "guidance_left": {
        "ur": "بائیں",
        "en": "Left"
    },
    "guidance_straight": {
        "ur": "سیدھا رکھیں",
        "en": "Straight"
    },
    "guidance_aligned": {
        "ur": "دوا بلکل سیدھی ہے",
        "en": "Aligned"
    },
    "guidance_searching": {
        "ur": "دوا تلاش کی جا رہی ہے، براہ کرم دوا کو کیمرے کے سامنے رکھیں۔",
        "en": "Searching for medicine. Please place the container in front of the camera."
    },
    "captured": {
        "ur": "تصویر محفوظ کر لی گئی ہے، لیبل پڑھا جا رہا ہے، برائے مہربانی انتظار کریں۔",
        "en": "Frame captured. Running offline character extraction, please wait."
    },
    "online_searching": {
        "ur": "دوا کا ریکارڈ مقامی فہرست میں نہیں ملا۔ برائے مہربانی انتظار کریں، آن لائن نیٹ ورک پر تصدیق کی جا رہی ہے۔",
        "en": "Medicine details not found in local records. Please wait, the system is now searching the online network database for verified information."
    },
    "offline_no_match": {
        "ur": "دوا مقامی طور پر رجسٹرڈ نہیں ہے۔ آن لائن تلاش کے لیے انٹرنیٹ ضروری ہے۔",
        "en": "Medicine not registered locally. Internet connection required for online verification."
    },
    "rescan_guide": {
        "ur": "تصدیق ناکام ہو گئی۔ دوا کی غلطی سے بچنے کے لیے دوبارہ اسکین کریں۔ بوتل کو کیمرے کے سامنے سیدھا پکڑیں اور اسپیس بار دبائیں۔",
        "en": "Verification failed. To prevent medicine error, information was discarded. Please follow these adjustments for re-capture: Ensure your fingers are not covering the text label. Hold the bottle or tube perfectly straight, upright, and steady about 6 inches directly in front of the camera. Press Spacebar to try again."
    },
    "returning_live": {
        "ur": "لائیو کیمرا ٹریکنگ پر واپس جا رہے ہیں۔",
        "en": "Returning to live camera tracking."
    },
    "shutdown": {
        "ur": "میڈیسن اسسٹنٹ بند ہو رہا ہے۔ اللہ حافظ۔",
        "en": "Shutting down medicine assistant. Goodbye."
    },
    "lang_switched_ur": {
        "ur": "زبان اردو میں تبدیل کر دی گئی ہے۔",
        "en": "Language set to Urdu."
    },
    "lang_switched_en": {
        "ur": "Language switched to English.",
        "en": "Language switched to English."
    }
}

# Dosage forms in Urdu
DOSAGE_FORMS_URDU = {
    "tablet": "ٹیبلٹ (گولی)",
    "tablets": "ٹیبلٹ (گولیاں)",
    "tab": "ٹیبلٹ",
    "capsule": "کیپسول",
    "capsules": "کیپسول",
    "cap": "کیپسول",
    "syrup": "شربت (سیرپ)",
    "suspension": "سسپنشن (شربت)",
    "susp": "سسپنشن",
    "cream": "کریم",
    "ointment": "مرہم (آئنٹمنٹ)",
    "gel": "جیل",
    "injection": "انجیکشن",
    "inj": "انجیکشن",
    "drops": "قطرے (ڈراپس)",
    "sachet": "ساشے (پاؤڈر)",
    "powder": "پاؤڈر",
    "solution": "محلول (سولوشن)",
    "spray": "اسپرے",
    "lotion": "لوشن",
    "inhaler": "انہیلر",
    "eye drops": "آنکھوں کے قطرے",
    "ear drops": "کان کے قطرے"
}

# Common indications translation mapping
COMMON_INDICATIONS_URDU = {
    "fever": "بخار",
    "moderate to severe painful conditions": "درمیانہ اور شدید درد",
    "moderate to severe pain": "درمیانہ اور شدید درد",
    "painful conditions": "شدید درد",
    "post-surgical pain": "آپریشن کے بعد کا درد",
    "severe pain": "شدید درد",
    "mild to moderate pain": "ہلکا اور درمیانہ درد",
    "headache": "سر درد",
    "migraine": "درد شقیقہ (آدھے سر کا درد)",
    "body ache": "جسم کا درد",
    "body pain": "جسم کا درد",
    "body aches": "جسم کا درد",
    "toothache": "دانت کا درد",
    "sore throat": "گلے کی سوزش اور درد",
    "cold": "نزلہ و زکام",
    "cough": "کھانسی",
    "chest congestion": "سینے کی جکڑن اور بلغم",
    "bronchitis": "سانس کی نالیوں کی سوزش",
    "flu": "فلو",
    "allergy": "الرجی",
    "allergic rhinitis": "چھینکیں اور نزلاتی الرجی",
    "sneezing": "چھینکیں اور الرجی",
    "runny nose": "ناک بہنا اور زکام",
    "watery eyes": "آنکھوں سے پانی بہنا اور الرجی",
    "bacterial infections": "بیکٹیریل انفیکشن",
    "infection": "انفیکشن",
    "skin infection": "جلد کا انفیکشن",
    "eczema": "چمبل اور ایگزیما",
    "dermatitis": "جلد کی الرجی اور سوزش",
    "psoriasis": "سورائسس اور خشک کھجلی",
    "itching": "خارش اور جلن",
    "burns": "جلنے کے زخم اور چھالے",
    "wound": "زخم اور چوٹ",
    "cuts": "کٹے ہوئے زخم اور خراشیں",
    "athlete's foot": "پاؤں کا فنگل انفیکشن",
    "ringworm": "داد اور چنبل",
    "fungal infection": "فنگل انفیکشن اور داد",
    "fungal": "فنگل انفیکشن",
    "yeast infection": "فنگس کا انفیکشن",
    "inflammation": "سوزش اور ورم",
    "hypertension": "بلڈ پریشر کی زیادتی",
    "diabetes": "ذیابیطس (شوگر)",
    "acidity": "معدے کی تیزابیت اور جلن",
    "heartburn": "سینے کی جلن",
    "gerd": "معدے کی تیزابیت اور جلن",
    "acid reflux": "کھٹے ڈکار اور سینے کی جلن",
    "peptic ulcer": "معدے کا السر",
    "nausea": "متلی اور قے",
    "vomiting": "الٹی اور متلی",
    "motion sickness": "سفر کی متلی اور الٹی",
    "diarrhea": "دست اور موشن",
    "dysentery": "پیچش اور مروڑ",
    "amoebiasis": "پیٹ کے جراثیم اور مروڑ",
    "cramps": "پیٹ کا مروڑ اور درد",
    "spasms": "پیٹ کا درد اور اینٹھن",
    "muscle pain": "پٹھوں کا درد",
    "joint pain": "جوڑوں کا درد اور گٹھیا",
    "arthritis": "جوڑوں کا درد اور سوزش",
    "sprains": "موچ اور کھچاؤ",
    "asthma": "دمہ اور سانس کی تنگی",
    "nasal congestion": "بند ناک اور سینوس کا دباؤ",
    "sinus pressure": "سینوس کی تکلیف",
    "antifungal": "فنگل انفیکشن اور داد"
}

BRAND_NAMES_URDU = {
    # Tubes, Creams & Ointments
    "betasalic": "بیٹاسالک",
    "betasalic ointment": "بیٹاسالک مرہم",
    "betasalic lotion": "بیٹاسالک لوشن",
    "polyfax": "پولی فیکس",
    "polyfax plus": "پولی فیکس پلس",
    "betnovate": "بیٹنوویٹ",
    "betnovate-n": "بیٹنوویٹ این",
    "betnovate n": "بیٹنوویٹ این",
    "betnovate-c": "بیٹنوویٹ سی",
    "dermovate": "ڈرموویٹ",
    "dermovate-nn": "ڈرموویٹ این این",
    "fucidin": "فیوسیڈن",
    "fucicort": "فیوسی کارٹ",
    "kenacomb": "کینکومب",
    "travocort": "ٹراووکارٹ",
    "travogen": "ٹراووجن",
    "canesten": "کینسٹین",
    "mobic": "موبک",
    "voltral": "وولٹرال",
    "voltral emulgel": "وولٹرال ایمل جیل",
    "voren": "وورن",
    "hydrozole": "ہائیڈروزول",
    "hydrocortisone": "ہائیڈروکارٹیسون",
    "daktarin": "ڈاکٹرین",
    "ketovate": "کیٹوویٹ",
    "bactroban": "بیکٹروبان",
    "burnol": "برنول",
    "fastum": "فاسٹم جیل",
    "fastum gel": "فاسٹم جیل",
    "candid": "کینڈیڈ",
    "candid-b": "کینڈیڈ بی",
    "cutivate": "کیوٹیویٹ",
    "advantan": "ایڈوانٹان",
    "genticin": "جینٹیسن",
    "quench": "کوینچ",
    "cloben-g": "کلوبین جی",
    "lamisil": "لیمیسل",
    "terbisil": "ٹربیسل",
    "zovirax": "زوویریکس",
    "acyclovir": "ایسائیکلوویر",
    "moov": "موو",
    "deep heat": "ڈیپ ہیٹ",

    # Syrups, Liquids & Suspensions
    "hydryllin": "ہائیڈریلین",
    "hydryllin dm": "ہائیڈریلین ڈی ایم",
    "pulmonol": "پلمونول",
    "tusdec": "ٹَسڈیک",
    "calpol": "کالپول",
    "calpol 6 plus": "کالپول سکس پلس",
    "calpol syrup": "کالپول شربت",
    "sancos": "سینکوس",
    "mucocaine": "میوکوکین",
    "acefyl": "ایسیفائل",
    "acefyl cough": "ایسیفائل کف سیرپ",
    "ventolin": "وینٹولن",
    "amoxil": "اموکسل",
    "cefspan": "سیفسپین",
    "ceporex": "سیپوریکس",
    "basoquin": "بیسوکوین",
    "klaricid": "کلیریسیڈ",
    "entamizole": "اینٹامیزول",
    "entamizole ds": "اینٹامیزول ڈی ایس",
    "gaviscon": "گیوسکان",
    "gaviscon double action": "گیوسکان ڈبل ایکشن",
    "gravinate": "گریوی نیٹ",
    "smecta": "سمیکٹا",
    "instaflex": "انسٹافلیکس",

    # Tablets & Capsules
    "panadol": "پیناڈول",
    "panadol extra": "پیناڈول ایکسٹرا",
    "panadol cf": "پیناڈول کولڈ اینڈ فلو",
    "panadol night": "پیناڈول نائٹ",
    "panadol syrup": "پیناڈول شربت",
    "panadol forte": "پیناڈول فورٹ",
    "arinac": "ایرینیک",
    "arinac forte": "ایرینیک فورٹ",
    "augmentin": "اگمنٹن",
    "augmentin ds": "اگمنٹن ڈی ایس",
    "disprin": "ڈسپرین",
    "disprin direct": "ڈسپرین ڈائریکٹ",
    "brufen": "بروفین",
    "brufen plus": "بروفین پلس",
    "brufen ds": "بروفین ڈی ایس",
    "flagyl": "فلیجل",
    "flagyl 400mg": "فلیجل 400 ملی گرام",
    "nexum": "نیکسم",
    "nexium": "نیکسیم",
    "rigix": "ریجکس",
    "zyrtec": "زیریٹیک",
    "softin": "سوفٹن",
    "nuberol": "نیوبرول",
    "nuberol forte": "نیوبرول فورٹ",
    "risek": "رائزک",
    "ponstan": "پونسٹان",
    "ponstan forte": "پونسٹان فورٹ",
    "flyp": "فلائپ",
    "surbex": "سربیکس",
    "surbex-z": "سربیکس زی",
    "surbex z": "سربیکس زی",
    "cac 1000": "سی اے سی ایک ہزار",
    "cac 1000 plus": "سی اے سی ایک ہزار پلس",
    "leflox": "لیفوکس",
    "motilium": "موٹیلیم",
    "buscopan": "بسکوپان",
    "spasfon": "اسپاسفون",
    "cipro": "سِپرو",
    "ciproxin": "سِپروکسن",
    "velosef": "ویلو سیف",
    "tonoflex": "ٹونوفلیکس",
    "tonoflex-p": "ٹونوفلیکس پی",
    "tonoflex p": "ٹونوفلیکس پی",
    "tonoflex sr": "ٹونوفلیکس ایس آر",
    "tonoflex forte": "ٹونوفلیکس فورٹ",
    "tramadol": "ٹرا ماڈول",

    # Comprehensive Pakistani Pharmacopeia Coverage
    "cac-1000": "سی اے سی ایک ہزار",
    "cac 1000": "سی اے سی ایک ہزار",
    "evion": "ایویون",
    "glucophage": "گلوکوفاج",
    "ispaghol": "اسپغول",
    "loprin": "لوپرن",
    "lowplat": "لوپلیٹ",
    "mucaine": "میوکین",
    "ors": "او آر ایس",
    "pyodine": "پائیوڈین",
    "septran": "سیپٹران",
    "septran ds": "سیپٹران ڈی ایس",
    "skinoren": "اسکنورین",
    "somogel": "سوموجیل",
    "xanax": "زینیکس",
    "zestril": "زیسٹریل",
    "azomax": "ایزومیکس",
    "bonjela": "بونجیلا",
    "citra-alka": "سٹرا الکا",
    "co-amoxiclav": "کو اموکسیکلاو",
    "corex": "کوریکس",
    "cranmax": "کرین میکس",
    "cravit": "کراوٹ",
    "dalacin-t": "ڈلاسن ٹی",
    "dalacin t": "ڈلاسن ٹی",
    "fesovit": "فیسووِٹ",
    "lipiget": "لپی گیٹ",
    "selsun": "سیلسن",
    "selsun blue": "سیلسن بلیو",
    "velo": "ویلو",
    "betamethasone": "بیٹامیتھاسون",
    "ketoprofen": "کیٹوپروفین",
    "acetone": "ایسیٹون",
    "ennerzo": "اینرزو",
    "areth": "ایریتھ",
    "dhn": "ڈی ایچ این",
    "hlla": "ہلہ",
    "ina": "آئینا",
    "kiri": "کیری",
    "tati": "ٹیٹی",
    "wua": "ڈبلیو یو اے",
    "ear": "ایئر ڈراپس",

    # Generic & Form descriptors
    "paracetamol": "پیراسیٹامول",
    "ibuprofen": "آئبوپروفین",
    "aspirin": "ایسپرین",
    "omeprazole": "اومیپرازول",
    "amoxicillin": "اموکسیسلن",
    "ciprofloxacin": "سِپروفلوکساسین",
    "metronidazole": "میٹرونیڈازول",
    "cetirizine": "سیٹریزین",
    "loratadine": "لوراٹاڈین",
    "dimenhydrinate": "ڈائیمن ہائیڈرینیٹ",
    "extra": "ایکسٹرا",
    "forte": "فورٹ",
    "plus": "پلس",
    "junior": "جونیئر",
    "infant": "انفینٹ",
    "syrup": "شربت",
    "suspension": "سسپنشن",
    "tablet": "گولی",
    "tablets": "گولیاں",
    "capsule": "کیپسول",
    "capsules": "کیپسول",
    "cream": "کریم",
    "ointment": "مرہم",
    "gel": "جیل",
    "drops": "ڈراپس",
    "sachet": "سیچٹ"
}

def get_text(key: str, lang: str = DEFAULT_LANGUAGE, default: str = "") -> str:
    """Retrieves translated UI text by key."""
    if key in TRANSLATIONS:
        return TRANSLATIONS[key].get(lang, TRANSLATIONS[key].get("en", default or key))
    if key in SPOKEN_MESSAGES:
        return SPOKEN_MESSAGES[key].get(lang, SPOKEN_MESSAGES[key].get("en", default or key))
    return default or key

def get_spoken(key: str, lang: str = DEFAULT_LANGUAGE, default: str = "") -> str:
    """Retrieves spoken voice prompt text by key."""
    if key in SPOKEN_MESSAGES:
        return SPOKEN_MESSAGES[key].get(lang, SPOKEN_MESSAGES[key].get("en", default or key))
    if key in TRANSLATIONS:
        return TRANSLATIONS[key].get(lang, TRANSLATIONS[key].get("en", default or key))
    return default or key

def translate_form_to_urdu(form: str) -> str:
    """Translates common dosage form names to readable Urdu."""
    if not form or form == "N/A":
        return "معلوم نہیں"
    form_lower = form.lower().strip()
    for eng, ur in DOSAGE_FORMS_URDU.items():
        if eng in form_lower:
            return ur
    return form

def transliterate_latin_to_urdu(text: str) -> str:
    """
    Phonetic transliteration of remaining Latin/English words to Urdu script
    so that Piper Urdu TTS never speaks raw English letters or foreign accents.
    """
    digraphs = [
        ('ch', 'چ'), ('sh', 'ش'), ('kh', 'خ'), ('ph', 'ف'), ('th', 'تھ'),
        ('gh', 'غ'), ('zh', 'ژ'), ('ee', 'ی'), ('oo', 'و'), ('ou', 'او')
    ]
    singles = {
        'a': 'ا', 'b': 'ب', 'c': 'ک', 'd': 'ڈ', 'e': 'ے', 'f': 'ف',
        'g': 'گ', 'h': 'ہ', 'i': 'ی', 'j': 'ج', 'k': 'ک', 'l': 'ل',
        'm': 'م', 'n': 'ن', 'o': 'و', 'p': 'پ', 'q': 'ق', 'r': 'ر',
        's': 'س', 't': 'ٹ', 'u': 'یو', 'v': 'و', 'w': 'و', 'x': 'ایکس',
        'y': 'ی', 'z': 'ز'
    }

    def convert_word(m):
        w = m.group(0).lower()
        res = ''
        i = 0
        while i < len(w):
            matched = False
            for dg, ur in digraphs:
                if w.startswith(dg, i):
                    res += ur
                    i += len(dg)
                    matched = True
                    break
            if not matched:
                c = w[i]
                res += singles.get(c, c)
                i += 1
        return res

    return re.sub(r'[a-zA-Z]+', convert_word, text)

def translate_brand_to_urdu(name: str) -> str:
    """Translates medicine brand names and variants to fluent Urdu script."""
    if not name or name == "N/A":
        return "غیر معروف دوا"
    
    # Clean internal serials (SR-xxxx) and trailing dosage noise for natural spoken delivery
    cleaned = re.sub(r'\bSR-\d+\b', '', name, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b\d+(\.\d+)?\s*(mg|ml|g|gm|mcg|iu|%|s)\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'[/,;:\(\)\[\]]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip('- ')
    if not cleaned:
        cleaned = name.strip()
        
    result = cleaned
    # Sort keys by length descending to match longest phrases first (e.g., surbex-z before surbex)
    for eng_brand, urdu_brand in sorted(BRAND_NAMES_URDU.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = re.compile(rf'\b{re.escape(eng_brand)}\b', re.IGNORECASE)
        result = pattern.sub(urdu_brand, result)
        
    # Phonetic fallback for any remaining English words
    result = transliterate_latin_to_urdu(result)
    return result

def translate_indication_to_urdu(indication: str, for_speech: bool = False) -> str:
    """Translates known medical indications to clear Urdu text where possible."""
    if not indication or indication == "N/A":
        return "طبی تفصیلات اور استعمال لیبل پر دیکھیں۔" if for_speech else "طبی تفصیلات لیبل پر دیکھیں۔"
    
    ind_lower = indication.lower()
    translated_parts = []
    
    # Check indications ordered by specificity (longest phrase first)
    for eng, ur in sorted(COMMON_INDICATIONS_URDU.items(), key=lambda x: len(x[0]), reverse=True):
        if eng in ind_lower:
            # Avoid adding sub-phrases or duplicates if already covered
            if not any(ur in p or p in ur for p in translated_parts):
                translated_parts.append(ur)
            
    if translated_parts:
        if for_speech:
            if len(translated_parts) == 1:
                return translated_parts[0] + " کے لیے"
            return "، ".join(translated_parts[:-1]) + " اور " + translated_parts[-1] + " کے لیے"
        return "، ".join(translated_parts) + f" ({indication})"
        
    if for_speech:
        return "ڈاکٹر کی ہدایت کے مطابق تجویز کردہ بیماری کے لیے"
    return indication

def normalize_urdu_speech_text(text: str) -> str:
    """Replaces English units, dosage symbols, and abbreviations with fluent Urdu speech equivalents."""
    if not text:
        return ""
    
    # 1. Compound units
    t = re.sub(r'(\d+)\s*mg\s*/\s*(\d+)\s*ml', r'\1 ملی گرام فی \2 ملی لیٹر', text, flags=re.IGNORECASE)
    # 2. Single units
    t = re.sub(r'(\d+)\s*mg\b', r'\1 ملی گرام', t, flags=re.IGNORECASE)
    t = re.sub(r'(\d+)\s*ml\b', r'\1 ملی لیٹر', t, flags=re.IGNORECASE)
    t = re.sub(r'(\d+)\s*mcg\b', r'\1 مائیکرو گرام', t, flags=re.IGNORECASE)
    t = re.sub(r'(\d+)\s*gm?\b', r'\1 گرام', t, flags=re.IGNORECASE)
    t = re.sub(r'(\d+)\s*iu\b', r'\1 انٹرنیشنل یونٹ', t, flags=re.IGNORECASE)
    t = re.sub(r'(\d+)\s*%', r'فیصد \1', t)
    
    # 3. Common English phrases/abbreviations
    replacements = {
        "mg": "ملی گرام",
        "ml": "ملی لیٹر",
        "g": "گرام",
        "gm": "گرام",
        "N/A": "معلوم نہیں",
        "None": "کوئی خاص منفی اثرات نہیں",
        "No major side effects": "کوئی خاص منفی اثرات نہیں",
        "Safe within recommended dose": "تجویز کردہ مقدار میں محفوظ دوا ہے۔",
        "Take with food": "کھانے کے بعد استعمال کریں",
        "Take on empty stomach": "نہار منہ استعمال کریں"
    }
    for eng, ur in replacements.items():
        t = re.sub(rf'\b{re.escape(eng)}\b', ur, t, flags=re.IGNORECASE)
        
    return t

SIDE_EFFECTS_PHRASES = [
    (r'external use only', 'صرف بیرونی استعمال کے لیے ہے۔ آنکھوں سے دور رکھیں۔'),
    (r'avoid (?:contact with )?eyes', 'آنکھوں میں لگنے سے بچائیں۔'),
    (r'do not exceed', 'تجویز کردہ مقدار سے زیادہ استعمال نہ کریں۔'),
    (r'take (?:with|after) food', 'معدے کی حفاظت کے لیے کھانے کے بعد لیں۔'),
    (r'empty stomach', 'نہار منہ استعمال کریں۔'),
    (r'may cause (?:mild )?drowsiness|drowsiness', 'اس سے غنودگی ہو سکتی ہے، احتیاط کریں۔'),
    (r'strictly avoid alcohol', 'علاج کے دوران نشہ آور اشیاء سے پرہیز کریں۔'),
    (r'complete (?:the )?full (?:prescribed )?course', 'ڈاکٹر کی ہدایت کے مطابق پورا کورس مکمل کریں۔'),
    (r'dissolve in water', 'استعمال سے پہلے پانی میں حل کر لیں۔'),
    (r'shake well', 'استعمال سے پہلے شیشی کو اچھی طرح ہلائیں۔'),
    (r'consult (?:a )?physician|consult pharmacist', 'ڈاکٹر یا فارماسسٹ کی ہدایت کے مطابق استعمال کریں۔'),
    (r'follow physician', 'ڈاکٹر کے نسخے کے مطابق استعمال کریں۔'),
    (r'safe within recommended', 'تجویز کردہ مقدار میں محفوظ دوا ہے۔'),
    (r'over-the-counter', 'عام ضرورت کے مطابق استعمال کریں۔'),
    (r'prescription', 'ڈاکٹر کی ہدایت کے مطابق استعمال کریں۔'),
    (r'avoid in peptic ulcer', 'معدے کے السر والے مریض احتیاط کریں۔'),
    (r'pregnant|pregnancy', 'حمل میں ڈاکٹر کے مشورے کے بغیر نہ لیں۔'),
    (r'nausea', 'متلی کی کیفیت ہو سکتی ہے'),
    (r'dizziness', 'چکر آ سکتے ہیں'),
    (r'headache', 'ہلکا سر درد ہو سکتا ہے'),
    (r'stomach upset', 'معدے کی خرابی سے بچنے کے لیے کھانے کے ساتھ لیں۔'),
    (r'allergic reaction', 'الرجی کی صورت میں فوراً ڈاکٹر سے رجوع کریں۔'),
    (r'tramadol|opioid', 'یہ شدید درد کی دوا ہے، غنودگی اور چکر کا باعث بن سکتی ہے۔ نشہ آور اشیاء سے پرہیز کریں۔'),
    (r'salicylic|keratolytic', 'صرف متاثرہ سخت جلد پر لگائیں، صحت مند جلد اور آنکھوں سے بچائیں۔'),
    (r'betamethasone|corticosteroid', 'ڈاکٹر کے بتائے ہوئے وقت سے زیادہ دیر تک مسلسل استعمال نہ کریں۔')
]

def translate_side_effects_to_urdu(text: str, form: str = "") -> str:
    """
    Translates pharmaceutical precautions, side effects, and warning instructions
    into pure, natural, fluent Urdu, eliminating awkward English pronunciations in Urdu mode.
    """
    if not text or text == "N/A":
        if any(f in form.lower() for f in ['cream', 'ointment', 'gel', 'tube']):
            return "صرف متاثرہ صاف جلد پر لگائیں اور آنکھوں سے دور رکھیں۔"
        elif any(f in form.lower() for f in ['syrup', 'suspension', 'liquid']):
            return "استعمال سے پہلے شیشی کو اچھی طرح ہلائیں اور ڈاکٹر کی ہدایت کے مطابق لیں۔"
        return "ڈاکٹر کی ہدایت کے مطابق استعمال کریں اور مقررہ مقدار سے تجاوز نہ کریں۔"

    t_lower = text.lower()
    urdu_points = []

    for pattern, urdu_trans in SIDE_EFFECTS_PHRASES:
        if re.search(pattern, t_lower):
            if urdu_trans not in urdu_points:
                urdu_points.append(urdu_trans)

    if urdu_points:
        clean_points = [p.rstrip('۔. ') + '۔' for p in urdu_points]
        return " ".join(clean_points)

    # Form-specific fallback if no specific phrase matched
    if any(f in form.lower() for f in ['cream', 'ointment', 'gel', 'tube']):
        return "صرف بیرونی استعمال کے لیے ہے۔ ضرورت سے زیادہ نہ لگائیں۔"
    elif any(f in form.lower() for f in ['syrup', 'suspension', 'liquid']):
        return "استعمال سے پہلے اچھی طرح ہلائیں اور ڈاکٹر کی ہدایت کے مطابق لیں۔"

    return "ڈاکٹر کی ہدایت کے مطابق استعمال کریں اور تجویز کردہ مقدار سے زیادہ نہ لیں۔"



