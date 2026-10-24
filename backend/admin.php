<?php
// Issabel-authenticated administration; the monitoring gateway stays public.
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: SAMEORIGIN');
function answer($code, $body) { http_response_code($code); echo json_encode($body); exit; }
if (empty($_SERVER['HTTPS']) || $_SERVER['HTTPS'] === 'off') answer(403, array('error'=>'Yönetim için HTTPS gereklidir.'));
session_name('issabelSession');
session_start();
if (empty($_SESSION['issabel_user']) || empty($_SESSION['issabel_pass']))
    answer(401, array('error'=>'Önce Issabel yönetici hesabınızla giriş yapın.', 'login'=>'/index.php'));
set_include_path('/var/www/html/libs' . PATH_SEPARATOR . get_include_path());
require_once '/var/www/html/libs/misc.lib.php';
require_once '/var/www/html/configs/default.conf.php';
require_once '/var/www/html/libs/paloSantoDB.class.php';
require_once '/var/www/html/libs/paloSantoACL.class.php';
$db = new paloDB($arrConf['issabel_dsn']['acl']);
$acl = new paloACL($db);
$user = $_SESSION['issabel_user'];
$groups = $acl->getMembership($acl->getIdUser($user));
if (!$acl->authenticateUser($user, $_SESSION['issabel_pass']) || !is_array($groups) || !in_array('1', array_map('strval', array_values($groups)), true))
    answer(403, array('error'=>'Issabel administrator grubu yetkisi gerekir.'));
if (empty($_SESSION['hop_csrf'])) $_SESSION['hop_csrf'] = bin2hex(random_bytes(32));
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $status = @json_decode(@file_get_contents('/var/lib/hop-web-update/status.json'), true);
    answer(200, array('csrf'=>$_SESSION['hop_csrf'], 'status'=>$status ?: array('state'=>'idle','message'=>'Henüz web güncellemesi çalıştırılmadı.')));
}
if ($_SERVER['REQUEST_METHOD'] !== 'POST') answer(405, array('error'=>'Yöntem desteklenmiyor.'));
if (!isset($_POST['csrf']) || !hash_equals($_SESSION['hop_csrf'], $_POST['csrf']))
    answer(403, array('error'=>'Güvenlik doğrulaması başarısız. Sayfayı yenileyin.'));
if (time() < (isset($_SESSION['hop_retry_after']) ? $_SESSION['hop_retry_after'] : 0))
    answer(429, array('error'=>'Tekrar denemeden önce 10 saniye bekleyin.'));
$_SESSION['hop_retry_after'] = time() + 10;
if (empty($_POST['password']) || !$acl->authenticateUser($user, md5($_POST['password'])))
    answer(403, array('error'=>'Yönetici şifresi doğrulanamadı.'));
// No user-controlled argument is passed to the privileged command.
session_write_close();
exec('/usr/bin/sudo -n /usr/bin/systemctl --no-block start hop-web-update.service 2>/dev/null', $output, $code);
if ($code !== 0) answer(503, array('error'=>'Güncelleme servisi başlatılamadı. Sunucu kurulumunu kontrol edin.'));
answer(202, array('message'=>'Güncelleme isteği alındı. İşlem durumunu bu pencereden izleyin.'));
