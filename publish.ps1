param(
    [string]$Repository = "https://github.com/AlexanderP101/Pavlov-A.V-pr-2-Configuration-management.git",
    [string]$Branch = "variant18-fixed"
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path .git)) {
    throw "Extract the ZIP with its .git folder. Do not use browser file upload."
}
git --version
if ($LASTEXITCODE -ne 0) { throw "Install Git for Windows first." }
py -B scripts/check_style.py
if ($LASTEXITCODE -ne 0) { throw "Repository check failed. Nothing was pushed." }
git push $Repository "HEAD:refs/heads/$Branch"
if ($LASTEXITCODE -ne 0) { throw "Push failed. Check GitHub sign-in and branch name." }
Write-Host "Submitted branch: $Branch"
Write-Host "Enter this branch name in the checker, alongside the repository URL."
