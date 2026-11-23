#!/usr/bin/env python3
"""Applies the v7.2 Zero-Trust Founder barrier to sites/api.php and sites/chat_index.html."""
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
API = BASE / "sites" / "api.php"
HTML = BASE / "sites" / "chat_index.html"

if "ZERO-TRUST FOUNDER BARRIER v7.2" in API.read_text():
    print("v7.2 zaten uygulanmış.")
    sys.exit(0)

# ---------------------------------------------------------------- frontend
h = HTML.read_text()

# 1. Cut the technical-architecture body out of the public HTML (it is served only after auth)
m_start = h.index('id="techInfoModal"')
body_start = h.index('<div class="space-y-3 text-xs text-slate-300 leading-relaxed">', m_start)
modal_end = h.index("<!-- =====", m_start)
depth, i = 0, body_start
for tok in re.finditer(r"<div\b|</div>", h[body_start:modal_end]):
    depth += 1 if tok.group(0).startswith("<div") else -1
    if depth == 0:
        body_end = body_start + tok.end()
        break
tech_html = h[body_start:body_end]
h = h[:body_start] + '<div id="techInfoBody" class="text-xs text-slate-300">Kurucu doğrulaması yapılıyor...</div>' + h[body_end:]

# 2. Founder-only header controls + login button
anchor_a = "<button onclick=\"openCortexModal('tabOverview')\""
anchor_b = '<button onclick="openModelSettingsModal()"'
assert anchor_a in h and anchor_b in h
h = h.replace(
    anchor_a,
    '<div id="founderOnlyControls" class="hidden items-center gap-2">\n        ' + anchor_a, 1)
h = h.replace(
    anchor_b,
    '</div>\n        <button id="founderLoginBtn" onclick="founderBtnClick()" class="px-2.5 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-amber-500/40 text-amber-300 text-xs font-bold flex items-center gap-1 transition" title="SYNAX Kurucu Girişi (yalnızca Dr. Ömer Faruk Aydın)">🔐 <span class="hidden md:inline">Kurucu Girişi</span></button>\n        ' + anchor_b, 1)

# 3. Login modal + JS prelude (auth state, fetch wrapper, login/logout)
login_modal = '''  <!-- FOUNDER LOGIN (Zero-Trust) -->
  <div id="founderLoginModal" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-[60] items-center justify-center p-4">
    <div class="bg-[#0b101d] border border-amber-500/40 rounded-2xl max-w-sm w-full p-5 shadow-2xl space-y-3">
      <div class="flex items-center justify-between">
        <h2 class="text-sm font-black text-white">🔐 SYNAX Kurucu Doğrulaması</h2>
        <button onclick="closeFounderLogin()" class="px-2 py-1 rounded-lg bg-slate-800 text-slate-300 text-xs font-bold">✕</button>
      </div>
      <p class="text-[11px] text-slate-400 leading-relaxed">Bellek, kalıcı kişiselleştirme ve teknik mimari katmanları yalnızca Kurucu için açıktır. Parola + doğrulayıcı uygulama kodu gerekir.</p>
      <input type="password" id="founderPassInput" autocomplete="current-password" placeholder="Kurucu parolası (passkey)" class="w-full bg-[#070b14] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-400" />
      <input type="text" id="founderTotpInput" inputmode="numeric" maxlength="6" autocomplete="one-time-code" placeholder="6 haneli doğrulayıcı kodu" class="w-full bg-[#070b14] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white font-mono tracking-widest focus:outline-none focus:border-amber-400" onkeydown="if(event.key==='Enter'){submitFounderLogin();}" />
      <div id="founderLoginMsg" class="text-[11px] font-mono min-h-[16px]"></div>
      <button onclick="submitFounderLogin()" class="w-full py-2 rounded-xl bg-gradient-to-r from-amber-400 to-emerald-400 text-slate-950 font-black text-xs">Kimliği Doğrula &amp; Aç</button>
    </div>
  </div>

  <script>
    let founderToken = sessionStorage.getItem('synax_founder_token') || '';
    const _origFetch = window.fetch.bind(window);
    window.fetch = (u, o = {}) => {
      if (founderToken && typeof u === 'string' && u.indexOf('api.php') !== -1) {
        o = Object.assign({}, o, { headers: Object.assign({}, o.headers || {}, { 'X-Synax-Sovereign-Token': founderToken }) });
      }
      return _origFetch(u, o);
    };

    function applyFounderUi(on) {
      const box = document.getElementById('founderOnlyControls');
      const btn = document.getElementById('founderLoginBtn');
      if (box) { box.classList.toggle('hidden', !on); box.classList.toggle('flex', on); }
      if (btn) btn.innerHTML = on ? '🔓 <span class="hidden md:inline">Kurucu · Çıkış</span>' : '🔐 <span class="hidden md:inline">Kurucu Girişi</span>';
    }
    function founderBtnClick() { if (founderToken) founderLogout(); else openFounderLogin(); }
    function openFounderLogin() {
      const m = document.getElementById('founderLoginModal');
      m.classList.remove('hidden'); m.classList.add('flex');
      document.getElementById('founderPassInput').focus();
    }
    function closeFounderLogin() {
      const m = document.getElementById('founderLoginModal');
      m.classList.add('hidden'); m.classList.remove('flex');
      document.getElementById('founderPassInput').value = '';
      document.getElementById('founderTotpInput').value = '';
    }
    function founderLogout() {
      founderToken = ''; sessionStorage.removeItem('synax_founder_token');
      applyFounderUi(false);
      ['cortexModal', 'techInfoModal'].forEach(id => { const e = document.getElementById(id); if (e) { e.classList.add('hidden'); e.classList.remove('flex'); } });
    }
    async function submitFounderLogin() {
      const msg = document.getElementById('founderLoginMsg');
      msg.className = 'text-[11px] font-mono text-slate-300'; msg.textContent = 'Doğrulanıyor...';
      try {
        const r = await _origFetch('api.php?action=verify_sovereign', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'verify_sovereign', sovereign_passkey: document.getElementById('founderPassInput').value, totp_code: document.getElementById('founderTotpInput').value })
        });
        const d = await r.json().catch(() => ({}));
        if (r.ok && d.authorized) {
          founderToken = d.sovereign_token; sessionStorage.setItem('synax_founder_token', founderToken);
          closeFounderLogin(); applyFounderUi(true);
          personalizationLoadedOnce = false; refreshAutonomousCortex(false);
        } else {
          msg.className = 'text-[11px] font-mono text-rose-400'; msg.textContent = d.error || 'Doğrulama başarısız.';
        }
      } catch (e) { msg.className = 'text-[11px] font-mono text-rose-400'; msg.textContent = 'Bağlantı hatası.'; }
    }
    async function validateFounderSession() {
      if (!founderToken) { applyFounderUi(false); return; }
      try {
        const r = await fetch('api.php?action=cortex_status', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{"action":"cortex_status"}' });
        const d = await r.json();
        if (d && d.authorized) { applyFounderUi(true); renderCortexData(d); } else { founderLogout(); }
      } catch (e) {}
    }

    const SKILLS_21 = ['''
