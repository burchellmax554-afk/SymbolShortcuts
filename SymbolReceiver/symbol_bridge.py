# SymbolReceiver.py
# Live mirror of MCU symbol state with clipboard copy on send
# UI (two lines, ANSI redraw):
#   Symbol Library: π [∑] µ Ω ∫
#   Last Sent: —

import serial # For connection to virtual port
import sys # For the terminal UI
import time # For recording response times and delaying a loop
import pyperclip # For running ctrl+c commands

# ========== CONFIG ==========
PORT = "/dev/cu.usbmodemO0LVP5LSL4VXL3"  # My current board's port
BAUDRATE = 115200 
TIMEOUT = 0.2

# ========== TRIGGER PHRASES ==========
TRIG_IDX = "SYMBOL_IDX:"    # From MCU on startup + every SW2
TRIG_SEND = "SYMBOL_SENT:"  # From MCU on SW3

# Order MUST match MCU's menu.c for the bracket highlight to align
SYMBOLS = ["π", "∑", "µ", "Ω", "∫"]

# Start without any measurement
_t0_ns = None

# ========== UI HELPERS ==========
# Clear the entire screen
def clear_screen():
    # Clear entire screen and move cursor home
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

# Create a UI
def draw_ui(selected_symbol: str | None, last_sent: str | None):
    # Redraw the 2-line UI without scrolling
    # Line 1: Symbol Library with brackets around the selected one
    sys.stdout.write("\033[1;1H")      # Move to row 1, col 1
    sys.stdout.write("\033[K")         # Clear to end of line
    sys.stdout.write("Symbol Library: ")
    # Determine which index is selected (if any)
    try: # Here to stop a crash if the next line fails
        sel_idx = SYMBOLS.index(selected_symbol) if selected_symbol else -1
    except ValueError: 
        sel_idx = -1  # Unknown symbol - render with no highlight

    # Print the list of symbols, putting [] around the selected one
    for i, sym in enumerate(SYMBOLS):
        if i == sel_idx:
            sys.stdout.write(f"[{sym}] ")
        else:
            sys.stdout.write(f"{sym} ")

    # Line 2: Currently Copied Symbol
    sys.stdout.write("\n\033[K")       # Ensure program is on line 2 and clear it
    sys.stdout.write("Currently Copied Symbol: ")
    sys.stdout.write(last_sent if last_sent else "—")
    sys.stdout.write("\033[K")         # Clear rest of line (in case length shrank)
    sys.stdout.flush()

# Find the symbol the MCU sent over
def extract_symbol(line: str) -> str | None:
    # Return the first non-empty token after the colon
    try:
        rhs = line.split(":", 1)[1].strip()
        return rhs.split()[0] if rhs else None
    except Exception:
        return None

# ========== TIMER SETUP ==========   
def timer_start():
    # Code to start timer
    global _t0_ns
    _t0_ns = time.perf_counter_ns()

def timer_record(label: str | None = None):
    # Code to record time
    global _t0_ns
    # Prevent timer_stop from continuing if timer isn't going
    if _t0_ns is None: 
        return None
    # Find time since input was detected
    dt_ns = time.perf_counter_ns() - _t0_ns
    _t0_ns = None
    # Convert from ns to ms
    dt_ms = dt_ns / 1_000_000
    if label:
        sys.stdout.write("\033[3;1H")      # Move cursor to line 3, column 1
        sys.stdout.write("\033[K")         # Clear the entire line
        sys.stdout.write(f"{label}: {dt_ms:.3f} ms")
        sys.stdout.flush()
    return dt_ms


# ========== MAIN LOOP ==========
def main():
    selected_symbol = SYMBOLS[0]   # Assume default at boot
    last_sent_symbol = None
    clear_screen()
    draw_ui(selected_symbol, last_sent_symbol)

    # Connect/reconnect loop
    while True:
        try:
            sys.stdout.write("\033[4;1H\033[K")
            sys.stdout.write(f"Connecting to {PORT} @ {BAUDRATE}...")
            sys.stdout.flush()

            # Run the correct port at the needed baudrate, establish a timeout, 
            # attach it to a variable, ser
            with serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT) as ser:

                # Toss any partial line
                ser.reset_input_buffer() # Cancel the data waiting to be read

                # Connected—erase status line to stop repitition
                sys.stdout.write("\033[4;1H\033[K")
                sys.stdout.flush()

                # Everything is set up correctly, wait for updates
                while True: 
                    # Check each line for the correct data
                    line = ser.readline().decode(errors="ignore").strip()
                    if not line:
                        continue

                    # Handle selection updates (SW2 or startup)
                    if line.startswith(TRIG_IDX):
                        timer_start()
                        sym = extract_symbol(line)
                        if sym:
                            selected_symbol = sym
                            draw_ui(selected_symbol, last_sent_symbol)
                            timer_record("Menu update")
                        continue

                    # Handle send event (SW3)
                    if line.startswith(TRIG_SEND):
                        timer_start()
                        sym = extract_symbol(line)
                        if sym:
                            if sym == "--":
                                last_sent_symbol = None
                            else:
                                last_sent_symbol = sym
                                try:
                                    pyperclip.copy(sym) # Auto-copy the symbol down
                                except Exception:
                                    pass
                            draw_ui(selected_symbol, last_sent_symbol)
                            timer_record("Copy + menu update")
                        continue

        # Prevent a crash when ctrl+c is pressed in terminal
        except KeyboardInterrupt:
            sys.stdout.write("\nExiting.\n")
            return
        except serial.SerialException:
            # Likely board unplugged or port busy. Sleep and retry.
            sys.stdout.write("\033[4;1H\033[K")
            sys.stdout.write("Port unavailable. Retrying in 2s...")
            sys.stdout.flush()

            time.sleep(2) # Hold 2 seconds
        except Exception as e:
            # Unexpected error—show briefly, then retry
            sys.stdout.write("\033[4;1H\033[K")
            sys.stdout.write(f"Error: {e}")
            sys.stdout.flush()

            time.sleep(2) # Hold 2 seconds

if __name__ == "__main__":
    main()
