$scripts = @(
    "c:\Users\iRepair\Downloads\database backup\crawler\discover.py",
    "c:\Users\iRepair\Downloads\database backup\crawler\fetch.py",
    "c:\Users\iRepair\Downloads\database backup\crawler\parse.py",
    "c:\Users\iRepair\Downloads\database backup\etl\clean.py",
    "c:\Users\iRepair\Downloads\database backup\etl\load.py",
    "c:\Users\iRepair\Downloads\database backup\etl\seed_users.py",
    "c:\Users\iRepair\Downloads\database backup\etl\export_csv.py",
    "c:\Users\iRepair\Downloads\database backup\validation\validate.py"
)

foreach ($script in $scripts) {
    $name = Split-Path $script -Leaf
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Running: $name" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    python $script
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[PASS] $name exited successfully." -ForegroundColor Green
    } else {
        Write-Host "[FAIL] $name exited with code $LASTEXITCODE." -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  All Milestone 2 scripts completed." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

