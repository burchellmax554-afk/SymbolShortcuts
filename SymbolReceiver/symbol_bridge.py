# SymbolReceiver.py
# Live mirror of MCU symbol state taht sends input to text apps
# UI (two lines, ANSI redraw):
#   Symbol Library: π [∑] µ Ω ∫
#   Last Sent Symbol Symbol: —

import serial  # For connection to virtual port
import sys     # For the terminal UI
import time    # For recording response times and delaying a loop
import pyperclip  # For getting the characters to the device
import pyautogui # For getting the characters to the device
import subprocess # For debugging and keystroke emulation
import platform # For cross-platform functionality

# In addition, the following dependencies are required:
# Pyserial 
# Pyperclip  
# Pyautogui 
# pywin32 (Windows only)
# psutil (Windows only)

# ========== CONFIG ==========
# PORT = "/dev/cu.usbmodemO0LVP5LSL4VXL3"  # My board's current port
PORT = "COM4"
BAUDRATE = 115200 # Baud rate
TIMEOUT = 0.2 # Check for serial updates for 0.2 s every iteration

# ========== TRIGGER PHRASES ==========
TRIG_IDX = "SYMBOL_IDX:"    # From MCU on startup + every SW2
TRIG_SEND = "SYMBOL_SENT:"  # From MCU on SW3

# Order MUST match MCU's menu.c for the bracket highlight to align
# Had such a FUN time debugging this :)
SYMBOLS = ["π", "∑", "µ", "Ω", "∫"]

# Don't want the character getting typed in the following apps for Windows:
WINDOWS_BLOCK_APPS = {"WindowsTerminal.exe", "cmd.exe", "powershell.exe", "pwsh.exe", "Code.exe"}  # Keep testing for other apps

# Don't want the character getting typed in the following apps for Mac:
MAC_BLOCK_APPS = {"Terminal", "iTerm2"}  # Keep testing for other apps

# Toggle if debug prints. Displays the following:
# Frontmost app 
# Raw MCU output
# Message classification
# Host side filter decisions
DEBUG = False

# Start without any measurement
_t0_ns = None

# Figure out the platform for different responses
OS_NAME = platform.system()  # computed once

# Windows exclusive imports not compatible with other platforms
# The 1st 3 are used to prevent "write" from accessing the wrong apps
# "keyboard" is used to ensure emulation goes smoothly for Windows
if OS_NAME == "Windows": # Don't want to import on a platform these don't exist on
    import psutil
    import win32gui
    import win32process  
    import keyboard
    
# ========== UI HELPERS ==========
def clear_screen():
    # Clear entire screen and move cursor home
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

def draw_ui(selected_symbol: str | None, last_sent: str | None):
    # Redraw the 2-line UI without scrolling
    # Line 1: Symbol Library with brackets around the selected one
    sys.stdout.write("\033[1;1H")  # Move to row 1, col 1
    sys.stdout.write("\033[K")     # Clear to end of line
    sys.stdout.write("Symbol Library: ") 

    # Find the needed character in the list
    try:
        sel_idx = SYMBOLS.index(selected_symbol) if selected_symbol else -1
    except ValueError: # Triggers if the symbol is not in the Python list
        sel_idx = -1

    # List all the characters, highlighting the selected one
    for i, sym in enumerate(SYMBOLS):
        if i == sel_idx:
            sys.stdout.write(f"[{sym}] ")
        else:
            sys.stdout.write(f"{sym} ")

    # Line 2: Currently Copied Symbol
    sys.stdout.write("\n\033[K")
    sys.stdout.write("Currently Copied Symbol: ")
    sys.stdout.write(last_sent if last_sent else "—") # Print the last symbol, or -
    sys.stdout.write("\033[K")
    sys.stdout.flush()

def extract_symbol(line: str) -> str | None:
    # Return the first non-empty token after the colon
    try:
        rhs = line.split(":", 1)[1].strip()
        return rhs.split()[0] if rhs else None
    except Exception:
        return None

# ========== DEBUG HELPERS ==========
# Mac Exclusive
def frontmost_app_name() -> str:
    if OS_NAME != "Darwin": # MacOS only, ignore it otherwise
        return ""
    try:
        out = subprocess.check_output(
            [
                "osascript",
                "-e",
                'tell application "System Events" to get name of first application process whose frontmost is true'
            ],
            text=True
        ).strip()
        return out
    except Exception:
        return ""

def debug_line(row: int, text: str):
    # Debug print to a fixed row
    sys.stdout.write(f"\033[{row};1H\033[K{text}")
    sys.stdout.flush()

# ========== TIMER SETUP ==========
def timer_start():
    # Record and save initial time
    global _t0_ns
    _t0_ns = time.perf_counter_ns()

def timer_record(label: str | None = None):
    # Record and save final time
    global _t0_ns
    if _t0_ns is None:
        return None

    # Subtract initial time from final time to get total time
    dt_ns = time.perf_counter_ns() - _t0_ns
    _t0_ns = None # Reset timer for next iteration
    dt_ms = dt_ns / 1_000_000 # Convert from ns to ms

    if label:
        sys.stdout.write("\033[3;1H")
        sys.stdout.write("\033[K")
        sys.stdout.write(f"{label}: {dt_ms:.3f} ms")
        sys.stdout.flush()

    return dt_ms

