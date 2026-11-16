# Windows window/session diagnosis

## When to Use
Use this when a Windows desktop capture omits an application that is known to be running. Do not infer Session 0 or virtual-desktop isolation from `list_apps`/`list_windows` alone.

## 1. Compare process user and session

In PowerShell, substitute the process IDs for the target application, Hermes, and the CUA driver:

```powershell
Get-Process -Id <targetPid>,<hermesPid>,<cuaPid> |
  Select-Object Name,Id,SessionId,MainWindowHandle,MainWindowTitle,Responding

$p = Get-WmiObject Win32_Process -Filter "ProcessId=<targetPid>"
$o = $p.GetOwner()
[pscustomobject]@{ User = ($o.Domain + "\\" + $o.User); SessionId = $p.SessionId }
```

A target with the same interactive user/session as Hermes and CUA is not explained by a Session 0 mismatch; continue by inspecting its window state. `MainWindowHandle=0` means there is no discoverable main window, not proof that the process is stopped.

## 2. Inspect HWND state

With the target's `MainWindowHandle` as an integer, query visibility, minimization, and DWM cloaking. This Python standard-library probe needs no added packages:

```powershell
python -c "import ctypes as c; h=c.c_void_p(<HWND>); u=c.WinDLL('user32'); d=c.WinDLL('dwmapi'); v=c.c_int(); u.IsWindow.argtypes=[c.c_void_p]; u.IsWindow.restype=c.c_bool; u.IsWindowVisible.argtypes=[c.c_void_p]; u.IsWindowVisible.restype=c.c_bool; u.IsIconic.argtypes=[c.c_void_p]; u.IsIconic.restype=c.c_bool; d.DwmGetWindowAttribute.argtypes=[c.c_void_p,c.c_uint,c.POINTER(c.c_int),c.c_uint]; d.DwmGetWindowAttribute.restype=c.c_long; hr=d.DwmGetWindowAttribute(h,14,c.byref(v),4); print({'is_window':u.IsWindow(h),'visible':u.IsWindowVisible(h),'minimized':u.IsIconic(h),'dwm_cloaked':v.value,'dwm_hresult':hr})"
```

Interpret the returned API values rather than relying on the accessibility list: `minimized=True` identifies a minimized window; `dwm_cloaked=0` means DWM did not report it as cloaked. Do not claim a virtual-desktop cause solely from either result.

## 3. Restore only with authorization

When the user has asked to locate/activate the existing app, restore its current HWND without terminating or restarting the process, then verify via a new `computer_use(action="capture", app="...")`:

```powershell
python -c "import ctypes as c,time; h=c.c_void_p(<HWND>); u=c.WinDLL('user32'); print({'restore':u.ShowWindow(h,9),'foreground':u.SetForegroundWindow(h)}); time.sleep(0.5); u.IsIconic.argtypes=[c.c_void_p]; u.IsIconic.restype=c.c_bool; print({'minimized_after':u.IsIconic(h)})"
```

`ShowWindow(..., 9)` restores the existing window. Only call `SetForegroundWindow` when bringing the UI forward was authorized; afterward, capture again to confirm the app is actually accessible. If user/session comparison or the restored capture still shows a genuine access boundary, report it and stop rather than changing security/session settings.