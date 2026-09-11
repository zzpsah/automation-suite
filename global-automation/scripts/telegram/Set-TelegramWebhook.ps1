param(
    [Parameter(Mandatory=$true)] [string]$BotToken,
    [Parameter(Mandatory=$true)] [string]$WebhookUrl,
    [Parameter(Mandatory=$false)] [string]$SecretToken = ''
)

$ErrorActionPreference = 'Stop'

$body = @{ url = $WebhookUrl }
if ($SecretToken) { $body.secret_token = $SecretToken }

$result = Invoke-RestMethod -Method Post `
    -Uri "https://api.telegram.org/bot$BotToken/setWebhook" `
    -Body $body

if (-not $result.ok) { throw "Telegram setWebhook failed: $($result.description)" }
Write-Host "Webhook configured: $WebhookUrl"
