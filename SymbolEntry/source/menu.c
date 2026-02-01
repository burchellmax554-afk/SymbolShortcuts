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
    BIOPutStrg("SYMBOL_IDX: ");
    BIOPutStrg(symbols[current_symbol_index]);
    BIOPutStrg("\r\n");

    BIOPutStrg("SYMBOL_SENT: ");
    if (last_sent_symbol != 0) {
        BIOPutStrg(last_sent_symbol);
    } else {
        BIOPutStrg("--");
    }
    BIOPutStrg("\r\n");
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

        BIOPutStrg("SYMBOL_IDX: ");
        BIOPutStrg(symbols[current_symbol_index]);
        BIOPutStrg("\r\n");
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

    BIOPutStrg("SYMBOL_SENT: ");
    if (last_sent_symbol != 0) {
        BIOPutStrg(last_sent_symbol);
    } else {
        BIOPutStrg("--");
    }
    BIOPutStrg("\r\n");
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
****************************************************************************************/
void MenuTiming_EndPrint(const INT8C *label)
{
    if (!g_timing_armed) {
        return;
    }

    INT32U t1 = TCCountGet();
    INT32U dt_ticks = (INT32U)(t1 - g_t0_ticks);
    INT32U dt_ms = dt_ticks;  /* TCCountGet is already ms ticks */

    /* Plain text, python-friendly */
    BIOPutStrg("MCU_");
    if (label != (const INT8C *)0) {
        BIOPutStrg(label);          /* "SW2" or "SW3" */
    } else {
        BIOPutStrg("TIME");
    }
    BIOPutStrg("_MS: ");
    BIOOutDecWord(dt_ms, 4, BIO_OD_MODE_AR);
    BIOPutStrg("\r\n");

    g_timing_armed = 0;
}

