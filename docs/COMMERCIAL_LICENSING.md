# SYNAX Open-Core & Commercial Licensing Architecture

**Target Stage:** TRL-4 (Validated in Laboratory) $\to$ TRL-7/8 (System Prototype Validated in Operational Clinical Environment)  
**Author:** Dr. Ömer Faruk Aydın, MD (dev@synaxcode.com)  
**Entity:** SYNAX Technologies  

---

## 1. Dual-Licensing Strategic Overview

SYNAX employs a high-leverage **Open-Core / Dual-Licensing Model**, engineered to achieve maximum global academic and developer adoption while capturing high enterprise value in safety-critical medical technology (MedTech) and mission-critical edge defense.

```
+-----------------------------------------------------------------------------+
|                          COMMERCIAL ENTERPRISE TIER                         |
|   - IMMUNE Compliance Suite (Automated IEC 62304 Class C & FDA 510(k) Logs) |
|   - MYELIN Cryptographic Silicon Fingerprint & Tamper-Proof Locking        |
|   - Multi-Node Heterogeneous NPU / DSP / ARM Co-Evolution (TYCON)          |
|   - Per-Device OEM Royalty / Annual High-Assurance SDK Subscription         |
+-----------------------------------------------------------------------------+
                                      ▲
                                      │ Extends & Monetizes
                                      │
+-----------------------------------------------------------------------------+
|                            OPEN-CORE COMMUNITY TIER                         |
|                         (Apache License 2.0 - Permissive)                    |
|   - Core SYNAX Language Compiler & Frontend (SYNAPSE)                       |
|   - Standard SIMD Code Lowering (AXON ARM64 NEON / AVX2 / C11)             |
|   - Dual-Reference Verification Gate (clang -O0 bit parity)                 |
|   - Standard Library Kernels & Python Bridge (@synax.kernel FFI)            |
|   - Developer CLI & VS Code Extension                                       |
+-----------------------------------------------------------------------------+
```

---

## 2. Licensing Matrix

| Capability / Module | Open-Core (Apache 2.0) | Enterprise Commercial License |
|---|:---:|:---:|
| **Language Frontend (`.sx` parser & AST)** | ✅ Included | ✅ Included |
| **Python SDK (`@synax.kernel`)** | ✅ Included | ✅ Included |
| **C/C++ Header Emitter (`--emit-c-header`)** | ✅ Included | ✅ Included |
| **SIMD Code Generators (NEON, AVX2, C11)** | ✅ Included | ✅ Included |
| **Basic Zero-Drift Verification Gate** | ✅ Included | ✅ Included |
| **Biomed & Defense StdLib Kernels** | ✅ Included | ✅ Included |
| **IEC 62304 Class C Regulatory Suite** | ❌ Community Only | ✅ Formal Audit Reports & FDA Dossier |
| **Hardware-Locked Cryptographic JIT** | ❌ Open Cache | ✅ Encrypted Silicon Fingerprint Locks |
| **Real-Time Heterogeneous NPU Offloading** | ❌ CPU Only | ✅ NPU, DSP & FPGA Accelerators |
| **OEM Per-Device Commercial Distribution** | Free for internal/dev | Royalty or Annual Fleet License |
| **Commercial Warranty & Indemnification** | None (AS-IS) | Full Enterprise SLA & Legal Shield |

---

## 3. Revenue Models & Monetization Streams

### 3.1 B2B OEM Licensing (Medical Device Manufacturers)
- **Target Customers:** Patient monitor manufacturers (e.g. Mindray, GE HealthCare, Philips, Draeger), ventilator and infusion pump vendors, implantable defibrillator engineers.
- **Model:** **Device Royalty + Annual SDK Maintenance Fee**.
  - Small volume (< 5,000 devices/year): \$15 - \$25 per active device.
  - High volume (> 50,000 devices/year): Tiered enterprise fleet royalty.
- **Value Proposition:** Reduces FDA 510(k) / EU MDR software verification costs by up to 70%, guarantees zero crash under catastrophic catheter detachment, and eliminates real-time pipeline branch jitter.

### 3.2 Enterprise Mission-Critical Defense & Edge SDK
- **Target Customers:** Unmanned aerial vehicles (UAV), radar/LiDAR telemetry systems, autonomous robotics operating under electronic jamming conditions.
- **Model:** **Annual Developer Seat License (\$12,000 / seat / year)** including custom accelerator target synthesis.

### 3.3 Regulated Cloud Verification Service
- **Model:** Cloud-based automated certification pipeline generating certified IEC 62304 / ISO 26262 audit packages on pull request (`synax verify --compliance iec62304`).

---

## 4. IP Invariant & Protection Strategy

1. **Patents as Primary Moat:** All core compiler methods relating to non-branching SIMD fault healing (`IMMUNE`) and cryptographic silicon fingerprint locking (`MYELIN`) are protected under international PCT patent applications.
2. **Permissive Open-Core as Distribution Vector:** Apache 2.0 license encourages medical researchers and universities to benchmark and publish using SYNAX without legal friction.
3. **Enterprise Gating:** Commercial exploitation in closed-source medical device firmware requiring formal regulatory compliance documentation requires the Enterprise License.
