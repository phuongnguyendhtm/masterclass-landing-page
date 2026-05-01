# ===== AUTO-SYNC: Tu dong day code len GitHub khi ban sua file =====
# Chay script nay 1 lan -> no se theo doi moi thay doi va tu dong push len GitHub
# Nhan Ctrl+C de dung.

$folder = "D:\My_brain_antigravity\masterclass-landing-page"
$debounceSeconds = 30  # Cho 30 giay sau lan thay doi cuoi cung moi push (tranh push lien tuc)

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  AUTO-SYNC DANG CHAY - THEO DOI THAY DOI" -ForegroundColor Green  
Write-Host "  Thu muc: $folder" -ForegroundColor Gray
Write-Host "  Nhan Ctrl+C de dung" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $folder
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $false

# Ignore .git folder
$watcher.Filter = "*.*"

$lastPush = [DateTime]::MinValue
$hasChanges = $false

while ($true) {
    $result = $watcher.WaitForChanged([System.IO.WatcherChangeTypes]::All, 5000)
    
    if (-not $result.TimedOut) {
        # Skip .git folder changes
        if ($result.Name -like ".git*") { continue }
        
        $hasChanges = $true
        $lastChange = Get-Date
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Phat hien thay doi: $($result.Name)" -ForegroundColor Cyan
    }
    
    # Push if there are changes and enough time has passed
    if ($hasChanges) {
        $elapsed = (Get-Date) - $lastChange
        if ($elapsed.TotalSeconds -ge $debounceSeconds) {
            Write-Host ""
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Dang push len GitHub..." -ForegroundColor Yellow
            
            Set-Location $folder
            git add -A 2>$null
            $commitResult = git commit -m "Auto-sync: $(Get-Date -Format 'dd/MM/yyyy HH:mm')" 2>&1
            
            if ($commitResult -like "*nothing to commit*") {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Khong co thay doi moi." -ForegroundColor Gray
            } else {
                git push origin main 2>$null
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] DA PUSH THANH CONG! Website se cap nhat trong 30 giay." -ForegroundColor Green
            }
            
            $hasChanges = $false
            Write-Host ""
        }
    }
}
