cumm_fee_per_lp = 0 
total_lp_shares = 0 

def add_liquidty(token_amount): 
    global total_lp_shares
    total_lp_shares += token_amount
    return (token_amount, cumm_fee_per_lp)

def remove_liquidity(token_amount, last_cumm_fee):
    global total_lp_shares
    total_lp_shares -= token_amount
    fee_payment = token_amount * (cumm_fee_per_lp - last_cumm_fee)
    return fee_payment

# add lp 
lp0_shares, lp0_last_cumm_fee = add_liquidty(10) 

# add lp 
lp1_shares, lp1_last_cumm_fee = add_liquidty(20) 

# fees 
fee = 10 
cumm_fee_per_lp += fee / total_lp_shares

# remove lp 
lp1_fee_payment = remove_liquidity(lp1_shares, lp1_last_cumm_fee)

# remove lp 
lp0_fee_payment = remove_liquidity(lp0_shares, lp0_last_cumm_fee)

print(lp0_fee_payment)
print(lp1_fee_payment)
