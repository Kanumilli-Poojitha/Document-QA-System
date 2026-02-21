# Smoke test for Document QA backend
# Requires curl.exe (Windows) and PowerShell

$base = "http://localhost:8000"

Write-Host "1) Checking /health..."
try {
    $health = Invoke-RestMethod -Uri "$base/health" -Method Get -ErrorAction Stop
    if ($health.status -eq 'ok') { Write-Host "  /health OK" }
    else { Write-Host "  /health returned unexpected body:"; $health; exit 1 }
} catch {
    Write-Host "  /health failed: $_"; exit 1
}

if (-Not (Test-Path "sample.txt")) {
    Write-Host "sample.txt not found in repo root. Create a sample.txt and re-run."; exit 1
}

Write-Host "2) Uploading sample.txt to /upload..."
$uploadResp = & curl.exe -s -X POST "$base/upload" -F "file=@sample.txt"
if (-Not $uploadResp) { Write-Host "  Upload failed or empty response"; exit 1 }
try {
    $uploadJson = $uploadResp | ConvertFrom-Json
    $docId = $uploadJson.document_id
    Write-Host "  Upload accepted. document_id=$docId"
} catch {
    Write-Host "  Upload returned non-JSON: $uploadResp"; exit 1
}

Write-Host "3) Polling document status..."
$maxAttempts = 12
$attempt = 0
$status = $null
while ($attempt -lt $maxAttempts) {
    Start-Sleep -Seconds 1
    try {
        $stat = Invoke-RestMethod -Uri "$base/documents/$docId/status" -Method Get -ErrorAction Stop
        $status = $stat.status
        Write-Host "  Attempt $($attempt+1): status=$status"
        if ($status -eq 'completed') { break }
        if ($status -eq 'failed') { Write-Host "  Document processing failed"; exit 1 }
    } catch {
        Write-Host "  Status check failed: $_"; exit 1
    }
    $attempt++
}
if ($status -ne 'completed') { Write-Host "  Document did not complete in time"; exit 1 }

Write-Host "4) Retrieving chunks..."
try {
    $chunksResp = Invoke-RestMethod -Uri "$base/documents/$docId/chunks" -Method Get -ErrorAction Stop
    if ($chunksResp.chunks -and $chunksResp.chunks.Count -gt 0) {
        Write-Host "  Retrieved $($chunksResp.chunks.Count) chunks"
    } else {
        Write-Host "  No chunks found"; exit 1
    }
} catch {
    Write-Host "  Failed to get chunks: $_"; exit 1
}

Write-Host "5) Asking a simple question via /ask..."
$question = "What is the capital of India?"
$payload = @{ session_id = $null; document_ids = @($docId); question = $question } | ConvertTo-Json -Depth 4
try {
    $askResp = Invoke-RestMethod -Uri "$base/ask" -Method Post -Body $payload -ContentType 'application/json' -ErrorAction Stop
    if ($askResp.answer -and $askResp.source_chunks) {
        Write-Host "  /ask returned answer (length: $($askResp.answer.Length)) and $($askResp.source_chunks.Count) source_chunks"
        $sessionId = $askResp.session_id
    } else {
        Write-Host "  /ask returned unexpected body:"; $askResp | ConvertTo-Json; exit 1
    }
} catch {
    Write-Host "  /ask failed: $_"; exit 1
}

Write-Host "6) Fetching session history..."
try {
    $hist = Invoke-RestMethod -Uri "$base/session/$sessionId" -Method Get -ErrorAction Stop
    if ($hist.history -and $hist.history.Count -ge 2) {
        Write-Host "  Session history has $($hist.history.Count) messages"
    } else {
        Write-Host "  Session history missing or small:"; $hist | ConvertTo-Json; exit 1
    }
} catch {
    Write-Host "  Session fetch failed: $_"; exit 1
}

Write-Host "7) Exporting conversation as PDF..."
try {
    $outFile = "session_$sessionId.pdf"
    Invoke-WebRequest -Uri "$base/session/$sessionId/export" -OutFile $outFile -ErrorAction Stop
    if (Test-Path $outFile) { Write-Host "  Exported PDF to $outFile" } else { Write-Host "  Export failed"; exit 1 }
} catch {
    Write-Host "  Export failed: $_"; exit 1
}

Write-Host "SMOKE TESTS PASSED"
exit 0
