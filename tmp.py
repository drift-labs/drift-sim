total_fees = 0
total_lp_balance = 0 # interest space 
total_lp_tokens = 0 # real space 
fee_cum_interest = 1

def add_lp(deposit_amount):
    global total_lp_balance, total_lp_tokens, fee_cum_interest
    lp_balance = deposit_amount / fee_cum_interest
    total_lp_balance += lp_balance
    total_lp_tokens += deposit_amount
    return lp_balance

def remove_lp(lp_balance):
    global total_lp_balance, total_lp_tokens, fee_cum_interest
    lp_tokens = lp_balance * fee_cum_interest
    total_lp_balance -= lp_balance
    total_lp_tokens -= lp_tokens
    return lp_tokens

# lp adds 
deposit_amount = 100 
lp0_balance = add_lp(deposit_amount)

# another lp adds 
deposit_amount = 100 
lp1_balance = add_lp(deposit_amount)

# trading occurs 
fee = 10 
fee_cum_interest += (total_lp_tokens + fee) / total_lp_balance - fee_cum_interest
total_lp_tokens += fee

# another lp adds 
deposit_amount = 100 
lp2_balance = add_lp(deposit_amount)

# trading occurs 
fee = 10 
fee_cum_interest += (total_lp_tokens + fee) / total_lp_balance - fee_cum_interest
total_lp_tokens += fee 

# lp removes 
lp0_balance = remove_lp(lp0_balance)
lp1_balance = remove_lp(lp1_balance)
lp2_balance = remove_lp(lp2_balance)

# 108.38709677419354 108.38709677419354
print(
    lp0_balance, lp1_balance 
)

# 103.2258064516129
print(
    lp2_balance
)
