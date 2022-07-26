def max_collateral_change(user, delta):
    if user.collateral + delta < 0: 
        print("warning neg collateral...")
        assert False
        delta = -user.collateral
    return delta

def add_prefix(data: dict, prefix: str):
    for key in list(data.keys()): 
        data[f"{prefix}_{key}"] = data.pop(key)