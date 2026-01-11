/* TimeCounter.c */

#include "TimeCounter.h"
#include "MCUType.h"
#include "FRDM_MCXN947_GPIO.h"
#include "assert.h"

typedef struct {
    INT32U counter;
} TC_CNT_BUFFER_T;

static volatile TC_CNT_BUFFER_T tcCntBuffer = {0u};

/*****************************************************************************************
* TCCounterInit()
*   Sets up LPTMR0 to generate periodic interrupts and increments tcCntBuffer.counter
*****************************************************************************************/
void TCCounterInit(void)
{
    /* Enable clock path for LPTMR (this macro worked in your current SDK build) */
    SYSCON->CLOCK_CTRL |= SYSCON_CLOCK_CTRL_CLKIN_ENA_FM_USBH_LPT(1);

    /* Disable timer while configuring */
    LPTMR0->CSR = LPTMR_CSR_TEN(0);

    /* Select clock source, bypass prescaler */
    LPTMR0->PSR = LPTMR_PSR_PCS(3) | LPTMR_PSR_PBYP(1);

    /* Compare value sets interrupt period */
    LPTMR0->CMR = LPTMR_CMR_COMPARE(240000u - 1u);

    /* Clear compare flag */
    LPTMR0->CSR = LPTMR_CSR_TCF(1);

    /* Enable IRQ in NVIC */
    NVIC_ClearPendingIRQ(LPTMR0_IRQn);
    NVIC_EnableIRQ(LPTMR0_IRQn);

    /* Enable timer + interrupt */
    LPTMR0->CSR |= LPTMR_CSR_TEN(1);
    LPTMR0->CSR |= LPTMR_CSR_TIE(1);
}

/*****************************************************************************************
* LPTMR0_IRQHandler()
*   Interrupt handler increments the tick counter.
*****************************************************************************************/
void LPTMR0_IRQHandler(void)
{
    /* Clear compare flag */
    LPTMR0->CSR |= LPTMR_CSR_TCF(1);

    /* Increment tick counter */
    tcCntBuffer.counter++;
}

/*****************************************************************************************
* TCCountGet()
*   Returns the current tick count.
*****************************************************************************************/
INT32U TCCountGet(void)
{
    return tcCntBuffer.counter;
}
