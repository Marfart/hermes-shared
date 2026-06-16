Set UAC = CreateObject("Shell.Application")
UAC.ShellExecute "powershell.exe", "-NoProfile -ExecutionPolicy Bypass -Command ""& 'C:\Users\Admin\AppData\Local\Programs\Cua\cua-driver\bin\cua-driver.exe' autostart enable; & 'C:\Users\Admin\AppData\Local\Programs\Cua\cua-driver\bin\cua-driver.exe' autostart status; Start-Sleep 3""", "", "runas", 0
