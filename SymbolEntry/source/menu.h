#ifndef MENU_H
#define MENU_H

#include "MCUType.h"   /* For INT8U and INT8C types */

/* number of symbols */
#define SYMBOL_COUNT 5

/* redraw full menu UI */
void UpdateMenu(void);

/* get current index */
INT8U GetCurrentSymbolIndex(void);

/* set current index + redraw */
void SetCurrentSymbolIndex(INT8U index);

/* get pointer to current symbol */
const INT8C* GetCurrentSymbol(void);

/* Set last sent symbol + redraw */
void SetLastSentSymbol(const INT8C *sym);

/* Record to start tracking time for an iteration */
void MenuTiming_Start(void);

/* Stop tracking time at the end of an iteration */
void MenuTiming_EndPrint(const INT8C *label);

#endif

