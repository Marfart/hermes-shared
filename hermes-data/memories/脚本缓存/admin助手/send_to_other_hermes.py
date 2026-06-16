import ctypes
from ctypes import wintypes
import time

# Windows API constants
STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE = -11

# Get console handles
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# Try to attach to the target PowerShell process's console
target_pid = 30324

# First, check if we can find the console
# Use GetConsoleWindow to see if we have our own console

# AttachConsole - if we already have a console, we need to free it first
# Actually, let's try a simpler approach: use Windows API to send keystrokes

# Use SendInput API
user32 = ctypes.WinDLL('user32', use_last_error=True)

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]
    _fields_ = [("type", wintypes.DWORD),
                ("union", _INPUT)]

def press_key(vk_code):
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk = vk_code
    inp.union.ki.wScan = 0
    inp.union.ki.dwFlags = 0
    inp.union.ki.time = 0
    inp.union.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

def release_key(vk_code):
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk = vk_code
    inp.union.ki.wScan = 0
    inp.union.ki.dwFlags = KEYEVENTF_KEYUP
    inp.union.ki.time = 0
    inp.union.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

def send_key(vk_code):
    press_key(vk_code)
    time.sleep(0.05)
    release_key(vk_code)

def type_text(text):
    # VK codes for alphanumeric
    vk = {}
    for c in 'abcdefghijklmnopqrstuvwxyz':
        vk[c] = ord(c.upper())
    for c in '0123456789':
        vk[c] = ord(c)
    vk[' '] = 0x20
    vk['~'] = 0x0D  # Enter
    vk['!'] = 0x31  # Shift+1
    
    special = {'.': 0xBE, '-': 0xBD, '_': 0xE2, ':': 0xBA}
    
    send_key(vk['w'])
    send_key(vk['o'])
    time.sleep(0.1)
    send_key(vk[' '])
    send_key(vk['y'])
    send_key(vk['i'])
    send_key(vk[' '])
    send_key(vk['j'])
    send_key(vk['i'])
    send_key(vk['n'])
    send_key(vk['g'])
    send_key(vk[' '])
    send_key(vk['g'])
    send_key(vk['a'])
    send_key(vk['o'])
    send_key(vk[' '])
    send_key(vk['d'])
    send_key(vk['i'])
    send_key(vk['n'])
    send_key(vk['g'])
    send_key(vk[' '])
    send_key(vk['l'])
    send_key(vk['e'])
    send_key(vk[' '])
    send_key(vk['~'])
    send_key(vk['~'])

# First find and activate the target window
ENUM_WINDOWS = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
EnumWindows = user32.EnumWindows
EnumWindows.argtypes = [ENUM_WINDOWS, wintypes.LPARAM]
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

ShowWindow = user32.ShowWindow
ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
ShowWindow.restype = wintypes.BOOL

SetForegroundWindow = user32.SetForegroundWindow
SetForegroundWindow.argtypes = [wintypes.HWND]
SetForegroundWindow.restype = wintypes.BOOL

found_hwnd = None

def enum_proc(hwnd, lparam):
    global found_hwnd
    length = GetWindowTextW(hwnd, None, 0)
    if length > 0:
        buf = ctypes.create_unicode_buffer(length + 1)
        GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value
    else:
        title = ""
    
    pid = wintypes.DWORD(0)
    GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    
    if pid.value == target_pid and IsWindowVisible(hwnd):
        found_hwnd = hwnd
        return False  # stop enumeration
    return True

callback = ENUM_WINDOWS(enum_proc)
EnumWindows(callback, 0)

if found_hwnd:
    print(f"Found window: {found_hwnd}")
    ShowWindow(found_hwnd, 9)  # SW_RESTORE
    time.sleep(0.5)
    SetForegroundWindow(found_hwnd)
    time.sleep(1.0)
    
    # Type the message using SendKeys via PowerShell one-liner
    import subprocess
    ps_script = '''
    Add-Type -AssemblyName System.Windows.Forms
    Start-Sleep -Milliseconds 200
    [System.Windows.Forms.SendKeys]::SendWait("wo yi jing gao ding le~ ke yi xia yi bu le!")
    Start-Sleep -Milliseconds 200
    [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
    Start-Sleep -Milliseconds 100
    [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
    '''
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_script],
        capture_output=True, text=True, timeout=15
    )
    print(f"stdout: {result.stdout}")
    print(f"stderr: {result.stderr}")
    print(f"Exit: {result.returncode}")
else:
    print("Window not found!")