assert "<script>\n    const SKILLS_21 = [" in h
h = h.replace("  <script>\n    const SKILLS_21 = [", login_modal, 1)

# 4. Gate modals / background loop / init
old_tech = """    function openTechInfoModal() {
      const m = document.getElementById('techInfoModal');
      m.classList.remove('hidden');
      m.classList.add('flex');
    }"""
new_tech = """    async function openTechInfoModal() {
      if (!founderToken) { openFounderLogin(); return; }
      const m = document.getElementById('techInfoModal');
      m.classList.remove('hidden');
      m.classList.add('flex');
      try {
        const r = await fetch('api.php?action=sovereign_tech_info', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{"action":"sovereign_tech_info"}' });
        const d = await r.json();
        if (r.ok && d.html) { document.getElementById('techInfoBody').innerHTML = d.html; }
        else { founderLogout(); closeTechInfoModal(); openFounderLogin(); }
      } catch (e) {}
    }"""
assert old_tech in h
h = h.replace(old_tech, new_tech, 1)

old_cx = "function openCortexModal(defaultTab = 'tabOverview') {\n"
assert old_cx in h
h = h.replace(old_cx, old_cx + "      if (!founderToken) { openFounderLogin(); return; }\n", 1)

old_loop = "if (!isGenerating && document.visibilityState === 'visible') {"
assert old_loop in h
h = h.replace(old_loop, "if (founderToken && !isGenerating && document.visibilityState === 'visible') {", 1)

old_init = "      renderSkillsAccordion();\n      if (threads.length === 0) {"
assert old_init in h
h = h.replace(old_init, "      renderSkillsAccordion();\n      validateFounderSession();\n      if (threads.length === 0) {", 1)
HTML.write_text(h)

# ------------------------------------------------------------------ backend
a = API.read_text()

