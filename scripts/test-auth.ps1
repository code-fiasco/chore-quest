# Auth endpoint smoke test (uses curl.exe, not the PowerShell curl alias).
$ErrorActionPreference = "Stop"

$BaseUrl = if ($env:API_URL) { $env:API_URL } else { "http://localhost:8000" }
$CookieJar = Join-Path $PSScriptRoot "cookies.txt"

function Invoke-CurlJsonPost {
    param(
        [string]$Url,
        [string]$JsonBody
    )

    $bodyFile = Join-Path $env:TEMP ("chore-quest-{0}.json" -f ([guid]::NewGuid().ToString("N")))
    try {
        [System.IO.File]::WriteAllText($bodyFile, $JsonBody)
        curl.exe -s -c $CookieJar -b $CookieJar `
            -X POST $Url `
            -H "Content-Type: application/json" `
            -d "@$bodyFile"
    } finally {
        Remove-Item $bodyFile -ErrorAction SilentlyContinue
    }
}

Write-Host "Cookie jar: $CookieJar"
Write-Host "API base:   $BaseUrl"
Write-Host ""

$registerBody = (@{
    email        = "curl-test-$(Get-Date -Format 'yyyyMMddHHmmss')@example.com"
    password     = "Password1"
    display_name = "Curl Tester"
    avatar       = "Tiger"
} | ConvertTo-Json -Compress)

Write-Host "POST $BaseUrl/auth/register"
$registerResponse = Invoke-CurlJsonPost -Url "$BaseUrl/auth/register" -JsonBody $registerBody
Write-Host $registerResponse
Write-Host ""

if ($registerResponse -match "household already has two members") {
  if ($env:TEST_EMAIL -and $env:TEST_PASSWORD) {
    $loginBody = (@{
      email    = $env:TEST_EMAIL
      password = $env:TEST_PASSWORD
    } | ConvertTo-Json -Compress)

    Write-Host "Household full - POST $BaseUrl/auth/login (TEST_EMAIL / TEST_PASSWORD)"
    $loginResponse = Invoke-CurlJsonPost -Url "$BaseUrl/auth/login" -JsonBody $loginBody
    Write-Host $loginResponse
    Write-Host ""
  } else {
    Write-Host "Household full. Set TEST_EMAIL and TEST_PASSWORD to test login cookies, or clear users and re-run."
    Write-Host ""
  }
}

Write-Host "GET $BaseUrl/auth/avatars (cookies preserved)"
curl.exe -s -c $CookieJar -b $CookieJar "$BaseUrl/auth/avatars"
Write-Host ""

if (Select-String -Path $CookieJar -Pattern "access_token" -Quiet) {
    Write-Host "Cookie jar contains access_token."
} else {
    Write-Host "Warning: cookie jar has no access_token entry."
}
