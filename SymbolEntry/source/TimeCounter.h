#ifndef TIMECounter_H
#define TIMECounter_H

#include "MCUType.h"
#include "os.h"
#include "FRDM_MCXN947ClkCfg.h"
#include "FRDM_MCXN947_GPIO.h"
#include "CsOS_SW.h"
#include "BasicIO.h"
#include "app_cfg.h"

// Function Prototypes
void TCCounterInit(void);
INT32U TCCountPend(OS_TICK tout, OS_ERR *os_err);
void LPTMR0_IRQHandler(void);
INT32U TCCountGet(void);

#endif // TimeCounter_H
