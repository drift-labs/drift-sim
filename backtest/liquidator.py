
import sys
sys.path.insert(0, '../')
sys.path.insert(0, '../driftpy/src/')

import pandas as pd 
import numpy as np 

from driftpy.math.amm import *
from driftpy.math.trade import *
from driftpy.math.positions import *
from driftpy.math.market import *
from driftpy.math.user import *

from driftpy.types import *
from driftpy.types import PerpMarket
from driftpy.constants.numeric_constants import *

from parsing import *
from helpers import *
from setup import *
from solana.rpc.core import RPCException
from anchorpy.coder.common import _sighash

class Liquidator: 
    def __init__(self, user_chs, n_markets, liquidator_index, send_ix_fcn) -> None:
        """class for a liquidator 

        Args:
            user_chs (dict(user_index => clearing_house)): all users we want to try to liq
            n_markets (int): number of markets to try to liq from 
            liquidator_index (int): user_chs[liquidator_index] == liquidator's clearing house 

        note we dont try to liquidate the liquidator (bc you cant liq yourself)
        """
        self.user_chs = user_chs
        self.n_markets = n_markets
        self.liq_ch: ClearingHouse = user_chs[liquidator_index]
        self.send_ix = send_ix_fcn

    async def liquidate_loop(self):
        await self.try_liquidate_perp()
        await self.try_liquidate_pnl()
        await self.resolve_bankruptcies()
        await self.derisk()

    async def try_liquidate_perp(self):
        ch: ClearingHouse
        promises = []

        for ch in self.user_chs.values(): 
            for i in range(self.n_markets):
                authority = ch.authority
                if authority == self.liq_ch.authority: 
                    continue
                position = await ch.get_user_position(i)

                if position and position.base_asset_amount != 0:
                    promise = self.liq_ch.get_liquidate_perp_ix(
                        authority, 
                        i, 
                        abs(position.base_asset_amount)
                    )
                    promises.append(promise)
        ixs = await asyncio.gather(*promises)

        promises = []
        for ix in ixs:
            ix_args = liq_perp_ix_args(ix)
            promise = self.send_ix(self.liq_ch, ix, 'liquidate_perp', ix_args, silent_fail=True)
            promises.append(promise)
        await asyncio.gather(*promises)

    async def try_liquidate_pnl(self):
        promises = []
        for ch in self.user_chs.values(): 
            for i in range(self.n_markets):
                authority = ch.authority
                if authority == self.liq_ch.authority: 
                    continue
                position = await ch.get_user_position(i)

                if position and position.base_asset_amount == 0 and position.quote_asset_amount < 0:
                    promise = self.liq_ch.get_liquidate_perp_pnl_for_deposit_ix(
                        authority,
                        i,
                        QUOTE_SPOT_MARKET_INDEX,
                        abs(position.quote_asset_amount) # take it fully on
                    )
                    promises.append(promise)
        ixs = await asyncio.gather(*promises)

        promises = []
        for ix in ixs:
            ix_args = liquidate_perp_pnl_for_deposit_ix_args(ix)
            promise = self.send_ix(self.liq_ch, ix, 'liquidate_perp_pnl_for_deposit', ix_args, silent_fail=True)
            promises.append(promise)
        await asyncio.gather(*promises)

    async def resolve_bankruptcies(self):
        ch: ClearingHouse
        user_promises = []
        chs = []
        for ch in self.user_chs.values(): 
            authority = ch.authority
            if authority == self.liq_ch.authority: 
                continue
            user = ch.get_user()
            user_promises.append(user)
            chs.append(ch)
        users = await asyncio.gather(*user_promises)

        promises = []
        user: User
        for ch, user in zip(chs, users):
            if user.is_bankrupt:
                for i in range(self.n_markets):
                    position = await ch.get_user_position(i)
                    if not is_available(position):
                        promise = self.liq_ch.get_resolve_perp_bankruptcy_ix(
                            user.authority, i
                        )
                        promises.append(promise)

        ixs = await asyncio.gather(*promises)
        p = []
        for ix in ixs:
            args = resolve_perp_bankruptcy_ix_args(ix)
            p.append(
                self.send_ix(self.liq_ch, ix, 'resolve_perp_bankruptcy', args, silent_fail=True)
            )
        await asyncio.gather(*p)
        
    async def derisk(self):
        ch: ClearingHouse = self.liq_ch
        provider = self.liq_ch.program.provider

        for i in range(self.n_markets):
            position = await ch.get_user_position(i)
            if position is None or position.base_asset_amount == 0: 
                continue

            market = await get_perp_market_account(self.liq_ch.program, i)
            slot = (await provider.connection.get_slot())['result']
            liq_time = (await provider.connection.get_block_time(slot))['result']
            print(f'=> liquidator derisking {position.base_asset_amount} baa in market status:', market.status)

            if str(market.status) == "MarketStatus.Settlement()" or market.expiry_ts >= liq_time:
                print(f'=> liquidator settling expired position')
                ix = await ch.get_settle_pnl_ix(self.liq_ch.authority, i)
                args = settle_pnl_ix_args(ix)
                await self.send_ix(ch, ix, SettlePnLEvent._event_name, args)
            else:
                print(f'=> liquidator derisking')
                ix = await ch.get_close_position_ix(i)
                args = place_and_take_ix_args(ix[1])
                await self.send_ix(ch, ix, ClosePositionEvent._event_name, args)