# SYNAX (`.sx`) Formal Language Specification

**Specification Version:** `0.5` (covering `synax 0.1`, `synax 0.5`, and Declarative `.sx` Compatibility)  
**Formal Grammar:** `spec/synax.ebnf`  
**Core Invariant:** *Optimization must never change semantics.*

---

## 1. Executive Overview / Türkçe Genel Bakış

### English Overview
**SYNAX (`.sx`)** is a domain-specific, safety-critical numerical kernel programming language engineered for deterministic signal processing, biomedical waveform research, and high-throughput tensor elementwise computation across heterogeneous silicon (C11 Scalar, ARM64 NEON SIMD, x86 AVX2, Apple GCD Multicore, and MCU fixed-point targets).

Unlike general-purpose languages where floating-point edge cases (`NaN`, `+Inf`, `-Inf`, `-0.0`, subnormals) are left to compiler flags or undefined library behavior, SYNAX elevates **IEEE-754 floating-point semantics** and **signal fault-handling policies (`SafetyPolicy`)** into first-class, statically checked, cryptographically locked language constructs. Every compiler optimization candidate must pass differential verification against dual independent references before execution or caching.

### Türkçe Genel Bakış (Bilingual Summary)
**SYNAX (`.sx`)**, biyomedikal sinyal işleme, sensör füzyonu ve yüksek verimli vektör/tensör hesaplamaları için tasarlanmış deterministik, güvenlik-öncelikli bir sayısal çekirdek (kernel) programlama dilidir. SYNAX'ın temel mühendislik değişmezi nettir:

> **"Optimizasyon semantiği asla değiştirmemelidir"** (*Optimization must never change semantics*).

SYNAX iki tamamlayıcı sözdizimi katmanını tek bir kanonik Ara Temsilde (`SynaxIR`) birleştirir:
1. **Yapısal Çekirdek Sözdizimi (`synax 0.1` / `synax 0.5`)**: Statik tipli `kernel` bildirimleri, şekil değişmezleri (`require shape(a) == shape(b)`), açık bağışıklık kalkanı politikaları (`safety { ... }`), değiştirilemez yerel bağlamalar (`let`), dönüş ifadeleri (`return`) ve donanım hedefleri (`optimize`, `target`).
2. **Bildirimsel Niyet Uyumluluk Katmanı (`niyet:` / `kural:` / `hedef:` / `formül:`)**: SYNAX v0.2–v0.4 betikleriyle %100 geriye dönük uyumluluk sağlayan sembolik ve doğal dil tabanlı bildirim biçimi.

Her `.sx` programı derleme aşamasında statik tip denetiminden (`TypeChecker`) geçer, IEEE-754 ikili32 (`binary32`) semantiğine sadık kalarak indirgenir ve `.sx.lock` kriptografik semantik kilit dosyasıyla 32 altın test vektörü üzerinden SHA-256 bütünlük koruması altına alınır.

---

## 2. Lexical Structure

### 2.1 Source Encoding & Spans
- All `.sx` source files are encoded in **UTF-8**.
- Every token produced by the SYNAX lexer carries a 1-indexed `SourceSpan(line, col, end_line, end_col)` enabling exact line/column diagnostics with caret (`^`) highlighting.
- Whitespace (`' '`, `'\t'`, `'\r'`, `'\n'`) separates tokens and carries no syntactic significance in structured `.sx` modules.

### 2.2 Comments
SYNAX supports two single-line comment forms outside string literals:
- C-style line comments: `// ...` up to end of line (canonical form in structured `.sx`).
- Hash line comments: `# ...` up to end of line (commonly used in declarative `.sx` headers).

### 2.3 Keywords & Contextual Identifiers
- **Reserved structural keywords**: `synax`, `kernel`, `intent`, `require`, `safety`, `let`, `return`, `optimize`, `target`, `true`, `false`.
- **Type identifiers**: `f32`, `f64`, `i32`, `bool`, `tensor`.
- **Policy & directive identifiers**: `shape`, `nonfinite`, `range_check`, `input_bound`, `heal`, `preserve`, `reject`, `zero_output`, `clamp`, `abs_max`, `latency`, `throughput`, `size`, `auto`, `neon`, `avx2`, `llvm`, `scalar`, `multicore`.
- **Identifiers**: Match `[A-Za-z_][A-Za-z0-9_]*`. Note that `bias` is a reserved implicit scalar channel constant (`f32`, default `0.25`) when not shadowed by an explicit parameter.

