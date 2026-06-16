# PowerShell via git-bash: Variable Expansion Workaround

## The Problem

When running PowerShell commands inline through git-bash:
```
powershell -Command "Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPClass -eq 'Camera' }"
```
git-bash interprets `$_.PNPClass` as a bash variable `$_` followed by `.PNPClass`, expanding it to something like `C:\Users\Admin.PNPClass`. This creates a PowerShell parse error.

## The Fix

**Always write PowerShell scripts to a file first, then execute with `-File`:**

```bash
# BAD — will break
powershell -c "Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPClass -eq 'Camera' }"

# GOOD — write file then execute
echo '$cameras = Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPClass -eq "Camera" }
$cameras | Format-List' > /tmp/scan.ps1
powershell -ExecutionPolicy Bypass -File /tmp/scan.ps1
```

Or use `write_file` to create the `.ps1` file, then:
```
powershell -ExecutionPolicy Bypass -File "C:\path\to\script.ps1"
```

## Also Works: Single-quote the entire PowerShell argument
In bash, single quotes prevent variable expansion:
```
powershell -Command 'Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPClass -eq "Camera" }'
```
But this fails if the command contains single quotes itself.
