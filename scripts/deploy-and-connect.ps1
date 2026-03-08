# Deploy backend to Railway and connect Vercel to it.
# Prereq: Run once in a terminal where browser can open: npx @railway/cli login
# If you already created a project from GitHub in Railway, run: npx @railway/cli link (select that project)
# Then run this script from repo root: .\scripts\deploy-and-connect.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "Checking Railway login..."
$railwayWho = npx --yes @railway/cli whoami 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Railway not logged in. Run this in your terminal (browser will open):"
    Write-Host "  npx @railway/cli login"
    Write-Host "Then run this script again."
    exit 1
}
Write-Host "Railway: $railwayWho"

Write-Host "`nDeploying to Railway (railway up)..."
npx --yes @railway/cli up 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "Railway deploy failed."; exit 1 }
Write-Host "Deploy triggered. Waiting 30s for build..."
Start-Sleep -Seconds 30

Write-Host "`nGet your Railway public URL:"
Write-Host "  1. Open: https://railway.app/dashboard"
Write-Host "  2. Open your project -> your service -> Settings -> Networking"
Write-Host "  3. If no domain yet, click 'Generate Domain'"
Write-Host "  4. Copy the URL (e.g. https://xxx.up.railway.app)"
$backendUrl = Read-Host "`nPaste the Railway backend URL (no trailing slash)"
$backendUrl = $backendUrl.Trim().TrimEnd('/')
if (-not $backendUrl) { Write-Host "No URL entered. Exiting."; exit 1 }

Write-Host "`nAdding BACKEND_URL to Vercel and redeploying..."
echo $backendUrl | npx --yes vercel env add BACKEND_URL production --force 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Vercel env add failed. Add manually: Vercel -> Project -> Settings -> Environment Variables -> BACKEND_URL = $backendUrl"
} else {
    Write-Host "Redeploying Vercel frontend..."
    npx --yes vercel --prod --yes 2>&1
}
Write-Host "`nDone. Open https://rag-mutual-fund-faq.vercel.app and try a chat."
