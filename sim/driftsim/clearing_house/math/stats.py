def calculate_rolling_average(
    data1, 
    data2, 
    weight_numer1, 
    weight_denom1
):
    ''' assumes that missing times are zeros (e.g. handle NaN as 0)'''
    w1 = float(max(0, weight_denom1-weight_numer1))/float(weight_denom1)
    # print(w1, weight_denom1, weight_numer1)
    prev_twap_99 = data1 * w1
    latest_price_01 = data2
    
    result = (
        (prev_twap_99 + latest_price_01)
    )
    return result
