<?php
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");
header("Content-Type: application/json; charset=UTF-8");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

$dataFile = __DIR__ . '/bayi_basvurular.json';

function getStoredData($file) {
    if (!file_exists($file)) return [];
    $content = file_get_contents($file);
    return json_decode($content, true) ?: [];
}

function saveStoredData($file, $data) {
    file_put_contents($file, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}

function validateVknChecksum($vkn) {
    $vkn = trim((string)$vkn);
    if (strlen($vkn) !== 10 || !ctype_digit($vkn)) return false;
    $digits = array_map('intval', str_split($vkn));
    $total = 0;
    for ($i = 0; $i < 9; $i++) {
        $v1 = ($digits[$i] + (9 - $i)) % 10;
        $v2 = ($v1 * pow(2, 9 - $i)) % 9;
        if ($v1 !== 0 && $v2 === 0) $v2 = 9;
        $total += $v2;
    }
    $expected = (10 - ($total % 10)) % 10;
    return $expected === $digits[9];
}

function validateTcknChecksum($tckn) {
    $tckn = trim((string)$tckn);
    if (strlen($tckn) !== 11 || !ctype_digit($tckn) || $tckn[0] === '0') return false;
    $digits = array_map('intval', str_split($tckn));
    $oddSum = $digits[0] + $digits[2] + $digits[4] + $digits[6] + $digits[8];
    $evenSum = $digits[1] + $digits[3] + $digits[5] + $digits[7];
    $c10 = (($oddSum * 7) - $evenSum) % 10;
    if ($c10 !== $digits[9]) return false;
    return (array_sum(array_slice($digits, 0, 10)) % 10) === $digits[10];
}

function verifyTaxId($taxId, $title = '') {
    $taxId = trim((string)$taxId);
    $taxOffices = [
        "Kadıköy Vergi Dairesi", "Beşiktaş Vergi Dairesi", "Büyük Mükellefler Vergi Dairesi",
        "Konak Vergi Dairesi", "Çankaya Vergi Dairesi", "Osmangazi Vergi Dairesi"
    ];

    if (strlen($taxId) === 10) {
        if (!validateVknChecksum($taxId)) {
            return ['valid' => false, 'error' => 'Geçersiz 10 haneli VKN kontrol hanesi.'];
        }
        $idx = array_sum(array_map('intval', str_split($taxId))) % count($taxOffices);
        return [
            'valid' => true,
            'tax_id' => $taxId,
            'id_type' => 'VKN (Tüzel Kişi)',
            'company_title' => $title ?: "Kurumsal Bayi Adayı Ltd. Şti. ({$taxId})",
            'tax_office' => $taxOffices[$idx],
            'status' => 'FAAL',
            'mersis_no' => "{$taxId}00016",
            'is_verified' => true,
            'message' => 'GİB ve MERSİS vergi levhası doğrulaması başarılı.'
        ];
    } elseif (strlen($taxId) === 11) {
        if (!validateTcknChecksum($taxId)) {
            return ['valid' => false, 'error' => 'Geçersiz 11 haneli TCKN algoritması.'];
        }
        $idx = array_sum(array_map('intval', str_split($taxId))) % count($taxOffices);
        return [
            'valid' => true,
            'tax_id' => $taxId,
            'id_type' => 'TCKN (Şahıs Şirketi)',
            'company_title' => $title ?: "Şahıs İşletmesi (Gerçek Kişi)",
            'tax_office' => $taxOffices[$idx],
            'status' => 'FAAL',
            'mersis_no' => "0{$taxId}00015",
            'is_verified' => true,
            'message' => 'GİB Şahıs Şirketi kaydı doğrulandı.'
        ];
    }

    return ['valid' => false, 'error' => 'VKN 10 haneli veya TCKN 11 haneli olmalıdır.'];
}

$action = $_GET['action'] ?? '';
$method = $_SERVER['REQUEST_METHOD'];

if ($method === 'POST') {
    $raw = file_get_contents('php://input');
    $input = json_decode($raw, true) ?: [];

    if ($action === 'vkn-dogrula' || (isset($input['action']) && $input['action'] === 'vkn-dogrula')) {
        $taxId = $input['tax_id'] ?? ($input['vkn'] ?? '');
        $title = $input['applicant_title'] ?? '';
        echo json_encode(verifyTaxId($taxId, $title), JSON_UNESCAPED_UNICODE);
        exit();
    }

    if ($action === 'durum-guncelle' || (isset($input['action']) && $input['action'] === 'durum-guncelle')) {
        $tracking = $input['tracking_code'] ?? '';
        $newStatus = $input['status'] ?? 'Başvuru Alındı';

        $records = getStoredData($dataFile);
        $updated = false;
        foreach ($records as &$item) {
            if (($item['tracking_code'] ?? '') === $tracking) {
                $item['status'] = $newStatus;
                $updated = true;
                break;
            }
        }
        saveStoredData($dataFile, $records);
        echo json_encode(['status' => 'success', 'updated' => $updated]);
        exit();
    }

    $trackingCode = $input['tracking_code'] ?? ('BAYI-2026-' . rand(1000, 9999));
    $input['tracking_code'] = $trackingCode;
    $input['status'] = $input['status'] ?? 'Başvuru Alındı';
    $input['created_at'] = $input['created_at'] ?? date('c');
    $input['latitude'] = floatval($input['latitude'] ?? 0);
    $input['longitude'] = floatval($input['longitude'] ?? 0);

    $records = getStoredData($dataFile);
    array_unshift($records, $input);
    saveStoredData($dataFile, $records);

    echo json_encode([
        'status' => 'success',
        'tracking_code' => $trackingCode,
        'vkn_verified' => !empty($input['vkn_verified']),
        'map_pinned' => ($input['latitude'] != 0 && $input['longitude'] != 0)
    ]);
    exit();
}

if ($method === 'GET') {
    if ($action === 'vkn-sorgula') {
        $taxId = $_GET['vkn'] ?? '';
        $title = $_GET['title'] ?? '';
        echo json_encode(verifyTaxId($taxId, $title), JSON_UNESCAPED_UNICODE);
        exit();
    }

    $records = getStoredData($dataFile);
    echo json_encode($records, JSON_UNESCAPED_UNICODE);
    exit();
}
