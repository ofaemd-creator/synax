# 🔒 SYNAX Agent Office & SYNAX-OMNI Ekosistemi Güvenlik Politikası (Security Policy)

SYNAX (`@ofaemd-creator`) açık kaynak ekosistemine, kullanıcı veri mahremiyetine ve tıbbi/biyomedikal yazılım güvenliğine en üst düzeyde önem verir. Bu politika belgesi; güvenlik açığı bildirme sürecini, desteklenen sürümleri ve platformumuzun temel güvenlik mimarisini tanımlar.

---

## 🛡️ Desteklenen Sürümler (Supported Versions)

SYNAX Agent Office ve bağlı çekirdek modülleri düzenli güvenlik güncellemeleri alır:

| Sürüm (Version) | Destek Durumu (Support Status) | Güvenlik Yamaları (Security Fixes) |
|---|---|---|
| **v6.0.x (SYNAX-OMNI)** | :white_check_mark: Tam Destekleniyor (Aktif) | Canlı & Öncelikli |
| **v5.0.x** | :white_check_mark: Destekleniyor | Kritik Hatalar |
| **v4.x / v3.x** | :warning: Sınırlı Destek | Sadece Güvenlik Açığı Tespiti |
| **< v3.0** | :x: Kullanım Dışı | Desteklenmiyor (Lütfen güncelleyin) |

---

## 🔐 Temel Güvenlik ve Gizlilik Mimarisi (Security Architecture)

1. **Sıfır-Bilgi Anahtar Güvenliği (Zero-Trust BYOK - Bring Your Own Key):**
   * Kullanıcıların girdiği harici API anahtarları (`Groq`, `Anthropic Claude`, `OpenAI`, `Gemini`, `OpenRouter`) **asla uzak sunuculara veya GitHub'a iletilmez ve kaydedilmez**.
   * Tarayıcı üzerinde çalışan versiyonlarda anahtarlar yalnızca istemci tarafında (`localStorage`) tutulur.
   * Masaüstü uygulamasında (`SYNAX Studio.app`) anahtarlar yerel kullanıcı dizininde `~/.synax/user_accounts.json` dosyasında `chmod 600` (sadece yerel kullanıcı okuyabilir) yetkisiyle saklanır.

2. **İzole Python Code Interpreter Sandbox:**
   * Kullanıcı veya ajanlar tarafından üretilen Python hesaplama scriptleri yerel işletim sisteminde sınırlandırılmış yetkilerle ve 5 saniyelik zaman aşımı (subprocess timeout) kontrolü altında çalıştırılır.

3. **IEEE-754 0-ULP & Lyapunov Sıfır-Sapma Güvenliği:**
   * Biyomedikal sinyal işleme çekirdeklerinde (`.sx`) oluşabilecek beklenmedik donanım taşmaları, `NaN` ve `Inf` değerleri donanımsal `heal(0.0)` emniyet kalkanı ile anında bertaraf edilir.

4. **Kriptografik Ajan Hafıza Kasası (SHA-256 Context Vault):**
   * Ajanlar arası bağlam devri sırasında üretilen kapsüller SHA-256 özetleri ile mühürlenir; veri manipülasyonuna veya üçüncü taraf müdahalesine kapalıdır.

---

## 🚨 Güvenlik Açığı Bildirimi (Reporting a Vulnerability)

SYNAX depolarında potansiyel bir güvenlik açığı veya veri güvenliği riski tespit ederseniz, lütfen bunu **herkese açık bir GitHub Issue (Hata Kaydı) olarak bildirmeyiniz**.

Bunun yerine aşağıdaki güvenli kanalları kullanınız:

1. **GitHub Private Vulnerability Reporting (Önerilen):**
   * Depo sayfasında [Security > Advisories > Report a vulnerability](https://github.com/ofaemd-creator/synax-agent-office/security/advisories/new) sekmesine giderek gizli bir rapor oluşturabilirsiniz.
2. **Doğrudan İletişim & Güvenlik Masası:**
   * E-posta: **`dev@synaxcode.com`**
   * Konu Başlığı: `[SECURITY AUDIT] SYNAX Agent Office - <Bileşen Adı>`
   * Raporunuzda lütfen:
     * Açığın tespit edildiği bileşen / dosya yolu,
     * Yeniden üretme adımları (PoC - Proof of Concept),
     * Olası etki değerlendirmesini belirtiniz.

### Yanıt Süresi Taahhüdümüz:
* **İlk Yanıt:** 24 saat içerisinde rapor onaylanır ve inceleme başlatılır.
* **Geçici Çözüm / Düzeltme:** Kritik açıklar için en geç 72 saat içerisinde yama yayınlanır.
* **Sorumlu İfşa (Responsible Disclosure):** Açık kapatılıp yeni sürüm yayınlanana kadar detaylar gizli tutulur. Katkıda bulunan araştırmacılara sürüm notlarında resmi teşekkür edilir.

---

## 🏥 Tıbbi & Biyomedikal Sorumluluk Reddi (Clinical Disclaimer)

SYNAX ve bağlı tüm biyomedikal algoritmalar (`Lyapunov-Kalman autocal`, `PRISMA meta-analysis`, `0-ULP verifier`), deneysel ve akademik araştırmalara yönelik açık kaynaklı mühendislik araçlarıdır. Ürünlerin klinik tanı ve acil tıp kararlarında kullanımı hekim ve sağlık personeli sorumluluğundadır; CE/FDA sınıflandırması gerektiren tıbbi cihaz yazılımlarında doğrudan birincil karar verici olarak kullanılamaz.
