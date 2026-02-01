# SymbolReceiver.py
# Live mirror of MCU symbol state with clipboard copy on send
# UI (two lines, ANSI redraw):
#   Symbol Library: π [∑] µ Ω ∫
#   Currently Copied Symbol: —

import serial  # For connection to virtual port
import sys     # For the terminal UI
import time    # For recording response times and delaying a loop
import pyperclip  # For clipboard ctrl+c commands
import pyautogui # For running ctrl+v commands
import subprocess # For debugging

# ========== CONFIG ==========
PORT = "/dev/cu.usbmodemO0LVP5LSL4VXL3"  # My current board's port
BAUDRATE = 115200
TIMEOUT = 0.2

# ========== TRIGGER PHRASES ==========
TRIG_IDX = "SYMBOL_IDX:"    # From MCU on startup + every SW2
TRIG_SEND = "SYMBOL_SENT:"  # From MCU on SW3

# Order MUST match MCU's menu.c for the bracket highlight to align
SYMBOLS = ["π", "∑", "µ", "Ω", "∫"]

# Debug prints. Displays the following:
# Frontmost app 
# Raw MCU output
# Message classification
# Host side filter decisions
DEBUG = False

# Start without any measurement
_t0_ns = None

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

    try:
        sel_idx = SYMBOLS.index(selected_symbol) if selected_symbol else -1
    except ValueError:
        sel_idx = -1

    for i, sym in enumerate(SYMBOLS):
        if i == sel_idx:
            sys.stdout.write(f"[{sym}] ")
        else:
            sys.stdout.write(f"{sym} ")

    # Line 2: Currently Copied Symbol
    sys.stdout.write("\n\033[K")
    sys.stdout.write("Currently Copied Symbol: ")
    sys.stdout.write(last_sent if last_sent else "—")
    sys.stdout.write("\033[K")
    sys.stdout.flush()

def extract_symbol(line: str) -> str | None:
    # Return the first non-empty token after the colon
    try:
        rhs = line.split(":", 1)[1].strip()
        return rhs.split()[0] if rhs else None
    except Exception:
        return None
    
def clipboard_copy_mac(text: str):
    subprocess.run("pbcopy", input=text, text=True, check=False)

# ========== DEBUG HELPERS ==========
def frontmost_app_name() -> str:
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

def terminal_is_focused() -> bool:
    app = frontmost_app_name()
    return app in ("Terminal", "iTerm2")

def debug_line(row: int, text: str):
    # Non-intrusive debug print to a fixed row
    sys.stdout.write(f"\033[{row};1H\033[K{text}")
    sys.stdout.flush()

# ========== TIMER SETUP ==========
def timer_start():
    global _t0_ns
    _t0_ns = time.perf_counter_ns()

def timer_record(label: str | None = None):
    global _t0_ns
    if _t0_ns is None:
        return None

    dt_ns = time.perf_counter_ns() - _t0_ns
    _t0_ns = None
    dt_ms = dt_ns / 1_000_000

    if label:
        sys.stdout.write("\033[3;1H")
        sys.stdout.write("\033[K")
        sys.stdout.write(f"{label}: {dt_ms:.3f} ms")
        sys.stdout.flush()

    return dt_ms

# ========== MAIN LOOP ==========
def main():
    selected_symbol = SYMBOLS[0]  # Assume default at boot
    last_sent_symbol = None

    clear_screen()
    draw_ui(selected_symbol, last_sent_symbol)

    last_idx_time = 0.0  # For host-side guard against spurious SEND after IDX

    while True:
        try:
            debug_line(4, f"Connecting to {PORT} @ {BAUDRATE}...")

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
                        sym = extract_symbol(line)
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
                            t_handle = timer_record("Menu + copy update")   # Any dalay after this point is a hardware issue

                            # OS-dependent step (not counted)
                            if sym != "--":
                                try:
                                    # Replace with pbcopy if you want
                                    pyperclip.copy(sym)
                                    pyautogui.hotkey("command", "v")
                                except Exception:
                                    pass
                        continue


                    # Unknown message type
                    if DEBUG:
                        debug_line(7, "Unknown message (ignored)")

        except KeyboardInterrupt:
            sys.stdout.write("\nExiting.\n")
            return

        except serial.SerialException:
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
