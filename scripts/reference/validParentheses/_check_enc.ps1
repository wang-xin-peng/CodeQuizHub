$path = "scripts\valid_parentheses_payload.json"
$bytes = [System.IO.File]::ReadAllBytes($path)
$first12 = $bytes[0..11]
Write-Host ("First 12 bytes (hex): " + (($first12 | ForEach-Object { $_.ToString("X2") }) -join " "))
$hasBom = ($bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
Write-Host ("Has UTF-8 BOM: " + $hasBom)
$content = [System.Text.Encoding]::UTF8.GetString($bytes)
Write-Host ("Title found: '" + ($content -match '"title"\s*:\s*"([^"]+)"' ? $matches[1] : "NOT FOUND") + "'")
