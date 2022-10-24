from driftpy.types import SwapDirection

def calculate_updated_collateral(collateral, pnl):
    if pnl < 0 and abs(pnl) > collateral:
        return 0 
    else: # < 0 pnl = subtract, > 0 pnl = add 
        # print('collatearl,pnl = ', collateral, pnl)
        return collateral + pnl 

def calculate_pnl(
    exit_value, 
    entry_value,
    swap_direction
):
    return {
        # add = buying asset (was prev short)
        # pnl = entry - exit 
        # short @ 2$ -- long @ 1$ -- pnl = 2 - 1 = 1$
        SwapDirection.ADD: exit_value - entry_value, 
        # remove = selling asset 
        # pnl = exit price - entry price 
        # long @ 1$ -- sell @ 2$ -- pnl = exit - entry = 2 - 1 = 1$
        SwapDirection.REMOVE: entry_value - exit_value,
    }[swap_direction]
    