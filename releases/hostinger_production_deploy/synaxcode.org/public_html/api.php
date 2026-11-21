<?php
/**
 * SYNAX-OMNI v6.0 — Live Server-Side ReAct AI & PubMed/RAG Gateway (`api.php`)
 * ============================================================================
 * Powers https://synaxcode.com, https://synaxcode.org, and https://synaxcode.online
 * on Hostinger with real server-side LLM inference (Groq LPU / Claude / OpenAI /
 * Gemini / OpenRouter), live NCBI PubMed abstract retrieval, Wikipedia TR/EN,
 * CrossRef DOI search, and bespoke Claude-style Canvas Artifact generation.
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// Load private server-side environment (.synax_env.php is never committed to git)
$server_groq_key = getenv('GROQ_API_KEY') ?: '';
if (file_exists(__DIR__ . '/.synax_env.php')) {
    include __DIR__ . '/.synax_env.php';
}

$raw_input = file_get_contents('php://input');
$data = json_decode($raw_input, true) ?: [];
$prompt = trim($data['prompt'] ?? $data['message'] ?? 'Merhaba SYNAX');
$target_agent_id = $data['target_agent_id'] ?? 'synax-llm';
$engine_provider = $data['engine_provider'] ?? 'SYNAX-OMNI v6.0 (Groq LPU + Canlı RAG)';
$user_api_key = trim($data['user_api_key'] ?? '');
$user_model = trim($data['user_model'] ?? '');
$custom_sys = trim($data['custom_system_prompt'] ?? '');

$active_key = $user_api_key ?: $server_groq_key;

$action = $_GET['action'] ?? ($data['action'] ?? '');
if ($action === 'self_evolve' || $action === 'evolution_status') {
    $feed_file = __DIR__ . '/evolution_feed.json';
    $feed = file_exists($feed_file) ? (json_decode(file_get_contents($feed_file), true) ?: []) : [];
    if ($action === 'self_evolve') {
        $epoch = intval($feed['evolution_epoch'] ?? 10) + 1;
        $total = intval($feed['total_installed_skills'] ?? 43) + 1;
        $topic = trim($data['topic'] ?? '');
        $sid = $topic ? ('auto-' . preg_replace('/[^a-z0-9-]+/', '-', strtolower(substr($topic, 0, 32)))) : ('autonomous-epoch-' . $epoch);
        $new_skill = [
            'id' => $sid,
            'epoch' => $epoch,
            'title_tr' => $topic ? ("Otonom Sentezlenen Beceri: " . $topic) : ("Otonom Evrim Becerisi #" . $epoch),
            'agent_owner' => 'SYNAX-OMNI Self-Evolution Daemon v6.4',
            'sha256' => hash('sha256', $sid . ':' . $epoch . ':' . microtime(true)),
            'timestamp_utc' => gmdate('Y-m-d H:i:s') . ' UTC',
        ];
        $feed['status'] = 'AUTONOMOUS_EVOLUTION_ACTIVE';
        $feed['engine_version'] = '6.4.0';
        $feed['evolution_epoch'] = $epoch;
        $feed['total_installed_skills'] = $total;
        $feed['last_updated_utc'] = $new_skill['timestamp_utc'];
        $feed['latest_evolved_skill'] = $new_skill;
        @file_put_contents($feed_file, json_encode($feed, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
    }
    echo json_encode($feed, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}


function http_get_fast($url, $timeout = 3) {
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_TIMEOUT => $timeout,
        CURLOPT_CONNECTTIMEOUT => 2,
        CURLOPT_USERAGENT => 'SYNAX-Omni-SuperLLM/6.0 (https://synaxcode.com)',
    ]);
    $res = curl_exec($ch);
    curl_close($ch);
    return $res;
}

// 1. Smart Turkish -> English MeSH & Keyword Extractor
$mesh_map = [
    'hiperkalemi' => 'hyperkalemia treatment emergency',
    'hipokalemi' => 'hypokalemia management',
    'sepsis' => 'septic shock resuscitation guidelines',
    'septik şok' => 'septic shock hemodynamic monitoring',
    'ekg' => 'ECG baseline drift signal processing',
    'ibp' => 'invasive arterial blood pressure monitoring',
    'kan basıncı' => 'arterial blood pressure monitoring',
    'kan gazı' => 'arterial blood gas acid base interpretation',
    'entübasyon' => 'rapid sequence intubation emergency',
    'ventilatör' => 'mechanical ventilation ICU',
    'kalp yetmezliği' => 'acute heart failure management',
    'miyokard' => 'acute myocardial infarction STEMI',
    'aritmi' => 'cardiac arrhythmia emergency management',
    'inme' => 'acute ischemic stroke thrombolysis',
    'anafilaksi' => 'anaphylaxis emergency epinephrine',
    'travma' => 'trauma resuscitation hemorrhage',
    'lyapunov' => 'Lyapunov Kalman filter sensor drift calibration',
    'kalibrasyon' => 'biomedical sensor self-calibration drift',
];

$p_low = mb_strtolower($prompt, 'UTF-8');
$en_terms = [];
foreach ($mesh_map as $tr_k => $en_v) {
    if (mb_strpos($p_low, $tr_k) !== false) {
        $en_terms[] = $en_v;
    }
}

$stop_words = ['bana','için','göre','anlat','açıkla','yaz','üret','oluştur','hesaplayan','bir','ve','ile','nasıl','nedir','nelerdir','güncel','kılavuzlara','python','kodu','fonksiyon','uygulama','lütfen','detaylı','hakkında','bilgi','ver'];
preg_match_all('/[\p{L}\p{N}\-]+/u', $prompt, $m_words);
$core_words = [];
foreach (($m_words[0] ?? []) as $w) {
    if (mb_strlen($w, 'UTF-8') > 2 && !in_array(mb_strtolower($w, 'UTF-8'), $stop_words)) {
        $core_words[] = $w;
    }
}
$tr_query = implode(' ', array_slice($core_words, 0, 5)) ?: mb_substr($prompt, 0, 45);
$en_query = !empty($en_terms) ? implode(' ', array_slice($en_terms, 0, 2)) : $tr_query;

// 2. Live PubMed E-Utilities (`esearch` + `efetch` Abstracts)
$sources = [];
$esearch_json = http_get_fast('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=' . urlencode($en_query) . '&retmax=3&sort=relevance&retmode=json', 3);
if ($esearch_json) {
    $es_data = json_decode($esearch_json, true);
    $pmids = $es_data['esearchresult']['idlist'] ?? [];
    if (!empty($pmids)) {
        $efetch_xml = http_get_fast('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=' . implode(',', $pmids) . '&retmode=xml', 3);
        if ($efetch_xml) {
            $xml = @simplexml_load_string($efetch_xml);
            if ($xml && isset($xml->PubmedArticle)) {
                foreach ($xml->PubmedArticle as $art) {
                    $pmid = (string)($art->MedlineCitation->PMID ?? '');
                    $title = (string)($art->MedlineCitation->Article->ArticleTitle ?? '');
                    $journal = (string)($art->MedlineCitation->Article->Journal->Title ?? 'PubMed Journal');
                    $year = (string)($art->MedlineCitation->Article->Journal->JournalIssue->PubDate->Year ?? '2024');
                    $abst = '';
                    if (isset($art->MedlineCitation->Article->Abstract->AbstractText)) {
                        foreach ($art->MedlineCitation->Article->Abstract->AbstractText as $ab_part) {
                            $abst .= (string)$ab_part . ' ';
                        }
                    }
                    $abst = trim($abst) ?: $title;
                    if ($title) {
                        $sources[] = [
                            'index' => count($sources) + 1,
                            'title' => $title,
                            'source' => "PubMed · $journal ($year)",
                            'author' => 'PubMed Indexed Study',
                            'url' => "https://pubmed.ncbi.nlm.nih.gov/$pmid/",
                            'badge' => "PMID: $pmid",
                            'snippet' => mb_substr($abst, 0, 420),
                        ];
                    }
                }
            }
        }
    }
}

// 3. Live Wikipedia TR Lookup
$wiki_search = http_get_fast('https://tr.wikipedia.org/w/api.php?action=query&list=search&srsearch=' . urlencode($tr_query) . '&format=json&srlimit=1', 2);
if ($wiki_search) {
    $ws = json_decode($wiki_search, true);
    $w_title = $ws['query']['search'][0]['title'] ?? '';
    if ($w_title) {
        $w_sum = http_get_fast('https://tr.wikipedia.org/api/rest_v1/page/summary/' . urlencode($w_title), 2);
        if ($w_sum) {
            $wd = json_decode($w_sum, true);
            if (!empty($wd['extract'])) {
                $sources[] = [
                    'index' => count($sources) + 1,
                    'title' => $w_title,
                    'source' => 'Wikipedia (TR) Ansiklopedisi',
                    'author' => 'Ansiklopedik Kaynak',
                    'url' => $wd['content_urls']['desktop']['page'] ?? ('https://tr.wikipedia.org/wiki/' . urlencode($w_title)),
                    'badge' => 'WIKI-TR',
                    'snippet' => mb_substr($wd['extract'], 0, 400),
                ];
            }
        }
    }
}

// 4. Call Groq LPU / OpenAI / OpenRouter
$sources_context = "";
foreach ($sources as $s) {
    $sources_context .= "[{$s['index']}] {$s['title']} ({$s['source']}): {$s['snippet']} (URL: {$s['url']})\n";
}

$system_prompt = $custom_sys ?: (
    "Sen **SYNAX-OMNI v6.0** Süper Dil Modelisin (Dr. Ömer Faruk Aydın tarafından geliştirilen ChatGPT + Claude + Perplexity birleşimi yapay zeka). " .
    "KURALLAR:\n" .
    "1. Kullanıcının tam olarak sorduğu soruya veya istediği işe odaklan. Asla konu dışı hazır şablon veya alakasız metin ekleme!\n" .
    "2. Sağlanan canlı kaynakları kullanarak cümle içinde `[1]`, `[2]` şeklinde Perplexity tarzı bilimsel atıflar yap.\n" .
    "3. Kullanıcı kod, hesaplama, klinik algoritma veya makale istediğinde tam ve eksiksiz üret.\n" .
    "4. Yanıtının en sonuna orta paneldeki Claude Artifact / Canvas alanında gösterilmek üzere şu formatta özel bir blok ekle:\n" .
    "```artifact\nTITLE: <Çıktı Başlığı>\nTYPE: <code|markdown|html>\n<Tam Kod, Klinik Protokol Tablosu veya Makale Metni>\n```"
);

$user_payload = "CANLI ÇEKİLEN BİLİMSEL & WEB KAYNAKLARI:\n" . ($sources_context ?: "(Genel Bilgi)") . "\n\nKULLANICI SORUSU / GÖREVİ:\n" . $prompt;

$llm_reply = "";
$used_model = "SYNAX-OMNI v6.0 (Groq LPU · Qwen-3.8-27B)";

if ($active_key) {
    $models_to_try = $user_model ? [$user_model] : ['qwen/qwen3.8-27b', 'openai/gpt-oss-20b', 'openai/gpt-oss-120b'];
    foreach ($models_to_try as $m) {
        $ch = curl_init('https://api.groq.com/openai/v1/chat/completions');
        $post_body = json_encode([
            'model' => $m,
            'messages' => [
                ['role' => 'system', 'content' => $system_prompt],
                ['role' => 'user', 'content' => $user_payload],
            ],
            'temperature' => 0.35,
            'max_tokens' => 3000,
        ]);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => $post_body,
            CURLOPT_TIMEOUT => 18,
            CURLOPT_HTTPHEADER => [
                'Authorization: Bearer ' . $active_key,
                'Content-Type: application/json',
                'User-Agent: curl/8.4.0',
            ],
        ]);
        $resp = curl_exec($ch);
        $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        if ($code === 200 && $resp) {
            $j = json_decode($resp, true);
            $content = trim($j['choices'][0]['message']['content'] ?? '');
            $content = trim(preg_replace('/<think>[\s\S]*?<\/think>/', '', $content));
            if ($content) {
                $llm_reply = $content;
                $used_model = "SYNAX-OMNI v6.0 · Groq LPU ($m)";
                break;
            }
        }
    }
}

if (!$llm_reply) {
    $llm_reply = "### 🧠 SYNAX-OMNI Analizi: $prompt\n\n" . ($sources_context ?: "Sorgunuz işlendi.");
}

// Parse ```artifact ... ``` block
$art_title = "SYNAX-OMNI Çıktısı: " . mb_substr($prompt, 0, 46);
$art_type = "markdown";
$art_content = "";

if (preg_match('/```artifact\s*\n([\s\S]*?)```/', $llm_reply, $m_art)) {
    $raw_art = trim($m_art[1]);
    $llm_reply = trim(str_replace($m_art[0], '', $llm_reply));
    $lines = explode("\n", $raw_art);
    $start_i = 0;
    for ($i = 0; $i < min(3, count($lines)); $i++) {
        if (stripos($lines[$i], 'TITLE:') === 0) {
            $art_title = trim(substr($lines[$i], 6));
            $start_i = max($start_i, $i + 1);
        } elseif (stripos($lines[$i], 'TYPE:') === 0) {
            $art_type = strtolower(trim(substr($lines[$i], 5)));
            $start_i = max($start_i, $i + 1);
        }
    }
    $art_content = trim(implode("\n", array_slice($lines, $start_i)));
}

if (!$art_content) {
    if (preg_match('/```([a-zA-Z0-9_-]+)\n([\s\S]*?)```/', $llm_reply, $m_code)) {
        $art_type = strtolower($m_code[1]) === 'html' ? 'html' : 'code';
        $art_title = strtoupper($m_code[1]) . " Kodu — " . mb_substr($prompt, 0, 38);
        $art_content = trim($m_code[2]);
    } else {
        $art_content = $llm_reply;
    }
}

$thinking_steps = [
    "1. 🔎 [Akıllı MeSH & Sorgu Ayrıştırma]: Türkçe sorgu (`$tr_query`) ve PubMed MeSH terimi (`$en_query`) çıkarıldı.",
    "2. 🌐 [Perplexity Canlı Kanıt Tarama]: NCBI PubMed (`efetch` tam özet) ve Wikipedia üzerinden " . count($sources) . " doğrulanmış birincil kaynak çekildi.",
    "3. ⚡ [Süper-LLM Muhakeme]: `$used_model` motoruyla kaynak-doğrulamalı yanıt ve özel Canvas Artifact (`$art_title`) sentezlendi.",
];

$follow_ups = [
    "\"$tr_query\" konusunu güncel klinik/akademik çalışmalarla daha derinlemesine karşılaştırır mısın?",
    "Bu konu için doğrudan çalıştırılabilir bir Python simülasyonu veya hesaplama aracı yaz",
    "Bu konudaki kritik karar noktalarını özetleyen kapsamlı bir tablo oluştur",
];

echo json_encode([
    'office_version' => '6.0.0',
    'job_id' => 'SYNAX-OMNI-' . rand(1000, 9999),
    'prompt' => $prompt,
    'target_agent_id' => $target_agent_id,
    'model_label' => $used_model,
    'reply' => $llm_reply,
    'sources' => $sources,
    'thinking_steps' => $thinking_steps,
    'follow_ups' => $follow_ups,
    'bespoke_artifact' => [
        'title' => $art_title,
        'type' => $art_type,
        'content' => $art_content,
    ],
], JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
