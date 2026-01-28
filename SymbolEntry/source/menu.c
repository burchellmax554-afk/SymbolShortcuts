/* menu.c */
#include "menu.h"
#include "MCUType.h"
#include "BasicIO.h"
#include "TimeCounter.h"

/* Symbol table: ordered list of selectable symbols */
/* As long as SYMBOL_COUNT and the python symbol list are appropriately */
/* updated, you can add and remove whatever symbols you like here */
static const INT8C *symbols[SYMBOL_COUNT] = {"π", "∑", "µ", "Ω", "∫"};

/* Tracks which symbol is currently active */
static INT8U current_symbol_index = 0;

/* Tracks last-sent symbol (NULL until first send) */
static const INT8C *last_sent_symbol = (const INT8C *)0;

/* Timer value initialization */
static INT32U g_t0_ticks = 0;
static INT8U  g_timing_armed = 0;

/*****************************************************************************************
* UpdateMenu()
*   Fully redraws the menu UI as 3 lines, top to bottom.
*   Intended to keep python-friendly "full lines" with '\n' at end.
*****************************************************************************************/
void UpdateMenu(void) {

    /* Clear entire screen + home cursor for a clean menu */
    BIOPutStrg("\033[2J\033[H");

    /* LINE 1: symbol library with brackets */
    for (INT8U i = 0; i < SYMBOL_COUNT; i++) {
        if (i == current_symbol_index) {
            BIOPutStrg("["); /* Once the symbol is found, put brackets around it */
            BIOPutStrg(symbols[i]);
            BIOPutStrg("] ");
        } else {
            BIOPutStrg(symbols[i]);
            BIOPutStrg(" ");
        }
    }
    BIOPutStrg("\r\n");

    /* LINE 2: SYMBOL_IDX: <symbol> */
    BIOPutStrg("SYMBOL_IDX: ");
    BIOPutStrg(symbols[current_symbol_index]);
    BIOPutStrg("\r\n");

    /* LINE 3: SYMBOL_SENT: <symbol> or -- if none*/
    BIOPutStrg("SYMBOL_SENT: ");
    if (last_sent_symbol != 0) {
        BIOPutStrg(last_sent_symbol);
    } else {
        BIOPutStrg("--");
    }
    BIOPutStrg("\r\n");

    /* LINE 4: RESPONSE_TIME */

}


/*****************************************************************************************
* GetCurrentSymbolIndex()
*****************************************************************************************/
INT8U GetCurrentSymbolIndex(void) {
    return current_symbol_index;
}


/*****************************************************************************************
* SetCurrentSymbolIndex()
*   Updates index then redraws menu
*****************************************************************************************/
void SetCurrentSymbolIndex(INT8U index) {
    if (index < SYMBOL_COUNT) {
        current_symbol_index = index;
        UpdateMenu();
    }
}


/*****************************************************************************************
* GetCurrentSymbol()
*****************************************************************************************/
const INT8C* GetCurrentSymbol(void) {
    return symbols[current_symbol_index];
}


/*****************************************************************************************
* SetLastSentSymbol()
*   Call this when SW3 fires
*****************************************************************************************/
void SetLastSentSymbol(const INT8C *sym) {
    last_sent_symbol = sym;
    UpdateMenu();
}

/*****************************************************************************************
* MenuTiming_Start()
*   This grabs the start time of the menu
****************************************************************************************/
void MenuTiming_Start(void)
{
    g_t0_ticks = TCCountGet();
    g_timing_armed = 1;
}

/*****************************************************************************************
* MenuTiming_()
*   Prints: "<label>: <ms> ms" on terminal line 4
*   Only viewable on the MCU terminal, not carried over to Python end
****************************************************************************************/
void MenuTiming_EndPrint(const INT8C *label)
{
    if (!g_timing_armed) {
        return; /* start not called */
    }

    INT32U t1 = TCCountGet();

    /* unsigned subtraction safely handles wraparound */
    INT32U dt_ticks = (INT32U)(t1 - g_t0_ticks);

    /* Timer value saved in ms */
    INT32U dt_ms = dt_ticks;

    /* Go to line 4 */
    BIOPutStrg("\x1B[4;1H\x1B[K");

    if (label != (const INT8C *)0) {
        BIOPutStrg(label);
        BIOPutStrg(": ");
    }

    BIOOutDecWord(dt_ms, 4, BIO_OD_MODE_AR);
    BIOPutStrg(" ms");

    g_timing_armed = 0;
}

