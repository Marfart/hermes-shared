"""
Use Windows messages (WM_CHAR, WM_KEYDOWN) to send text to the target console window.
This is the most reliable way to inject text into another process's console.
"""
import ctypes
from ctypes import wintypes
import time

user32 = ctypes.WinDLL('user32', use_last_error=True)

# Constants
WM_CHAR = 0x0102
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
VK_RETURN = 0x0D

# Find the target window
EnumWindows = user32.EnumWindows
EnumWindows.argtypes = [ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM), wintypes.LPARAM]
EnumWindows.restype = wintypes.BOOL

GetWindowTextW = user32.GetWindowTextW
GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
GetWindowTextW.restype = ctypes.c_int

GetWindowThreadProcessId = user32.GetWindowThreadProcessId
GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
GetWindowThreadProcessId.restype = wintypes.DWORD

IsWindowVisible = user32.IsWindowVisible
IsWindowVisible.argtypes = [wintypes.HWND]
IsWindowVisible.restype = wintypes.BOOL

PostMessageW = user32.PostMessageW
PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
PostMessageW.restype = wintypes.BOOL

ShowWindow = user32.ShowWindow
ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
ShowWindow.restype = wintypes.BOOL

SetForegroundWindow = user32.SetForegroundWindow
SetForegroundWindow.argtypes = [wintypes.HWND]
SetForegroundWindow.restype = wintypes.BOOL

# First find the console window that belongs to PID 30324
found_hwnd = None

def enum_proc(hwnd, lparam):
    global found_hwnd
    length = GetWindowTextW(hwnd, None, 0)
    buf = ctypes.create_unicode_buffer(length + 1) if length > 0 else None
    if buf:
        GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value
    else:
        title = ""
    
    pid = wintypes.DWORD(0)
    GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    
    if pid.value == 30324 and IsWindowVisible(hwnd):
        global found_hwnd
        found_hwnd = hwnd
        print(f"Found window: hwnd={hwnd}, title='{title}'")
        return False
    return True

callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
callback = callback_type(enum_proc)
EnumWindows(callback, 0)

if found_hwnd is None:
    print("Window not found")
    exit(1)

# First, let's try clicking on the OTHER visible PowerShell window
# We found earlier there were 2 PowerShell windows: one empty title (PID 30324) and 2 titled "Windows PowerShell" (PID 13812)
# The empty title one IS our target

# Let's enumerate ALL visible windows to find the actual console window
# PowerShell actually uses a console window hosted by conhost.exe, not by powershell.exe
# We need to find the conhost.exe window

# Let's look for ALL console-related windows
all_windows = []
def enum_all(hwnd, lparam):
    length = GetWindowTextW(hwnd, None, 0)
    buf = ctypes.create_unicode_buffer(length + 1) if length > 0 else ctypes.create_unicode_buffer(1)
    GetWindowTextW(hwnd, buf, length + 1 if length > 0 else 1)
    title = buf.value
    
    pid = wintypes.DWORD(0)
    GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    
    if IsWindowVisible(hwnd) and title:
        all_windows.append((hwnd, pid.value, title))
    return True

callback_all = callback_type(enum_all)
EnumWindows(callback_all, 0)

# Look for the console host window for PID 30324
# conhost.exe's child of powershell.exe would have a different PID
# Let's find the actual console by checking all windows that might be console windows
print("\nAll visible windows with titles:")
for h, pid, title in all_windows:
    print(f"  HWND={h}, PID={pid}, Title='{title}'")
    if title.strip() == "":
        print(f"    *** Empty title, could be our target ***")

# The window with HWND 15141942 has empty title, PID 30324
# Let's send WM_CHAR to it directly
target_hwnd = found_hwnd  # 15141942

print(f"\nSending message to HWND {target_hwnd}...")

# Bring it to front so it processes messages
ShowWindow(target_hwnd, 9)
time.sleep(0.3)
SetForegroundWindow(target_hwnd)
time.sleep(0.5)

# Send the message character by character using WM_CHAR
message = "wo yi jing gao ding le~ ke yi xia yi bu le!"
for ch in message:
    PostMessageW(target_hwnd, WM_CHAR, ord(ch), 0)
    time.sleep(0.03)

# Send Enter twice
PostMessageW(target_hwnd, WM_CHAR, ord('\r'), 0)
time.sleep(0.1)
PostMessageW(target_hwnd, WM_CHAR, ord('\n'), 0)
time.sleep(0.1)
PostMessageW(target_hwnd, WM_CHAR, ord('\r'), 0)
time.sleep(0.1)
PostMessageW(target_hwnd, WM_CHAR, ord('\n'), 0)

print("Message sent via WM_CHAR!")
print(f"Sent: '{message}'")