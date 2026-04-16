param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$InvoicePath = "tests/fixtures/sample_invoice.txt",
    [string]$BillOfLadingPath = "tests/fixtures/sample_bill_of_lading.txt",
    [int]$PollIntervalSeconds = 5,
    [int]$MaxAttempts = 24
)

$invoiceFullPath = (Resolve-Path $InvoicePath).Path
$billFullPath = (Resolve-Path $BillOfLadingPath).Path

Write-Host "Checking API health at $BaseUrl ..."
$health = Invoke-RestMethod -Method Get -Uri "$BaseUrl/health"
Write-Host "Health status: $($health.status)"

Write-Host "Uploading sample documents..."
$uploadResponse = Invoke-RestMethod `
    -Method Post `
    -Uri "$BaseUrl/api/upload" `
    -Form @{
        invoice = Get-Item $invoiceFullPath
        bill_of_lading = Get-Item $billFullPath
    }

$jobId = $uploadResponse.job_id
Write-Host "Queued job: $jobId"

for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    Start-Sleep -Seconds $PollIntervalSeconds
    $result = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/results/$jobId"
    Write-Host "Attempt $attempt/$MaxAttempts - status: $($result.status)"

    if ($result.status -eq "completed") {
        $downloadTarget = Join-Path (Get-Location) "smoke-report-$jobId.md"
        Invoke-WebRequest -Method Get -Uri "$BaseUrl/api/results/$jobId/report" -OutFile $downloadTarget
        Write-Host "Report downloaded to $downloadTarget"
        $result | ConvertTo-Json -Depth 8
        exit 0
    }

    if ($result.status -eq "failed") {
        Write-Error "Job failed: $($result.error_message)"
        $result | ConvertTo-Json -Depth 8
        exit 1
    }
}

Write-Error "Timed out waiting for job completion."
exit 1
