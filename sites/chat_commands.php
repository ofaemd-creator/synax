<?php
/** Pure request normalization; no network, credentials or persistence. */
function synax_chat_timeout($started_at, $now, $provider_timeout) {
    return max(0, min((int)$provider_timeout, (int)floor($started_at + 34.0 - $now)));
}

function synax_provider_payload($url, $model, $messages, $temperature, $enable_thinking) {
    $payload = [
        'model' => $model,
        'messages' => $messages,
        'temperature' => max(0.0, min(1.0, $temperature)),
        'max_tokens' => 4096,
    ];
    if (parse_url($url, PHP_URL_HOST) === 'integrate.api.nvidia.com' && strpos($model, 'nemotron') !== false) {
        $payload['chat_template_kwargs'] = ['enable_thinking' => (bool)$enable_thinking];
    }
    return $payload;
}

function synax_prepare_chat_request(array $data) {
    unset($data['_command_instruction'], $data['_command']);
    $text = $data['prompt'] ?? $data['message'] ?? '';
    if (!is_string($text)) {
        return ['data' => $data, 'response' => ['status_code' => 400, 'reply' => 'Mesaj metin olmalıdır.', 'error' => 'INVALID_PROMPT']];
    }
    $text = trim($text);
    $catalog = [
        'prisma' => ['Sistematik derleme planı ve kaynak araştırması', 'synax-med-scholar', true, 'academic', 'Araştırma sorusunu ve protokolü açıkla. PRISMA sayıları veya eleme işlemleri gerçekten yapılmadıysa tamamlandı diye yazma.'],
        'q1' => ['Akademik makale taslağı', 'synax-med-scholar', true, 'academic', 'Kaynak destekli bir akademik taslak hazırla. Eksik veriyi belirt; sonuç veya dergi kabulü uydurma.'],
        'meta' => ['Veriye dayalı meta-analiz desteği', 'synax-biostat-lyapunov', true, 'academic', 'Gerekli çalışma verilerini ve varsayımları denetle. Çalıştırılmayan istatistik hesabını yapılmış gibi sunma.'],
        'humanize' => ['Metni anlamını ve atıflarını koruyarak düzenle', 'synax-turbo-flash', false, 'all', 'Verilen metni akıcı biçimde düzenle; anlamı, atıfları ve sayıları koru.'],
        'klinik' => ['Kaynaklı klinik bilgi', 'synax-med-scholar', true, 'academic', 'İlgili güncel kaynakları kullan; kanıtın kapsamını ve belirsizliğini belirt.'],
        'kod' => ['Kod geliştirme desteği', 'synax-silicon-code', false, 'tech_code', 'İstenen kodu ve gerekli açıklamayı üret. Gerçekte çalıştırılmamış test veya formal kanıt için başarılı iddiası kullanma.'],
        'web' => ['Web ve haber araştırması', 'synax-turbo-flash', true, 'web_news', 'İlgili canlı kaynaklara dayanarak doğrudan yanıt ver. Kaynaklar yoksa güncel araştırma yapıldığını iddia etme.'],
        'tablo' => ['Karşılaştırmalı tablo', 'synax-med-scholar', true, 'academic', 'İstenen karşılaştırmayı kaynak destekli bir tabloda sun; eksik veya doğrulanmamış değerleri belirt.'],
    ];
    if (!preg_match('~^/([a-zA-Z][a-zA-Z0-9_-]*)(?:\s+([\s\S]*))?$~u', $text, $m) && $text !== '/') {
        return ['data' => $data, 'response' => null];
    }
    $name = strtolower($m[1] ?? 'help');
    $args = trim($m[2] ?? '');
    $help = "Kullanılabilir komutlar:\n\n";
    foreach ($catalog as $id => $spec) {
        $help .= "- `/{$id} konu veya metin` — {$spec[0]}\n";
    }
    if (in_array($name, ['help', 'yardim', 'komutlar'], true)) {
        return ['data' => $data, 'response' => ['status_code' => 200, 'reply' => $help, 'model_label' => 'SYNAX Komut Yardımı', 'sources' => [], 'command' => ['name' => $name, 'requires_input' => false]]];
    }
    if (!isset($catalog[$name])) {
        return ['data' => $data, 'response' => ['status_code' => 400, 'reply' => "Bilinmeyen komut: /{$name}. Liste için `/help` yazın.", 'error' => 'UNKNOWN_COMMAND']];
    }
    if ($args === '') {
        return ['data' => $data, 'response' => ['status_code' => 200, 'reply' => "Kullanım: `/{$name} konu veya metin`\n\n{$catalog[$name][0]}. Komutun ardından çalışılacak konuyu veya metni yazın.", 'model_label' => 'SYNAX Komut Yardımı', 'sources' => [], 'command' => ['name' => $name, 'requires_input' => true]]];
    }
    $spec = $catalog[$name];
    $data['prompt'] = $args;
    $data['user_model'] = $spec[1];
    $data['web_search'] = $spec[2];
    $data['web_search_mode'] = $spec[3];
    $data['_command_instruction'] = $spec[4];
    $data['_command'] = $name;
    return ['data' => $data, 'response' => null];
}