### 2.4 Literals
- **Integer literals**: Decimal sequences `[0-9]+` (e.g., `0`, `2`, `1024`). Used for fixed tensor dimensions (`tensor<f32, 1024>`), integer exponents (`x^2`, `x^3`), and `i32` constants.
- **Floating-point literals**: Decimal and scientific notation `[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?` (with either a decimal point, an exponent part, or both; e.g., `0.0`, `3.1415927`, `1e-6`, `3.4e38`, `1.5E+3`). Evaluated in `f32` kernels by rounding to the nearest IEEE-754 binary32 value (round-ties-to-even).
- **Boolean literals**: `true` and `false`.
- **String literals**: Double-quoted UTF-8 text `"..."` supporting escape sequences `\"`, `\\`, `\n`, `\r`, and `\t`. Unterminated string literals or raw newlines inside quotes raise `SynaxLexError`.

### 2.5 Operators & Punctuation
- **Arithmetic**: `+`, `-`, `*`, `/`, `^`, `**`
- **Relational / Binding / Return**: `==`, `=`, `->`
- **Delimiters**: `(`, `)`, `{`, `}`, `<`, `>`, `:`, `,`, `;`

---

## 3. Program Structure

### 3.1 Structured Kernel Modules (`synax 0.1` / `synax 0.5`)
A structured `.sx` file begins with an optional version declaration (`synax 0.1` or `synax 0.5`) followed by a `kernel` definition:

```sx
synax 0.1

kernel coronary_perfusion_pressure(
  dbp: tensor<f32>,
  cvp: tensor<f32>
) -> tensor<f32> {
  intent "Compute protected coronary perfusion pressure (CPP = DBP - CVP)."

  require shape(dbp) == shape(cvp)

  safety {
    nonfinite = heal(0.0)
    range_check = clamp(-50.0, 300.0)
  }

  let cpp = dbp - cvp
  return cpp

  optimize latency
  target auto
}
```

A kernel body may contain:
- At most one `intent "<description>"` metadata declaration.
- Zero or more `require <shape_expr> == <shape_expr>` shape assertions.
- At most one `safety { ... }` block defining input/output signal immunity rules.
- Zero or more immutable `let <ident> [: <type>] = <expr>` bindings evaluated strictly top-to-bottom.
- Exactly one `return <expr>` statement defining the elementwise output expression.
- At most one `optimize (latency | throughput | size)` compiler goal directive (default: `latency`).
- At most one `target (auto | neon | avx2 | llvm | scalar | multicore)` backend hint (default: `auto`).

### 3.2 Declarative Compatibility Modules (`niyet:` / `kural:` / `hedef:` / `formül:`)
For backward compatibility with SYNAX v0.2/v0.4 pipelines, files without a `synax <ver>` or `kernel` header are parsed as declarative intent modules supporting key-value directives (`niyet:`/`intent:`, `kural:`/`rule:`, `hedef:`/`target:`, `formül:`/`formula:`/`expr:`) and lowered into the identical `SynaxIR` representation.

---

## 4. Static Type System & Shape Invariants

### 4.1 Supported Types
| Type Syntax | Category | Description |
| :--- | :--- | :--- |
| `f32` | Scalar | IEEE-754 binary32 single-precision floating-point (primary native compute type) |
| `f64` | Scalar | IEEE-754 binary64 double-precision floating-point |
| `i32` | Scalar | Signed 32-bit two's-complement integer |
| `bool` | Scalar | Logical boolean (`true` / `false`) |
| `tensor<T>` | Dynamic 1D Tensor | Contiguous 1D buffer of scalar element type `T` (`T` in `{f32, f64, i32, bool}`) |
| `tensor<T, N>` | Fixed 1D Tensor | Contiguous 1D buffer of scalar element type `T` and static positive length `N > 0` |

### 4.2 Type Checking & Broadcasting Rules
`TypeChecker.check(kernel_decl)` enforces the following static rules prior to lowering:
1. **Parameter Uniqueness & Validity**: All parameter names must be distinct and annotated with valid SYNAX types.
2. **Lexical `let` Scoping**:
   - **No use-before-definition**: An expression may reference only kernel parameters, previously defined `let` bindings, or the implicit `bias` (`f32`) constant.
   - **No shadowing**: Re-binding an existing `let` identifier or shadowing a parameter name within the same kernel block raises `SynaxTypeError`.
   - **Optional type annotations**: In `let x: T = expr`, the inferred type of `expr` must be compatible with `T`.
