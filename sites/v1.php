<?php
/**
 * SYNAX Commercial OpenAI-Compatible API Gateway (`v1.php` -> /v1.php)
 * =====================================================================
 * Allows external developers, hospitals, apps, Cursor, Continue, LangChain,
 * and OpenAI Python/Node SDKs to integrate directly with SYNAX Core LLM &
 * SYNAX-OMNI 1.5 using `sk-synax-...` API keys and prepaid credit balances.
 *
 * Usage:
 *   POST https://chat.synaxcode.com/v1.php
 *   Authorization: Bearer sk-synax-...
 *   {"model": "synax-omni-1.5-ultra", "messages": [{"role": "user", "content": "..."}]}
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

function v1_read_guarded($path) {
    if (!is_file($path)) return [];
    $raw = preg_replace('/^<\?php exit; \?>\R?/', '', (string)@file_get_contents($path));
    $j = json_decode($raw, true);
    return is_array($j) ? $j : [];
}
function v1_write_guarded($path, $arr) {
    @file_put_contents($path, "<?php exit; ?>\n" . json_encode($arr, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT), LOCK_EX);
}

$keys_file = __DIR__ . '/.synax_api_keys.php';
$keys_store = v1_read_guarded($keys_file);
$all_keys = is_array($keys_store['keys'] ?? null) ? $keys_store['keys'] : [];

// GET /v1.php -> OpenAI-compatible /v1/models catalog
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $now = time();
    echo json_encode([
        'object' => 'list',
        'provider' => 'SYNAX Sovereign AI Platform (Dr. Omer Faruk Aydin)',
        'data' => [
            ['id' => 'synax-core-1.5', 'object' => 'model', 'created' => $now, 'owned_by' => 'synax', 'credit_cost_per_1k_tokens' => 1],
            ['id' => 'synax-omni-1.5-ultra', 'object' => 'model', 'created' => $now, 'owned_by' => 'synax', 'credit_cost_per_1k_tokens' => 5],
            ['id' => 'synax-med-scholar-1.5', 'object' => 'model', 'created' => $now, 'owned_by' => 'synax', 'credit_cost_per_1k_tokens' => 5],
            ['id' => 'synax-silicon-code-1.5', 'object' => 'model', 'created' => $now, 'owned_by' => 'synax', 'credit_cost_per_1k_tokens' => 4],
            ['id' => 'synax-biostat-lyapunov-1.5', 'object' => 'model', 'created' => $now, 'owned_by' => 'synax', 'credit_cost_per_1k_tokens' => 4],
            ['id' => 'synax-turbo-1.5-flash', 'object' => 'model', 'created' => $now, 'owned_by' => 'synax', 'credit_cost_per_1k_tokens' => 2],
        ],
    ], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

// Extract Bearer sk-synax-... API key
$auth_hdr = (string)($_SERVER['HTTP_AUTHORIZATION'] ?? ($_SERVER['REDIRECT_HTTP_AUTHORIZATION'] ?? ''));
if (!$auth_hdr && function_exists('getallheaders')) {
    foreach (getallheaders() as $hk => $hv) {
        if (strtolower($hk) === 'authorization') { $auth_hdr = (string)$hv; break; }
    }
}
$bearer_key = '';
if (preg_match('/Bearer\s+(sk-synax-[A-Za-z0-9_-]+)/i', $auth_hdr, $km)) {
    $bearer_key = trim($km[1]);
}

if ($bearer_key === '') {
    http_response_code(401);
    echo json_encode(['error' => ['message' => 'Missing or invalid SYNAX API key. Expected Authorization: Bearer sk-synax-...', 'type' => 'authentication_error', 'code' => 'invalid_api_key']], JSON_UNESCAPED_UNICODE);
    exit;
}

$key_hash = hash('sha256', $bearer_key);
$matched_idx = -1;
foreach ($all_keys as $idx => $krec) {
    if (!empty($krec['key_hash']) && hash_equals($krec['key_hash'], $key_hash)) {
        $matched_idx = $idx;
        break;
    }
}

if ($matched_idx === -1) {
    http_response_code(401);
    echo json_encode(['error' => ['message' => 'SYNAX API key not found or revoked.', 'type' => 'authentication_error', 'code' => 'key_not_found']], JSON_UNESCAPED_UNICODE);
    exit;
}

$krec = $all_keys[$matched_idx];
if (($krec['status'] ?? 'active') !== 'active') {
    http_response_code(403);
    echo json_encode(['error' => ['message' => 'This SYNAX API key is suspended.', 'type' => 'permission_error', 'code' => 'key_suspended']], JSON_UNESCAPED_UNICODE);
    exit;
}

$credits_left = floatval($krec['credits_remaining'] ?? 0);
if ($credits_left <= 0) {
    http_response_code(402);
    echo json_encode(['error' => ['message' => 'Insufficient SYNAX credits. Please top up your credit balance at chat.synaxcode.com.', 'type' => 'insufficient_quota', 'code' => 'credits_exhausted']], JSON_UNESCAPED_UNICODE);
    exit;
}

$body = json_decode(file_get_contents('php://input'), true) ?: [];
$messages = is_array($body['messages'] ?? null) ? $body['messages'] : [];
$req_model = strtolower(trim((string)($body['model'] ?? 'synax-omni-1.5-ultra')));
$last_prompt = '';
foreach (array_reverse($messages) as $m) {
    if (($m['role'] ?? '') === 'user' && !empty($m['content'])) {
        $last_prompt = is_string($m['content']) ? $m['content'] : json_encode($m['content']);
        break;
    }
}
if ($last_prompt === '') {
    http_response_code(400);
    echo json_encode(['error' => ['message' => 'messages array must include at least one user message.', 'type' => 'invalid_request_error']], JSON_UNESCAPED_UNICODE);
    exit;
}

$model_map = [
    'synax-core-1.5' => ['internal' => 'synax-core-1.5', 'rate' => 1.0],
    'synax-omni-1.5-ultra' => ['internal' => 'synax-omni-ultra', 'rate' => 5.0],
    'synax-med-scholar-1.5' => ['internal' => 'synax-med-scholar', 'rate' => 5.0],
    'synax-silicon-code-1.5' => ['internal' => 'synax-silicon-code', 'rate' => 4.0],
    'synax-biostat-lyapunov-1.5' => ['internal' => 'synax-biostat-lyapunov', 'rate' => 4.0],
    'synax-turbo-1.5-flash' => ['internal' => 'synax-turbo-flash', 'rate' => 2.0],
];
$chosen = $model_map[$req_model] ?? $model_map['synax-omni-1.5-ultra'];

// Forward internally to SYNAX api.php engine
$scheme = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
$host = $_SERVER['HTTP_HOST'] ?? 'chat.synaxcode.com';
$dir = rtrim(dirname($_SERVER['SCRIPT_NAME'] ?? ''), '/');
$internal_api_url = "{$scheme}://{$host}{$dir}/api.php";

$ch = curl_init($internal_api_url);
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode([
        'prompt' => $last_prompt,
        'messages' => $messages,
        'user_model' => $chosen['internal'],
        'web_search' => isset($body['web_search']) ? (bool)$body['web_search'] : true,
        'temperature' => isset($body['temperature']) ? floatval($body['temperature']) : 0.35,
    ]),
    CURLOPT_TIMEOUT => 35,
    CURLOPT_HTTPHEADER => ['Content-Type: application/json', 'User-Agent: SYNAX-V1-Gateway/9.0'],
]);
$raw_res = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

$api_res = $raw_res ? (json_decode($raw_res, true) ?: []) : [];
$reply_text = (string)($api_res['reply'] ?? '');
if ($http_code !== 200 || $reply_text === '') {
    http_response_code(502);
    echo json_encode(['error' => ['message' => 'SYNAX Core inference temporarily unavailable.', 'type' => 'server_error']], JSON_UNESCAPED_UNICODE);
    exit;
}

// Token accounting & Credit deduction
$prompt_tokens = max(1, intval(ceil(mb_strlen($last_prompt, 'UTF-8') / 3.8)));
$completion_tokens = max(1, intval(ceil(mb_strlen($reply_text, 'UTF-8') / 3.8)));
$total_tokens = $prompt_tokens + $completion_tokens;
$credits_used = round(max(0.1, ($total_tokens / 1000.0) * $chosen['rate']), 3);

$all_keys[$matched_idx]['credits_remaining'] = round(max(0.0, $credits_left - $credits_used), 3);
$all_keys[$matched_idx]['credits_used_total'] = round(floatval($krec['credits_used_total'] ?? 0) + $credits_used, 3);
$all_keys[$matched_idx]['total_requests'] = intval($krec['total_requests'] ?? 0) + 1;
$all_keys[$matched_idx]['total_tokens'] = intval($krec['total_tokens'] ?? 0) + $total_tokens;
$all_keys[$matched_idx]['last_used_utc'] = gmdate('Y-m-d H:i:s') . ' UTC';
$keys_store['keys'] = $all_keys;
$keys_store['total_platform_requests'] = intval($keys_store['total_platform_requests'] ?? 0) + 1;
$keys_store['total_platform_credits_billed'] = round(floatval($keys_store['total_platform_credits_billed'] ?? 0) + $credits_used, 3);
v1_write_guarded($keys_file, $keys_store);

// Return 100% OpenAI-compatible Chat Completion JSON
echo json_encode([
    'id' => 'chatcmpl-synax-' . bin2hex(random_bytes(8)),
    'object' => 'chat.completion',
    'created' => time(),
    'model' => $req_model,
    'choices' => [[
        'index' => 0,
        'message' => [
            'role' => 'assistant',
            'content' => $reply_text,
        ],
        'finish_reason' => 'stop',
    ]],
    'usage' => [
        'prompt_tokens' => $prompt_tokens,
        'completion_tokens' => $completion_tokens,
        'total_tokens' => $total_tokens,
    ],
    'synax_billing' => [
        'credits_charged' => $credits_used,
        'credits_remaining' => $all_keys[$matched_idx]['credits_remaining'],
        'tier' => $krec['tier'] ?? 'pro',
    ],
], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
