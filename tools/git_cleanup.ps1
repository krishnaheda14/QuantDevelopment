# Git Cleanup Script
# Removes accidentally staged node_modules and other large directories from git

Write-Host "=== Git Cleanup Script ===" -ForegroundColor Cyan
Write-Host ""

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "❌ Not a git repository. Please run this from the project root." -ForegroundColor Red
    exit 1
}

Write-Host "🔍 Checking git status..." -ForegroundColor Yellow
git status

Write-Host ""
Write-Host "📋 Steps to remove node_modules from git:" -ForegroundColor Green
Write-Host ""
Write-Host "1️⃣  Remove node_modules from staging area (if staged)" -ForegroundColor Cyan
Write-Host "   git rm -r --cached frontend/node_modules" -ForegroundColor White
Write-Host ""
Write-Host "2️⃣  Remove from git history (if already committed)" -ForegroundColor Cyan
Write-Host "   git filter-branch --force --index-filter 'git rm -r --cached --ignore-unmatch frontend/node_modules' --prune-empty --tag-name-filter cat -- --all" -ForegroundColor White
Write-Host ""
Write-Host "3️⃣  Ensure .gitignore is correct" -ForegroundColor Cyan
Write-Host "   Already updated with node_modules/ exclusions" -ForegroundColor White
Write-Host ""
Write-Host "4️⃣  Force push (if already pushed to remote)" -ForegroundColor Cyan
Write-Host "   git push origin --force --all" -ForegroundColor White
Write-Host ""

$response = Read-Host "Do you want to remove node_modules from git now? (y/n)"

if ($response -eq 'y' -or $response -eq 'Y') {
    Write-Host ""
    Write-Host "🧹 Removing node_modules from git..." -ForegroundColor Yellow
    
    # Remove from staging/index
    Write-Host "   Removing from staging area..." -ForegroundColor Cyan
    git rm -r --cached frontend/node_modules 2>$null
    git rm -r --cached node_modules 2>$null
    
    Write-Host "   ✓ Removed from staging" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "📊 New git status:" -ForegroundColor Yellow
    git status
    
    Write-Host ""
    Write-Host "💡 Next steps:" -ForegroundColor Green
    Write-Host "   1. Review changes with: git status" -ForegroundColor White
    Write-Host "   2. Commit the changes: git commit -m 'Remove node_modules from git tracking'" -ForegroundColor White
    Write-Host "   3. Push to remote (if applicable): git push origin main" -ForegroundColor White
    Write-Host ""
    Write-Host "⚠️  If node_modules was already committed in history:" -ForegroundColor Yellow
    Write-Host "   Run the filter-branch command above to remove from history" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "ℹ️  No changes made. Run the commands manually when ready." -ForegroundColor Blue
}

Write-Host ""
Write-Host "✅ Cleanup script complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Additional cleanup commands:" -ForegroundColor Yellow
Write-Host "   Remove other large files:" -ForegroundColor Cyan
Write-Host "   git rm -r --cached data/*.db" -ForegroundColor White
Write-Host "   git rm -r --cached .venv/" -ForegroundColor White
Write-Host "   git rm -r --cached frontend/dist/" -ForegroundColor White
Write-Host ""
