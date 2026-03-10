# Auto Push to GitHub Script
# This script commits and pushes changes to GitHub

param(
    [string]$commitMessage = "Auto commit: Updates to School Management System"
)

Write-Host "🔄 Starting auto-push to GitHub..." -ForegroundColor Cyan

# Activate virtual environment
& "$PSScriptRoot\venv\Scripts\Activate.ps1"

# Navigate to project directory
Set-Location $PSScriptRoot

# Check if there are changes
$status = git status --porcelain
if ($status) {
    Write-Host "📝 Changes detected. Committing..." -ForegroundColor Yellow
    
    # Add all changes
    git add .
    
    # Commit with message
    git commit -m $commitMessage
    
    # Push to GitHub
    Write-Host "⬆️  Pushing to GitHub..." -ForegroundColor Green
    git push origin main
    
    Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
} else {
    Write-Host "ℹ️  No changes to commit." -ForegroundColor Blue
}
