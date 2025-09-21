# Script PowerShell pour lancer frontend et backend
Write-Host "🎯 Starting Weather AI - Full Stack" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Yellow

# Démarrer le backend en arrière-plan
Write-Host "🚀 Starting Backend Services..." -ForegroundColor Blue
$backend = Start-Process -FilePath "python" -ArgumentList "start.py", "--mode", "backend" -PassThru

# Attendre que le backend démarre
Write-Host "⏳ Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Démarrer le frontend en arrière-plan
Write-Host "🌐 Starting Frontend..." -ForegroundColor Blue
$frontend = Start-Process -FilePath "npm" -ArgumentList "start" -WorkingDirectory "frontend" -PassThru

Write-Host ""
Write-Host "✅ Both services started!" -ForegroundColor Green
Write-Host "📋 URLs:" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "🛑 Press Ctrl+C to stop all services" -ForegroundColor Red

try {
    # Attendre que les processus se terminent
    $backend.WaitForExit()
    $frontend.WaitForExit()
} catch {
    Write-Host "🛑 Stopping all services..." -ForegroundColor Red
    $backend.Kill()
    $frontend.Kill()
    Write-Host "✅ All services stopped!" -ForegroundColor Green
}