NEW_AUTH = r'''$server_groq_key = getenv('GROQ_API_KEY') ?: '';
foreach ([__DIR__, dirname(__DIR__)] as $__env_dir) {
    if (@is_readable($__env_dir . '/.synax_env.php')) {
        include $__env_dir . '/.synax_env.php';
        break;
    }
}
$sovereign_pass_salt = '';
$sovereign_pass_hash = '';
$sovereign_totp_secret = '';
$sovereign_session_secret = '';
foreach ([__DIR__, dirname(__DIR__)] as $__sv_dir) {
    if (@is_readable($__sv_dir . '/.synax_sovereign.php')) {
        include $__sv_dir . '/.synax_sovereign.php';
        break;
    }
}

$raw_input = file_get_contents('php://input');
$data = json_decode($raw_input, true) ?: [];
$action = $_GET['action'] ?? ($data['action'] ?? '');

// ============================================================================
// 0. ZERO-TRUST FOUNDER BARRIER v7.2  (Dr. Ömer Faruk Aydın ONLY)
//    Fail-closed: if founder credentials are not provisioned, NOBODY is founder.
//    Factors: PBKDF2 passkey + TOTP, then a 12h HMAC-signed expiring session token.
// ============================================================================
function synax_read_guarded($path) {
    if (!is_file($path)) return [];
    $raw = (string)@file_get_contents($path);
    $raw = preg_replace('/^<\?php exit; \?>\R?/', '', $raw);
    $j = json_decode($raw, true);
    return is_array($j) ? $j : [];
}
function synax_write_guarded($path, $arr) {
    @file_put_contents($path, "<?php exit; ?>\n" . json_encode($arr, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT), LOCK_EX);
}
function synax_b32_decode($s) {
    $alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
    $s = strtoupper(preg_replace('/[^A-Za-z2-7]/', '', (string)$s));
    $bits = '';
    foreach (str_split($s) as $c) {
        $v = strpos($alphabet, $c);
        if ($v === false) continue;
        $bits .= str_pad(decbin($v), 5, '0', STR_PAD_LEFT);
    }
    $out = '';
    foreach (str_split($bits, 8) as $byte) {
        if (strlen($byte) === 8) $out .= chr(bindec($byte));
    }
    return $out;
}
function synax_totp_verify($secret_b32, $code) {
    $code = preg_replace('/\D/', '', (string)$code);
    if (strlen($code) !== 6) return false;
    $key = synax_b32_decode($secret_b32);
    $t = intdiv(time(), 30);
    for ($i = -1; $i <= 1; $i++) {
        $counter = pack('N*', 0) . pack('N*', $t + $i);
        $h = hash_hmac('sha1', $counter, $key, true);
        $o = ord($h[19]) & 0xf;
        $bin = ((ord($h[$o]) & 0x7f) << 24) | ((ord($h[$o + 1]) & 0xff) << 16) | ((ord($h[$o + 2]) & 0xff) << 8) | (ord($h[$o + 3]) & 0xff);
        $otp = str_pad((string)($bin % 1000000), 6, '0', STR_PAD_LEFT);
        if (hash_equals($otp, $code)) return true;
    }
    return false;
}
function synax_issue_token($secret, $ttl = 43200) {
    $exp = time() + $ttl;
    return $exp . '.' . hash_hmac('sha256', 'SYNAX_FOUNDER|' . $exp, $secret);
}
function synax_verify_token($secret, $token) {
    if ($secret === '' || $token === '' || strpos($token, '.') === false) return false;
    list($exp, $sig) = explode('.', $token, 2);
    if (!ctype_digit($exp) || intval($exp) < time()) return false;
    return hash_equals(hash_hmac('sha256', 'SYNAX_FOUNDER|' . $exp, $secret), $sig);
}

$sovereign_configured = ($sovereign_pass_hash !== '' && $sovereign_pass_salt !== '' && $sovereign_session_secret !== '');
$client_token = trim((string)($_SERVER['HTTP_X_SYNAX_SOVEREIGN_TOKEN'] ?? ($data['sovereign_token'] ?? '')));
$is_sovereign_founder = $sovereign_configured && synax_verify_token($sovereign_session_secret, $client_token);

if ($action === 'verify_sovereign') {
    if (!$sovereign_configured) {
        http_response_code(503);
        echo json_encode(['authorized' => false, 'error' => 'Kurucu erişimi henüz yapılandırılmadı.'], JSON_UNESCAPED_UNICODE);
        exit;
    }
    $guard_file = __DIR__ . '/.sovereign_guard.php';
    $guard = synax_read_guarded($guard_file);
    $ip_hash = substr(hash('sha256', ($_SERVER['REMOTE_ADDR'] ?? '0') . '|synax'), 0, 16);
    $now_t = time();
    $rec = $guard['locks'][$ip_hash] ?? ['fails' => 0, 'lock_until' => 0];

    if (intval($rec['lock_until']) > $now_t) {
        http_response_code(429);
        echo json_encode(['authorized' => false, 'error' => 'Çok fazla hatalı deneme. Güvenlik kilidi aktif; daha sonra tekrar deneyin.'], JSON_UNESCAPED_UNICODE);
        exit;
    }

    // Evaluate BOTH factors every time so a failure never reveals which one was wrong.
    $pass_in = (string)($data['sovereign_passkey'] ?? '');
    $calc = hash_pbkdf2('sha256', $pass_in, $sovereign_pass_salt, 250000, 64, false);
    $pass_ok = ($pass_in !== '') && hash_equals($sovereign_pass_hash, $calc);
    $totp_ok = ($sovereign_totp_secret === '') ? true : synax_totp_verify($sovereign_totp_secret, $data['totp_code'] ?? '');

    $audit = $guard['audit'] ?? [];
    if ($pass_ok && $totp_ok) {
        unset($guard['locks'][$ip_hash]);
        $recent = array_slice($audit, 0, 5);
        array_unshift($audit, ['t' => gmdate('Y-m-d H:i:s') . ' UTC', 'ip' => $ip_hash, 'event' => 'LOGIN_OK']);
        $guard['audit'] = array_slice($audit, 0, 40);
        synax_write_guarded($guard_file, $guard);
        echo json_encode([
            'authorized' => true,
            'role' => 'SOVEREIGN_FOUNDER',
            'sovereign_token' => synax_issue_token($sovereign_session_secret),
            'expires_in_sec' => 43200,
            'recent_access_events' => $recent,
        ], JSON_UNESCAPED_UNICODE);
        exit;
    }

    $rec['fails'] = intval($rec['fails'] ?? 0) + 1;
    if ($rec['fails'] >= 5) {
        $rec['lock_until'] = $now_t + 900; // 15-minute lockout after 5 failures
        $rec['fails'] = 0;
    }
    $guard['locks'][$ip_hash] = $rec;
    array_unshift($audit, ['t' => gmdate('Y-m-d H:i:s') . ' UTC', 'ip' => $ip_hash, 'event' => 'LOGIN_FAIL']);
    $guard['audit'] = array_slice($audit, 0, 40);
    synax_write_guarded($guard_file, $guard);
    usleep(700000);
    http_response_code(403);
    echo json_encode(['authorized' => false, 'error' => 'Doğrulama başarısız.'], JSON_UNESCAPED_UNICODE);
    exit;
}

if ($action === 'sovereign_tech_info') {
    if (!$is_sovereign_founder) {
        http_response_code(403);
        echo json_encode(['error' => 'Bu katman yalnızca Kurucu içindir.'], JSON_UNESCAPED_UNICODE);
        exit;
    }
    $tech_html = <<<'SXHTML'
__TECH_HTML__
SXHTML;
    echo json_encode(['html' => $tech_html], JSON_UNESCAPED_UNICODE);
    exit;
}

'''.replace("__TECH_HTML__", tech_html)

