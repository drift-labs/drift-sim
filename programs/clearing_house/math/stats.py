def calculate_rolling_average(
    data1, 
    data2, 
    weight_numer1, 
    weight_denom1
):
    ''' assumes that missing times are zeros (e.g. handle NaN as 0)'''
    prev_twap_99 = data1 * float(max(0, weight_denom1-weight_numer1))/float(weight_denom1)
    latest_price_01 = data2
    
    result = (
        (prev_twap_99 + latest_price_01)
    )
    return result
