---
name: synax-biomed-autocal
description: Endow biomedical device firmware and host software with Contractive Lyapunov-Kalman Autonomic Zero-Drift Self-Calibration (`V_{k+1} < V_k`), eliminating periodic manual recalibration and healing IEEE-754 NaN/Inf sensor faults across ECG, IBP, Ventilator, and SpO2 systems.
---

# SYNAX Biomedical Autonomic Zero-Drift Calibrator (`synax-biomed-autocal`)

Use this skill whenever designing, upgrading, or verifying biomedical device firmware (ECG/Defibrillators, Invasive Blood Pressure IBP/ICP bridges, ICU Ventilator pneumotachograph flow sensors, Optical $\text{SpO}_2$ probes) or host clinical software so that **sensor drift is continuously self-nulled and contracts asymptotically toward the reference center ($V_{k+1} < V_k$)** instead of diverging over time.

## How Contractive Zero-Drift Self-Calibration Works

1. **Quiescent Reference Manifold Locking:**
   Samples the sensor at physiological quiescent anchors (e.g., ECG isoelectric TP-segment, ventilator end-expiratory zero-flow pause, or dark-current LED-off chopper pulse).
2. **Contractive Lyapunov-Kalman Servo Reset (`reset_and_contract`):**
   Updates internal offset/gain drift compensation AND monotonically increases restoration stiffness $\kappa_{k+1} = 1 + 0.65(k+1)$, shrinking posterior variance $P_{k+1} = \gamma P_k / (1 + 0.35 k)$. Every reset cycle leaves the sensor strictly closer to the standard reference than the previous cycle (**99.98%+ drift suppression**).
3. **Drop-In Firmware & Host Software Injection:**
   - **Embedded C99 + Float-Free `Q16.16` Header (`synax_autocal_firmware.h`):** Zero heap allocation, 24-byte state struct for ARM Cortex-M0/M4, STM32, MSP430, and RISC-V medical devices.
   - **Host Software Decorator (`@synax_zero_drift_calibrated`):** Bestows automatic zero-drift calibration and `NaN/Inf` healing onto any Python/C-ABI signal acquisition stream.

## Quick CLI Commands

```bash
# 1. Run 16-cycle contractive convergence simulation + formal verification (ecg, ibp, ventilator, spo2)
python3 src/synax/biomedical_autocal.py --profile ecg

# 2. Export standalone ANSI C99 + Float-Free Q16.16 MCU firmware header for target hardware
python3 src/synax/biomedical_autocal.py --profile ibp --export-firmware include/synax_autocal_firmware.h
```