start = a.index("$server_groq_key = getenv('GROQ_API_KEY') ?: '';")
end = a.index("// ============================================================================\n// 1. 24/7 AUTONOMOUS")
a = a[:start] + NEW_AUTH + a[end:]

def sub(old, new, count_expected=None):
    global a
    assert old in a, f"anchor not found: {old[:60]}"
    a = a.replace(old, new)

sub("header('Access-Control-Allow-Headers: Content-Type, Authorization');",
    "header('Access-Control-Allow-Headers: Content-Type, Authorization, X-Synax-Sovereign-Token');")
sub("$cortex_file = __DIR__ . '/synax_memory_cortex.json';", "$cortex_file = __DIR__ . '/synax_memory_cortex.php';")
sub("$cortex = file_exists($cortex_file) ? (json_decode(file_get_contents($cortex_file), true) ?: []) : [];",
    "$cortex = synax_read_guarded($cortex_file);")
sub("@file_put_contents($cortex_file, json_encode($cortex, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));",
    "synax_write_guarded($cortex_file, $cortex);")
sub("$custom_sys = trim($data['custom_system_prompt'] ?? '');",
    "$custom_sys = $is_sovereign_founder ? trim($data['custom_system_prompt'] ?? '') : '';")
API.write_text(a)

# telegram bot: read the guarded cortex file
TG = BASE / "sites" / "telegram_webhook.php"
t = TG.read_text()
old_t = "$cortex_file = __DIR__ . '/synax_memory_cortex.json';\n$cortex = file_exists($cortex_file) ? (json_decode(file_get_contents($cortex_file), true) ?: []) : [];"
if old_t in t:
    t = t.replace(old_t, "$cortex_file = __DIR__ . '/synax_memory_cortex.php';\n$cortex = file_exists($cortex_file) ? (json_decode(preg_replace('/^<\\?php exit; \\?>\\R?/', '', (string)file_get_contents($cortex_file)), true) ?: []) : [];")
    TG.write_text(t)

print("v7.2 yamaları uygulandı. tech_html uzunluğu:", len(tech_html))