3. **Elementwise Broadcasting**:
   - Arithmetic operators (`+`, `-`, `*`, `/`) require numeric operands (`bool` is rejected) of matching element precision (`f32` with `f32`, `f64` with `f64`, `i32` with `i32`; untyped numeric literals coerce to the peer float type when unambiguous).
   - Combining `tensor<T>` with scalar `T` broadcasts the scalar across all tensor lanes, yielding `tensor<T>`.
   - Combining `tensor<T, N>` with `tensor<T, M>` requires `N == M`; mismatched static lengths (`N != M`) or mixing `tensor<T, N>` with dynamic `tensor<T>` raises `SynaxTypeError`.
4. **Exponentiation Restriction**: `base ^ exp` (or `base ** exp`) requires a numeric `base` and a constant literal exponent equal to `2` (`POW2`) or `3` (`POW3`). All other exponents raise `SynaxTypeError`.
5. **Builtin Function Signatures & Static Range Checks**:
   - **Unary (`1` arg)**: `sqrt`, `square`, `pow2`, `cube`, `pow3`, `abs`, `fabs`, `sin`, `cos`, `exp`, `log`, `ln`, `sigmoid`, `tanh`, `relu`. Passing `!= 1` argument raises `SynaxTypeError`.
   - **Binary (`2` args)**: `min(x, y)`, `max(x, y)`. Passing `!= 2` arguments raises `SynaxTypeError`.
   - **Ternary (`3` args)**: `clamp(x, lo, hi)`. Passing `!= 3` arguments raises `SynaxTypeError`. Furthermore, if `lo` and `hi` are constant numeric literals (including signed literals such as `-5.0`) and `lo > hi`, `TypeChecker` raises `SynaxTypeError` at compile time.
6. **Return Compatibility**: The inferred type of `return <expr>` must match the declared `-> <return_type>` of the kernel (`tensor<f32>` cannot be returned from an `-> f32` kernel, nor vice versa).

### 4.3 Shape Invariants (`require`)
A `require shape(p0) == shape(p1)` declaration statically asserts that:
1. Both `p0` and `p1` are declared parameters of `kernel`. Referencing an undeclared variable or a `let` binding raises `SynaxTypeError`.
2. Both `p0` and `p1` have `tensor<...>` types. Referencing a scalar parameter (e.g., `k: f32`) inside `shape(k)` raises `SynaxTypeError`.
3. If both parameters have static lengths (`tensor<T, N>` and `tensor<U, M>`) or compare against a static dimension literal (`require shape(p0) == 1024`), mismatched static dimensions raise `SynaxTypeError`.

At runtime, compiled kernels receive buffer length `n` (`size_t n`). When `n == 0`, kernels are guaranteed to perform zero out-of-bounds reads or writes (verified via `1234.5f` sentinel buffers).

---

## 5. IEEE-754 Floating-Point Semantics & Why `-ffast-math` Is Forbidden

### 5.1 Strict `binary32` Semantics
Every node in a `f32` SYNAX AST operates under **IEEE-754-2019 binary32** round-ties-to-even arithmetic:
- **Division (`DIV`)**: `x / 0.0` yields `+Inf` or `-Inf` according to `copysign(1, x) * copysign(1, 0.0)`; `0.0 / 0.0` and `±Inf / ±Inf` yield quiet `NaN`; finite divided by `±Inf` yields signed `±0.0`.
- **Square Root & Logarithm (`SQRT`, `LOG`)**: Negative inputs (`x < 0.0`) yield `NaN`; `sqrt(-0.0) == -0.0`; `log(±0.0) == -Inf`.
- **Exponential & Sigmoid (`EXP`, `SIGMOID`)**: Overflow above `88.722839f` yields `+Inf`; underflow below `-103.97208f` flushes cleanly to `+0.0` without wrap-around; `sigmoid(-Inf) == +0.0`, `sigmoid(+Inf) == 1.0`, `sigmoid(NaN) == NaN`.
- **Signed-Zero & `NaN`-Exact Extremals (`MIN`, `MAX`, `RELU`, `CLAMP`)**:
  - If either operand to `min`, `max`, or `clamp` is `NaN`, the result is `NaN` (`relu(NaN) == NaN`).
  - `min(-0.0, +0.0) == -0.0` and `max(-0.0, +0.0) == +0.0`.
  - `clamp(x, lo, hi)` is defined identically to `min(max(x, lo), hi)`.

### 5.2 Why `-ffast-math` Is Strictly Forbidden
Compiler flags such as `-ffast-math` (and sub-flags `-ffinite-math-only`, `-funsafe-math-optimizations`, `-fassociative-math`, `-fno-signed-zeros`, `-freciprocal-math`) are **unconditionally prohibited** in all SYNAX compiler backends for four critical engineering reasons:

