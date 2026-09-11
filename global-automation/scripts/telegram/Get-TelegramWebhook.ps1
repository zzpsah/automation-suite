param(
    [Parameter(Mandatory=$true)] [string]$BotToken
)

$ErrorActionPreference = 'Stop'

$me = Invoke-RestMethod -Method Get -Uri "https://api.telegram.org/bot$BotToken/getMe"
$info = Invoke-RestMethod -Method Get -Uri "https://api.telegram.org/bot$BotToken/getWebhookInfo"

Write-Host "Bot: @$($me.result.username) (id $($me.result.id))"
Write-Host "Webhook URL: $($info.result.url)"
Write-Host "Pending updates: $($info.result.pending_update_count)"
if ($info.result.last_error_message) {
    Write-Host "Last webhook error: $($info.result.last_error_message)"
} else {
    Write-Host "Last webhook error: none"
}
