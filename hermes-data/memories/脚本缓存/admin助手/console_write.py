"""
Write directly to the PowerShell console's input buffer of the target process.
This doesn't need window focus - it injects keystrokes into the console input queue.
"""
import ctypes
from ctypes import wintypes
import time

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# Constants
STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE = -11

# Console input record types
KEY_EVENT = 0x0001
RIGHT_ALT_PRESSED = 0x0001
LEFT_ALT_PRESSED = 0x0002
RIGHT_CTRL_PRESSED = 0x0004
LEFT_CTRL_PRESSED = 0x0008
SHIFT_PRESSED = 0x0010
CAPSLOCK_ON = 0x0080

VK_RETURN = 0x0D

class COORD(ctypes.Structure):
    _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]

class KEY_EVENT_RECORD(ctypes.Structure):
    _fields_ = [
        ("bKeyDown", wintypes.BOOL),
        ("wRepeatCount", wintypes.WORD),
        ("wVirtualKeyCode", wintypes.WORD),
        ("wVirtualScanCode", wintypes.WORD),
        ("uChar", wintypes.WCHAR),
        ("dwControlKeyState", wintypes.DWORD)
    ]

class MOUSE_EVENT_RECORD(ctypes.Structure):
    _fields_ = [
        ("dwMousePosition", COORD),
        ("dwButtonState", wintypes.DWORD),
        ("dwControlKeyState", wintypes.DWORD),
        ("dwEventFlags", wintypes.DWORD)
    ]

class WINDOW_BUFFER_SIZE_RECORD(ctypes.Structure):
    _fields_ = [("dwSize", COORD)]

class INPUT_RECORD(ctypes.Structure):
    class _Event(ctypes.Union):
        _fields_ = [
            ("KeyEvent", KEY_EVENT_RECORD),
            ("MouseEvent", MOUSE_EVENT_RECORD),
            ("WindowBufferSizeEvent", WINDOW_BUFFER_SIZE_RECORD),
        ]
    _fields_ = [
        ("EventType", wintypes.WORD),
        ("Event", _Event)
    ]

# Get target process console
target_pid = 30324

# Use AttachConsole to attach to the target process console
FreeConsole = kernel32.FreeConsole
FreeConsole.restype = wintypes.BOOL

AttachConsole = kernel32.AttachConsole
AttachConsole.argtypes = [wintypes.DWORD]
AttachConsole.restype = wintypes.BOOL

# First free our own console
FreeConsole()

# Try to attach to the target process console
result = AttachConsole(target_pid)
if not result:
    error = ctypes.get_last_error()
    print(f"AttachConsole failed with error {error}")
    
    # Error 5 = Access denied, 87 = wrong param, 6 = invalid handle
    if error == 5:
        print("Access denied - need admin or different method")
    exit(1)

print(f"Attached to console of PID {target_pid}")

# Get console input handle
GetStdHandle = kernel32.GetStdHandle
GetStdHandle.argtypes = [wintypes.DWORD]
GetStdHandle.restype = wintypes.HANDLE

hStdin = GetStdHandle(STD_INPUT_HANDLE)
print(f"Input handle: {hStdin}")

if hStdin is None or hStdin == -1 or hStdin == 0:
    print("Could not get stdin handle")
    FreeConsole()
    exit(1)

# Function to write a key event
WriteConsoleInputW = kernel32.WriteConsoleInputW
WriteConsoleInputW.argtypes = [wintypes.HANDLE, ctypes.POINTER(INPUT_RECORD), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
WriteConsoleInputW.restype = wintypes.BOOL

def write_key(char, key_down=True):
    """Write a single character key event"""
    record = INPUT_RECORD()
    record.EventType = KEY_EVENT
    record.Event.KeyEvent.bKeyDown = key_down
    record.Event.KeyEvent.wRepeatCount = 1
    record.Event.KeyEvent.wVirtualKeyCode = 0
    record.Event.KeyEvent.wVirtualScanCode = 0
    record.Event.KeyEvent.uChar = char
    record.Event.KeyEvent.dwControlKeyState = 0
    
    written = wintypes.DWORD(0)
    result = WriteConsoleInputW(hStdin, ctypes.byref(record), 1, ctypes.byref(written))
    if not result:
        error = ctypes.get_last_error()
        print(f"WriteConsoleInputW failed for '{char}': error {error}")
        return False
    return True

def write_enter():
    """Write an Enter key"""
    record = INPUT_RECORD()
    record.EventType = KEY_EVENT
    record.Event.KeyEvent.bKeyDown = True
    record.Event.KeyEvent.wRepeatCount = 1
    record.Event.KeyEvent.wVirtualKeyCode = VK_RETURN
    record.Event.KeyEvent.wVirtualScanCode = 0
    record.Event.KeyEvent.uChar = '\r'
    record.Event.KeyEvent.dwControlKeyState = 0
    written = wintypes.DWORD(0)
    WriteConsoleInputW(hStdin, ctypes.byref(record), 1, ctypes.byref(written))
    
    record.Event.KeyEvent.bKeyDown = False
    written = wintypes.DWORD(0)
    WriteConsoleInputW(hStdin, ctypes.byref(record), 1, ctypes.byref(written))

# Type the message character by character
message = "我已经搞定了！可以下一步了~\r"
for ch in message:
    write_key(ch)
    time.sleep(0.05)
    write_key(ch, key_down=False)
    time.sleep(0.02)

# Send Enter
write_enter()
time.sleep(0.1)
write_enter()

print("Message sent to console input buffer!")

# Detach from the target console
FreeConsole()
print("Detached from target console")