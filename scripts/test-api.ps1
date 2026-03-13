# Test API pushes to the OpenClaw display (server must be running on localhost:8080).
# Usage: .\scripts\test-api.ps1

$base = "http://localhost:8080"

Write-Host "1. GET /status"
try {
    $r = Invoke-RestMethod -Uri "$base/status" -Method Get
    $r | ConvertTo-Json
} catch { Write-Host "Error: $_" }

Write-Host "`n2. POST /panels (news + reminder)"
try {
    $body = '{"panels": [{"title": "NEWS", "items": ["Test headline: Display API is working."]}, {"title": "NEXT", "items": ["Call Sam at 3:15 PM"]}]}'
    $r = Invoke-RestMethod -Uri "$base/panels" -Method Post -ContentType "application/json" -Body $body
    $r | ConvertTo-Json
} catch { Write-Host "Error: $_" }

Write-Host "`n3. POST /request → thinking"
Invoke-RestMethod -Uri "$base/request" -Method Post -ContentType "application/json" -Body '{"phase": "thinking"}' | ConvertTo-Json
Start-Sleep -Seconds 2

Write-Host "`n4. POST /request → speaking"
Invoke-RestMethod -Uri "$base/request" -Method Post -ContentType "application/json" -Body '{"phase": "speaking"}' | ConvertTo-Json
Start-Sleep -Seconds 2

Write-Host "`n5. POST /request → reading (with response text)"
$readingBody = '{"phase": "reading", "response_text": "Good morning! The display API is working. You should see this text in the response panel, scrolling slowly. Have a great day."}'
Invoke-RestMethod -Uri "$base/request" -Method Post -ContentType "application/json" -Body $readingBody | ConvertTo-Json
Start-Sleep -Seconds 5

Write-Host "`n6. POST /request → done (back to idle)"
Invoke-RestMethod -Uri "$base/request" -Method Post -ContentType "application/json" -Body '{"phase": "done"}' | ConvertTo-Json

Write-Host "`nDone. Check the display window."
