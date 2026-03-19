$shell = New-Object -ComObject WScript.Shell
$shortcutPath = "C:\Users\trabajo ia\Desktop\RolPlay.ai.lnk"
if (Test-Path $shortcutPath) {
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.IconLocation = "C:\Users\trabajo ia\.gemini\antigravity\scratch\RolPlay.ai\assets\logo.ico"
    $shortcut.Save()
    Write-Host "Icon updated successfully!"
} else {
    Write-Error "Shortcut not found on desktop."
}