1. **Destruction of Safety Shields (`-ffinite-math-only`)**: Under `-ffinite-math-only`, C/LLVM optimizers assume `NaN` and `±Inf` can never exist at runtime and legally **delete `isnan(x)` and `isinf(x)` branches as dead code**. In biomedical monitoring (e.g., ECG/ABP electrode disconnection producing `NaN`/`Inf`), deleting those checks silently corrupts downstream patient-research waveforms and breaks `SafetyPolicy`.
2. **Invalid Algebraic Annihilation (`x * 0.0 -> 0.0`)**: In IEEE-754, `NaN * 0.0 == NaN` and `Inf * 0.0 == NaN`. `-ffast-math` rewrites `x * 0.0` to `0.0`, erasing `NaN` fault propagation. SYNAX's `ASTNode.simplify()` explicitly forbids `x * 0.0 -> 0.0` unless `SafetyPolicy.guarantees_finite_inputs()` (`heal_inputs` or `zero_output`) statically proves all inputs are finite prior to evaluation.
3. **Non-Associative Reordering (`-fassociative-math`)**: Floating-point addition and multiplication are non-associative; `(a + b) - a` cannot be rewritten to `b` when `a` overflows to `Inf` or absorbs low-order mantissa bits.
4. **Signed-Zero & Reciprocal Drift (`-fno-signed-zeros`, `-freciprocal-math`)**: Approximate SIMD reciprocals (`vrecpeq_f32`) alter `1.0f / (-0.0f)` sign bits and introduce multi-ULP errors that violate differential equivalence. Instead, SYNAX uses exact hardware IEEE-754 instructions (`vdivq_f32`, `vsqrtq_f32`) and bitwise `uint32_t` exponent/mantissa masks (`(bits & 0x7FFFFFFFu) <= bound_u32`).

---

## 6. Operational Semantics of `SafetyPolicy`

A kernel's `safety { ... }` block configures a `SafetyPolicy(nonfinite_mode, heal_value, input_abs_bound, output_clamp)`:

- `input_bound = abs_max(B)` (optional, statically requires `B > 0`): Defines channel validity predicate:
  $$\text{valid}(v) \iff \text{isfinite}(v) \land (|v| \le B)$$
  If `input_bound` is omitted, $\text{valid}(v) \iff \text{isfinite}(v)$ (implemented in hardware via `(bits & 0x7FFFFFFFu) <= 0x7F7FFFFFu`).
- `range_check = clamp(lo, hi)` (optional, statically requires `lo <= hi`): Applies post-evaluation output clamping $\text{clamp}(y, \text{lo}, \text{hi})$.

For each sample index $i \in \{0, \dots, n-1\}$ with raw binary32 inputs $(a_i, b_i)$, let $\text{bad}_a = \neg\text{valid}(a_i)$ and $\text{bad}_b = \neg\text{valid}(b_i)$. The four `nonfinite_mode` policies execute as follows:

### 6.1 `preserve` (`nonfinite = preserve`, default)
- **Semantics**: Pure IEEE-754 propagation; inputs are untouched and anomaly counter increment is $\Delta\text{healed}_i = 0$.
- **Transition**:
  $$y_i = f(a_i, b_i), \quad \text{out}_i = \text{clamp}_{\text{opt}}(y_i), \quad \Delta\text{healed}_i = 0$$

### 6.2 `heal_inputs` (`nonfinite = heal(h)`)
- **Semantics**: Pre-evaluation channel sanitization ("Ranvier immune shield"). Each invalid input channel is replaced with $h = \text{f32}(\text{heal\_value})$ *before* evaluating expression $f$, and counted individually ($\Delta\text{healed}_i \in \{0, 1, 2\}$).
- **Transition**:
  $$a'_i = \begin{cases} h & \text{if } \text{bad}_a \\ a_i & \text{otherwise} \end{cases}, \quad b'_i = \begin{cases} h & \text{if } \text{bad}_b \\ b_i & \text{otherwise} \end{cases}$$
  $$\text{out}_i = \text{clamp}_{\text{opt}}(f(a'_i, b'_i)), \quad \Delta\text{healed}_i = [\text{bad}_a] + [\text{bad}_b]$$

