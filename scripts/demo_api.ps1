param(
  [string]$BaseUrl = "http://localhost:8010",
  [string]$Org = "org-demo",
  [string]$Email = "gm@demo.com",
  [string]$Password = "StrongPass123"
)

$ErrorActionPreference = "Stop"

Write-Host "Register..."
$registerBody = @{
  email = $Email
  display_name = "GM"
  password = $Password
  organization_id = $Org
  role = "admin"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/auth/register" -ContentType "application/json" -Body $registerBody | Out-Null

Write-Host "Token..."
$tokenBody = @{
  email = $Email
  password = $Password
  organization_id = $Org
} | ConvertTo-Json

$token = (Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/auth/token" -ContentType "application/json" -Body $tokenBody).access_token
$headers = @{ Authorization = "Bearer $token" }

Write-Host "Create table..."
$table = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/tables" -Headers $headers -ContentType "application/json" -Body (@{ name = "Mesa PS1" } | ConvertTo-Json)
$tableId = $table.id
Write-Host "TableId: $tableId"

Write-Host "Add player..."
$player = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/tables/$tableId/players" -Headers $headers -ContentType "application/json" -Body (@{ display_name = "Luna" } | ConvertTo-Json)
$playerId = $player.id
Write-Host "PlayerId: $playerId"

Write-Host "Set player unavailable..."
Invoke-RestMethod -Method Patch -Uri "$BaseUrl/api/v1/tables/$tableId/players/$playerId" -Headers $headers -ContentType "application/json" -Body (@{ availability = "red" } | ConvertTo-Json) | Out-Null

Write-Host "Schedule sound event..."
$executeAt = (Get-Date).ToUniversalTime().AddSeconds(2).ToString("o")
$soundBody = @{
  table_id = $tableId
  session_id = "session-ps1"
  action = "play:battle"
  execute_at = $executeAt
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/v1/sound-events" -Headers $headers -ContentType "application/json" -Body $soundBody | Out-Null

Write-Host "Audit..."
$audit = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/v1/audit/$Org" -Headers $headers
$audit | Select-Object -First 5 | Format-Table

Write-Host "Done."

