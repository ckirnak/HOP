<?php
// Public read-only HOP gateway; AMI remains restricted to localhost.
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: SAMEORIGIN');
if (isset($_GET['events'])) {
    ini_set('zlib.output_compression', '0');
    set_time_limit(0);
    while (ob_get_level()) { ob_end_clean(); }
    $context = stream_context_create(array('http'=>array('timeout'=>15)));
    $stream = @fopen('http://127.0.0.1:8765/events', 'r', false, $context);
    if (!$stream) { http_response_code(503); exit; }
    header('Content-Type: text/event-stream; charset=utf-8');
    header('Cache-Control: no-cache, no-store');
    header('X-Accel-Buffering: no');
    echo ':' . str_repeat(' ', 2048) . "\n\nretry: 1500\n\n";
    flush();
    $until = microtime(true) + 50;
    while (!connection_aborted() && microtime(true) < $until && !feof($stream)) {
        $line = fgets($stream);
        if ($line === false) { break; }
        echo $line;
        if (trim($line) === '') { flush(); }
    }
    fclose($stream);
    if (!connection_aborted()) {
        echo "event: reconnect\ndata: {}\n\n";
        flush();
    }
    exit;
}
if (isset($_GET['state'])) {
    header('Content-Type: application/json; charset=utf-8');
    $context = stream_context_create(array('http'=>array('timeout'=>4)));
    $body = @file_get_contents('http://127.0.0.1:8765/state', false, $context);
    if ($body === false) {
        http_response_code(503);
        echo json_encode(array('connected'=>false,'error'=>'HOP bağlantı servisine erişilemiyor.'));
    } else {
        echo $body;
    }
    exit;
}
header('Content-Type: text/html; charset=utf-8');
readfile('/opt/hop/live.html');
