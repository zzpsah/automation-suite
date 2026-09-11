param(
    [Parameter(Mandatory=$true)] [string]$SupabaseUrl,
    [Parameter(Mandatory=$true)] [string]$ServiceRoleKey
)

$ErrorActionPreference = 'Stop'
$base = $SupabaseUrl.TrimEnd('/')
$headers = @{
    apikey = $ServiceRoleKey
    Authorization = "Bearer $ServiceRoleKey"
}

$uri = "$base/rest/v1/documents?select=id&limit=1"
$response = Invoke-RestMethod -Method Get -Uri $uri -Headers $headers
Write-Host "Supabase REST API: OK"
Write-Host "documents endpoint reachable; returned $(@($response).Count) row(s)."
