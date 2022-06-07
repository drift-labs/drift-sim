import numpy as np 
import json

# %%
def random_walk_oracle(start_price, n_steps=100):
    prices = []
    timestamps = []
    
    price = start_price
    time = 0     
    for _ in range(n_steps):
        prices.append(price)
        timestamps.append(time)

        sign = np.random.choice([-1, 1])
        price = price + sign * np.random.normal()
        time = time + np.random.randint(low=1, high=10)

    # normalize prices 
    prices = np.array(prices)
    # lowest price = $1
    prices = prices - np.min(prices) + 1
    
    timestamps = np.array(timestamps)
        
    return prices, timestamps


def rand_heterosk_oracle(start_price, n_steps=100):
    prices = []
    timestamps = []
    
    k_period = 10 # 10 seconds
    price = start_price
    time = 0     
    std = 1
    for _ in range(n_steps):
        prices.append(price)
        timestamps.append(time)

        sign = np.random.choice([-1, 1])
        if np.random.randint(low=1, high=9) > 7:
            price_delta = sign * abs(np.random.normal(scale=1))
        else:
            price_delta = sign * abs(np.random.normal(scale=std))

        time_delta = np.random.randint(low=1, high=9)

        std = np.sqrt((price_delta**2 * time_delta + std**2 * (k_period-time_delta))/k_period)
        # print(std)
        price += price_delta
        time += time_delta

    # normalize prices 
    prices = np.array(prices)
    # lowest price = $1
    prices = prices - np.min(prices) + 1
    
    timestamps = np.array(timestamps)
        
    return prices, timestamps

def class_to_json(obj, classkey=None):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = class_to_json(v, classkey)
        return data
    elif hasattr(obj, "_asdict"):
        return class_to_json(obj._asdict())
    elif hasattr(obj, "_ast"):
        return class_to_json(obj._ast())
    elif hasattr(obj, "__iter__"):
        return [class_to_json(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict([(key, class_to_json(value, classkey))
                     for key, value in obj.__dict__.items()
                     if not callable(value) and not key.startswith('_')])
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj