from anchorpy.coder.common import _sighash

def parse_ix_args(ix, layout, identifier):
    """ix => ix_args dictionary using anchorpy's layout
    """
    data = ix.data
    args = layout.parse(data.split(identifier)[1])
    dargs = dict(args)
    dargs.pop('_io')
    return dargs

def place_and_take_ix_args(ix):
    from client.instructions.place_and_take_perp_order import layout
    identifier = b"\xd53\x01\xbbl\xdc\xe6\xe0" 
    ix_args = parse_ix_args(ix, layout, identifier) # [1] bc we increase the compute too
    order_params = dict(ix_args.pop('params'))
    order_params.pop('_io')
    ix_args['params'] = order_params
    return ix_args

def settle_pnl_ix_args(ix):
    from client.instructions.settle_pnl import layout
    identifier = _sighash('settle_pnl')
    ix_args = parse_ix_args(ix, layout, identifier)
    return ix_args

def add_liquidity_ix_args(ix):
    from client.instructions.add_perp_lp_shares import layout
    identifier = b"8\xd18\xc5w\xfe\xbcu"
    ix_args = parse_ix_args(ix, layout, identifier)
    return ix_args

def remove_liquidity_ix_args(ix):
    from client.instructions.remove_perp_lp_shares import layout
    identifier = b"\xd5Y\xd9\x12\xa075\x8d"    
    ix_args = parse_ix_args(ix, layout, identifier)
    return ix_args

def settle_lp_ix_args(ix):
    from client.instructions.settle_lp import layout
    identifier = b"\x9b\xe7tqa\xe5\x8b\x8d"
    ix_args = parse_ix_args(ix, layout, identifier)
    return ix_args

def liq_perp_ix_args(ix):
    from client.instructions.liquidate_perp import layout
    identifier = b"K#w\xf7\xbf\x12\x8b\x02"
    ix_args = parse_ix_args(ix, layout, identifier)
    return ix_args

def liquidate_perp_pnl_for_deposit_ix_args(ix):
    from client.instructions.liquidate_perp_pnl_for_deposit import layout
    identifier = b"\xedK\xc6\xeb\xe9\xbaK#"
    ix_args = parse_ix_args(ix, layout, identifier)
    return ix_args

def resolve_perp_bankruptcy_ix_args(ix):
    from client.instructions.resolve_perp_bankruptcy import layout
    identifier = b"\xe0\x10\xb0\xd6\xa2\xd5\xb7\xde"
    ix_args = parse_ix_args(ix, layout, identifier)
    return ix_args

def withdraw_ix_args(ix):
    from client.instructions.withdraw import layout
    identifier = b'\xb7\x12F\x9c\x94m\xa1"'
    ix_args = parse_ix_args(ix, layout, identifier)
    return ix_args