### 6.3 `zero_output` (`nonfinite = zero_output`)
- **Semantics**: Short-circuiting output substitution. If either input channel is invalid, expression $f$ is bypassed for sample $i$ and output defaults directly to $h = 0.0\text{f}$ (clamped if `output_clamp` is active), while counting each invalid input channel.
- **Transition**:
  $$\text{out}_i = \begin{cases} \text{clamp}_{\text{opt}}(h) & \text{if } \text{bad}_a \lor \text{bad}_b \\ \text{clamp}_{\text{opt}}(f(a_i, b_i)) & \text{otherwise} \end{cases}, \quad \Delta\text{healed}_i = [\text{bad}_a] + [\text{bad}_b]$$

### 6.4 `reject` (`nonfinite = reject`)
- **Semantics**: Strict fault-signaling mode. Any invalid input channel increments `healed` and forces `out[i] = NaN` (bypassing `output_clamp` on faulted samples so `NaN` is never masked into a finite bound), enabling checked runtime callers to raise a deterministic safety rejection whenever `healed > 0`.
- **Transition**:
  $$\text{out}_i = \begin{cases} \text{NaN} & \text{if } \text{bad}_a \lor \text{bad}_b \\ \text{clamp}_{\text{opt}}(f(a_i, b_i)) & \text{otherwise} \end{cases}, \quad \Delta\text{healed}_i = [\text{bad}_a] + [\text{bad}_b]$$

---

## 7. Evaluation Determinism & Multi-Target Equivalence

Every compiled SYNAX kernel exposes two C11 ABI entrypoints:
```c
void synax_kernel(const float* a, const float* b, float* out, size_t n);
void synax_kernel_tracked(const float* a, const float* b, float* out, size_t n, size_t* out_healed);
```

Before any SIMD (`v2_neon_simd`, `v3_neon_4acc_prefetch`) or multicore (`v4_gcd_multicore_neon`) candidate is accepted into the Myelin cache:
1. **Dual-Reference Gate**: The pure-Python IEEE-754 binary32 evaluator (`SynaxIR.eval_element_f32`) must agree with the unoptimized C11 `-O0` scalar reference across adversarial edge-case suites.
2. **19-Suite Differential Elimination**: Every candidate must match the reference across lengths $n \in \{0, 1, 3, 4, 5, 7, 8, 15, 16, 17, 31, 63, 1023, 4097, 100003\}$ (exercising vector loop bodies and scalar tail cleanup) and the $12 \times 12 = 144$ Cartesian product of IEEE-754 special values with:
   - Exact `NaN` index parity,
   - Exact `+Inf` / `-Inf` index and sign parity,
   - Relative numerical tolerance $\le 10^{-5}$ on finite outputs,
   - Exact `out_healed` anomaly counter equality.

---

## 8. Cryptographic Semantic Lock (`.sx.lock`)

To guarantee zero semantic drift across compiler upgrades, code formatting, refactoring, or deployment environments, SYNAX provides a cryptographic **Semantic Lockfile** (`<program>.sx.lock`) managed by `src/synax/semantic_lock.py`:

1. **Canonical IR Digest (`ir_hash`)**: 12-character hexadecimal prefix of the SHA-256 digest over canonical JSON (`version`, `bias_default`, `safety`, and lowered `expr` AST). Formatting a file via `format_sx` is strictly `ir_hash`-preserving:
   ```text
   format_sx(format_sx(src)) == format_sx(src)
   parse_sx(format_sx(src)).ir_hash == parse_sx(src).ir_hash
   ```
2. **32 Deterministic Golden Vectors**: Evaluates 32 curated `(a, b)` pairs spanning clean normals, `+0.0`, `-0.0`, quiet `NaN`, `+Inf`, `-Inf`, subnormals (`1e-40`), near-`FLT_MAX` (`3.4e38`), and threshold spikes (`-1000.0`, `2500.0`). Inputs and expected outputs are serialized in exact lossless IEEE-754 hexadecimal notation (`float.hex()`, `"nan"`, `"inf"`, `"-inf"`) alongside per-vector and cumulative `healed` counts.
3. **Tamper-Evident Integrity (`_integrity_sha256`)**: The entire lock payload is signed with `SynaxSecurityGuard.compute_canonical_sha256`. `verify_lockfile(sx_path, lock_path, kernel)` verifies:
   - Cryptographic SHA-256 lockfile integrity (rejecting unsigned or modified lockfiles),
   - Zero `ir_hash` drift between `.sx` source and `.sx.lock`,
   - Bit-exact reproducibility of all 32 golden vectors against `ir.eval_element_f32`,
   - Optional native binary verification against a compiled `LoadedKernel` shared library.