# ========== Keyboard Emulation ==========
# Ensures charcaters are sent to device correctly as a keypress
# Also prevents accidental terminal overwrites
# There's a Windows and Mac version (Maybe future Linix version?)
# The correct platform is found at the start to automatically use the
# correct function

# Windows version
def keystroke_emulation_windows(text: str):
    try:
        # Find the window in focus
        hwnd = win32gui.GetForegroundWindow() # Window in focus
        if not hwnd: # Safeguard
            return
        # Use PID to name the process currently in focus
        # "_" allows the thread ID that is found to be ignored
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if not pid:
            return

        # Get the executable name of the focused app and block if needed
        name = psutil.Process(pid).name()
        if name in WINDOWS_BLOCK_APPS:
            return

        # "keyboard" works best for Windows
        keyboard.write(text)   

    # An error occurred somewhere in the emulation
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return
    
# MacOS version
def keystroke_emulation_mac(text: str):
    safe = text.replace("\\", "\\\\").replace('"', '\\"')

    # Cancel request if blocked app is focused
    block_list = ", ".join([f'"{a}"' for a in MAC_BLOCK_APPS])

    script = f'''
    tell application "System Events"
        set frontApp to name of first application process whose frontmost is true
        if frontApp is not in {{{block_list}}} then
            keystroke "{safe}"
        end if
    end tell
    '''
    subprocess.run(["osascript", "-e", script], check=True)

# Legacy version left as a fallback
def terminal_is_focused() -> bool:
    # See what is in focus. Also useful for debugging
    # WARNING: ADDS AT LEAST 120ms TO THE PROCESS
    # The keyboard emulation functions are prioritzed for 
    # faster response, but this is used if all else fails
    app = frontmost_app_name()
    return app in ("Terminal", "iTerm2")

# ========== MAIN LOOP ==========
def main():
    selected_symbol = SYMBOLS[0]  # Default at boot
    last_sent_symbol = None # No symbol sent at boot

    clear_screen() # Clear screen before drawing UI
    draw_ui(selected_symbol, last_sent_symbol) # Draw UI

    last_idx_time = 0.0  

    # Iterate loop
    while True:
        try:
            debug_line(4, f"Connecting to {PORT} @ {BAUDRATE}...")

            # Connect to the virtual porrt to start receiving input
            with serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT) as ser:
                ser.reset_input_buffer()

                debug_line(4, "")  # Clear status line

                while True:
                    line = ser.readline().decode(errors="ignore").strip()
                    if not line:
                        continue

                    if DEBUG:
                        debug_line(6, f"RAW: {repr(line)}")
                        debug_line(5, f"Frontmost: {frontmost_app_name()}")

                    # ---- SW2 / selection updates ----
                    if line.startswith(TRIG_IDX):
                        timer_start()
                        sym = extract_symbol(line) # Grab the selected MCU symbol
                        if sym:
                            selected_symbol = sym
                            draw_ui(selected_symbol, last_sent_symbol)
                            timer_record("Menu update")
                        if DEBUG:
                            debug_line(7, "IDX handled")
                        continue

                    # ---- SW3 / send events ----
                    if line.startswith(TRIG_SEND):
                        timer_start()
                        sym = extract_symbol(line)
                        if sym:
                            if sym == "--":
                                last_sent_symbol = None
                            else:
                                last_sent_symbol = sym
                            draw_ui(selected_symbol, last_sent_symbol)

                            # Write symbol to device
                            if sym != "--":
                                try:
                                    # Figure out the operating system and how to repsond
                                    if OS_NAME == "Darwin": # For Mac
                                        keystroke_emulation_mac(sym)
                                        t_handle = timer_record("Menu + write update")   # Device-dependent delay
                                    elif OS_NAME == "Windows": # For Windows
                                        keystroke_emulation_windows(sym)
                                        t_handle = timer_record("Menu + write update")   # Device-dependent delay
                                    else: # Less effective fallback if not on a Mac/Windows or other error
                                        if not terminal_is_focused():
                                            pyautogui.write(sym)
                                            t_handle = timer_record("Menu + write update")   # Device-dependent delay
                                except Exception: # Crash prevention
                                    pass
                        continue


                    # Unknown message type
                    if DEBUG:
                        debug_line(7, "Unknown message (ignored)")

        except KeyboardInterrupt:
            # Commands like ctrl+v can trigger this
            sys.stdout.write("\nExiting.\n")
            return

        except serial.SerialException as err:
            # Port probably disconnected
            for i in range(5, 0, -1):
                debug_line(4, f"Port unavailable. Retrying in {i}s...")
                time.sleep(1)

        except Exception as e:
            # Show just the first line of the error
            err = str(e).splitlines()[0] if str(e) else "Unknown error"
            for i in range(5, 0, -1):
                debug_line(4, f"Error: {err}. Retrying in {i}s...")
                time.sleep(1)

if __name__ == "__main__":
    main()

