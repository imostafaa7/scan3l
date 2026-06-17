# ⚡ scan3l - Ultimate Bug Bounty Recon & Vulnerability Scanner ⚡

<p align="center">
  <img src="https://img.shields.io/badge/Language-Python%203-blue.svg?style=for-the-badge&logo=python" alt="Python 3">
  <img src="https://img.shields.io/badge/Platform-Kali%20Linux%20|%20Debian-red.svg?style=for-the-badge&logo=kali-linux" alt="Kali Linux">
  <img src="https://img.shields.io/badge/Speed-Ultra%20Fast-brightgreen.svg?style=for-the-badge" alt="Speed">
  <img src="https://img.shields.io/badge/License-GPL%203.0-orange.svg?style=for-the-badge" alt="License">
</p>

---

## 📖 نظرة عامة (Overview)

**scan3l** هي أداة متكاملة وضخمة مبنية بلغة **Python** مخصصة لصائدي الثغرات (Bug Bounty Hunters) ومهندسي الأمن السيبراني. صُممت الأداة لدمج أفضل تقنيات الاستطلاع (Recon) وفحص الثغرات تلقائياً وبأقصى سرعة ممكنة عبر تقنية الـ **Multi-threading** المتقدمة، مع توفير مظهر بصري فريد وجذاب على واجهة الأوامر الطرفية (CLI).

---

## ✨ المميزات الرئيسية (Key Features)

*   🔍 **Subdomain Discovery (كشف النطاقات الفرعية):** يجمع بين فحص الـ APIs العامة غير المحدودة (crt.sh, HackerTarget, AlienVault) ومحرك تخمين داخلي فائق السرعة عبر الـ DNS.
*   🌐 **HTTP Probing (فحص العناوين النشطة):** يحدد بسرعة البروتوكولات الحية (HTTP/HTTPS)، ويقوم بجلب عناوين الصفحات (HTML Titles) ومعلومات خوادم الويب (Web Servers).
*   🔌 **Port Scanning (فحص المنافذ):** محرك فحص منافذ داخلي ذو كفاءة عالية يفحص أهم المنافذ الشائعة للخدمات المكتشفة.
*   📂 **Directory Fuzzing (تخمين المجلدات الحساسة):** فاحص مدمج يبحث عن الملفات الخطيرة والمتروكة (مثل ملفات `.env` و `.git/config` و ملفات النسخ الاحتياطي وقواعد البيانات الحساسة).
*   📦 **Wayback URL Gathering (استخراج روابط الأرشيف):** جمع فوري للروابط المؤرشفة واستخراج الروابط البرمجية التي تحتوي على متغيرات (Parameters) لتسهيل عمليات الفحص اللاحقة.
*   🛡️ **Vulnerability Assessment (فحص الثغرات التلقائي):** فحص ذكي وخالٍ من التعقيد يكشف عن:
    *   **Subdomain Takeover** (استباق الاستيلاء على النطاقات عبر مطابقة بصمات الخدمات السحابية).
    *   **CORS Misconfigurations** (ثغرات مشاركة الموارد الخارجية الحساسة).
    *   **Open Redirects** (التوجيه المفتوح والثغرات الرابطة).
    *   **Sensitive Data Leaks** (تسريبات المفاتيح البرمجية وقواعد البيانات).
*   🛠️ **Auto-Dependency Setup:** تثبيت فوري تلقائي لجميع أدوات كالي لينكس المساعدة الشهيرة بنقرة واحدة.

---

## 🖥️ الواجهة البصرية للأداة (UI Preview)

```text
                                      _ 
 ___  ___  __ _ _ __   _________  _ _| |
/ __|/ __|/ _` | '_ \ /__   __  || | | |
\__ \ (__| (_| | | | |   / / / / | | | |
|___/\___|\__,_|_| |_|  /_/ /_/  |_|_|_|
                                       
        Ultimate Automated Bug Bounty Framework
              [ Version 1.0.0 - Fast & Precise ]

[*] Checking for recommended system-level Kali tools...
[+] Installed tools found: nmap, dirsearch
[!] Missing recommended tools: subfinder, httpx, nuclei
[+] Don't worry! scan3l will run its ultra-fast native Python engines.

[=] Starting Subdomain Discovery on: target.com
[+] Retrieved 45 subdomains from crt.sh
[+] Retrieved 12 subdomains from HackerTarget
[+] DNS Brute-forcing added 8 resolved subdomains.
[+] Found a total of 65 unique subdomains.
```

---

## 🚀 التثبيت والتشغيل (Installation & Quick Start)

### 1. تحميل الأداة وتجهيز الصلاحيات
```bash
git clone https://github.com/yourusername/scan3l.git
cd scan3l
chmod +x scan3l.py
```

### 2. تثبيت جميع أدوات كالي المساعدة تلقائياً (موصى به)
```bash
sudo python3 scan3l.py --install-deps
```

### 3. تشغيل فحص شامل سريع
```bash
python3 scan3l.py -t example.com --threads 100
```

---

## ⚙️ الخيارات والتحكم (Usage & Arguments)

| الأمر | الوصف | الإعداد الافتراضي |
| :--- | :--- | :--- |
| `-t, --target` | النطاق أو الموقع المستهدف وفحصه (مثال: `target.com`) | **مطلوب** |
| `-w, --wordlist` | ملف مخصص للتخمين العشوائي للنطاقات الفرعية | المدمج بالأداة |
| `-o, --output` | مجلد مخصص لحفظ النتائج فيه | `results_<target_name>` |
| `--threads` | عدد الخيوط لتسريع عمليات الفحص والطلبات بالتوازي | `50` |
| `--install-deps`| تثبيت تلقائي لكافة أدوات كالي لينكس الموصى بها | `False` |

---

## 📁 هيكلية مجلد النتائج (Output Structure)

عند انتهاء الفحص بنجاح، ستجد مخرجات منظمة في المجلد الخاص بالهدف بالشكل التالي:

```text
results_example_com/
├── subdomains.txt          # قائمة بجميع النطاقات الفرعية المكتشفة
├── alive_subdomains.txt    # النطاقات النشطة فقط التي تقبل اتصالات HTTP
├── ports.txt               # تقرير المنافذ المفتوحة لكل عنوان
├── urls.txt                # جميع روابط الأرشيف المجمعة
├── directories.txt         # المجلدات والملفات الحساسة التي تم العثور عليها
├── vulnerabilities.txt     # تقرير الثغرات الأمنية المكتشفة بالتفصيل
└── scan_report.json        # التقرير الشامل بصيغة JSON لمعالجته خارجياً
```

---

## ⚠️ إخلاء المسؤولية (Disclaimer)

هذه الأداة مخصصة **للأغراض التعليمية واختبار الاختراق الأخلاقي المصرح به فقط**. لا يتحمل المطور أي مسؤولية عن أي إساءة استخدام أو أضرار ناتجة عن استخدام الأداة ضد أهداف دون الحصول على إذن كتابي رسمي مسبق.
