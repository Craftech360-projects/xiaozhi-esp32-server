# PowerShell Script to Add Python to PATH
# Run this script as Administrator

$pythonPath = "C:\Users\rahul\AppData\Local\Programs\Python\Python311"
$pythonScriptsPath = "C:\Users\rahul\AppData\Local\Programs\Python\Python311\Scripts"

Write-Host "Adding Python to System PATH..." -ForegroundColor Green
Write-Host "Python Path: $pythonPath" -ForegroundColor Cyan
Write-Host "Scripts Path: $pythonScriptsPath" -ForegroundColor Cyan

# Get current PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

# Check if already in PATH
if ($currentPath -like "*$pythonPath*") {
    Write-Host "Python path already exists in PATH!" -ForegroundColor Yellow
} else {
    # Add Python to PATH
    $newPath = "$currentPath;$pythonPath"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "✅ Added Python to PATH" -ForegroundColor Green
}

# Check if Scripts already in PATH
if ($currentPath -like "*$pythonScriptsPath*") {
    Write-Host "Scripts path already exists in PATH!" -ForegroundColor Yellow
} else {
    # Add Scripts to PATH
    $newPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $newPath = "$newPath;$pythonScriptsPath"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "✅ Added Scripts to PATH" -ForegroundColor Green
}

Write-Host "`n✅ Done! Please restart your PowerShell terminal for changes to take effect." -ForegroundColor Green
Write-Host "After restarting, test with: python --version" -ForegroundColor Cyan
