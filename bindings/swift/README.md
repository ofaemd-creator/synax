# SYNAX Native Swift & Xcode Entegrasyon Kılavuzu

Bu dizin, **SYNAX Nöro-Sembolik Derleyici ve LLM Asistanı**'nın Apple platformlarına (macOS, iOS, iPadOS) ve Xcode geliştirme ortamına tam yerel (native) entegrasyonunu sağlar.

---

## 🏗️ İki Temel Entegrasyon Yolu

### 1. Sıfır Bağımlılık & Donanım Hızlandırmalı C-ABI (Sensör & Monitörizasyon İçin)
SYNAX `.sx` dosyalarını doğrudan Apple Silicon donanımına kilitli bağımsız C11 koduna derleyip Xcode projenize dahil edebilirsiniz.

```bash
# Terminalden C-Header ve C dosyasını üretin:
synax build stdlib/biomed/hemodynamic_triage.sx --emit-c-header -o xcode_export/
```

**Xcode'a Ekleme:**
1. Üretilen `hemodynamic_triage.h` ve `hemodynamic_triage.c` dosyalarını Xcode projenizin dosya gezginine sürükleyip bırakın.
2. Projenizin `Bridging-Header.h` dosyasına ekleyin:
   ```c
   #include "hemodynamic_triage.h"
   ```
3. Swift içerisinden sıfır gecikmeyle (Zero-Overhead) çağırın:
   ```swift
   import Foundation

   func computeTriage(hr: [Float], sbp: [Float]) -> [Float] {
       var result = [Float](repeating: 0.0, count: hr.count)
       synax_hemodynamic_triage(hr, sbp, &result, hr.count)
       return result
   }
   ```

---

### 2. Native SwiftUI Chat & LLM Asistanı (`SynaxChatView.swift`)
Xcode uygulamanızın içine doğrudan yapay zeka destekli kodlama ve klinik formül analiz ekranı eklemek için:

#### Adım A: Swift Dosyalarını Xcode Projenize Dahil Edin
* `bindings/swift/Sources/SynaxBridge/SynaxBridge.swift`
* `bindings/swift/Sources/SynaxBridge/SynaxChatView.swift`
dosyalarını projenize ekleyin (veya `bindings/swift` dizinini **Local Swift Package** olarak bağlayın).

#### Adım B: SwiftUI Görünümünde Kullanın
```swift
import SwiftUI
import SynaxBridge

struct ContentView: View {
    var body: some View {
        SynaxChatView()
            .frame(minWidth: 500, minHeight: 650)
    }
}
```

#### Adım C: macOS App Sandbox Yetkisi (Gerekliyse)
Eğer uygulamanız macOS App Sandbox açık olarak derleniyorsa ve `synax_chat.py` komut satırı sürecini çağıracaksa:
* `YourApp.entitlements` dosyasında `App Sandbox` değerini `NO` yapabilir veya XPC/Process izinlerini etkinleştirebilirsiniz.

---

## ⚡ Swift Bridge API Örnekleri

```swift
let bridge = SynaxBridge()

// 1. Serbest Klinik / Kodlama İstemi Gönderme
let res = try await bridge.sendMessage("Serebral perfüzyon için koruyucu kernel yaz")
print(res.text)
if let code = res.code {
    print("Üretilen Kod:\n\(code)")
}

// 2. Otonom Beceri Öğretme (Autopoiesis)
let skill = try await bridge.teachSkill(
    concept: "serebral_oksijen",
    formula: "clamp(spo2 * 0.7 + map * 0.3, 0.0, 100.0)"
)
print("Öğrenilen Nesil: #\(skill.generation), Bütünlük: \(skill.sha256)")

// 3. TYCON 4-Varyant Evrim Arenasını Çalıştırma
let report = try await bridge.evolveKernel(code: myKernelSxCode)
print(report)
```
