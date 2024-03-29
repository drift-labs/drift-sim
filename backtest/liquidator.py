
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

from .parsing import *
from .helpers import *
from .setup import *

from solana.rpc.core import RPCException
from anchorpy.coder.common import _sighash
from driftpy.clearing_house import ClearingHouse

class Liquidator: 
    def __init__(
        self, 
        user_chs, 
        n_markets, 
        n_spot_markets, 
        liquidator_index, 
        send_ix_fcn,
        liquidator_subacc_id: int = 0,
    ) -> None:
        """class for a liquidator 

        Args:
            user_chs (dict(user_index => clearing_house)): all users we want to try to liq
            n_markets (int): number of markets to try to liq from 
            liquidator_index (int): user_chs[liquidator_index] == liquidator's clearing house 

        note we dont try to liquidate the liquidator (bc you cant liq yourself)
        """
        self.user_chs = user_chs
        self.n_markets = n_markets
        self.n_spot_markets = n_spot_markets
        self.liq_ch: ClearingHouse = user_chs[liquidator_index]
        self.liquidator_subacc = liquidator_subacc_id
        self.send_ix = send_ix_fcn
        self.silent = True

    async def liquidate_loop(self):
        await self.try_liquidate_spot()
        await self.try_liquidate_perp()
        await self.try_liquidate_pnl()
        await self.resolve_bankruptcies()
        await self.derisk()
    
    async def try_liquidate_spot(self):
        promises = []
        ixs_args = []

        ch: ClearingHouse
        for i, ch in self.user_chs.items(): 
            authority = ch.authority
            if authority == self.liq_ch.authority: continue

            assets = []
            liabilities = []
            for sid in ch.subaccounts:
                user = await ch.get_user(sid)
                for spot_position in user.spot_positions: 
                    if is_spot_position_available(spot_position): continue
                    match str(spot_position.balance_type):
                        case "SpotBalanceType.Deposit()":
                            assets.append(spot_position.market_index)
                        case "SpotBalanceType.Borrow()":
                            liabilities.append(spot_position.market_index)

                if len(liabilities) > 0 and len(assets) > 0:
                    # try to liq em 
                    promise = await self.liq_ch.get_liquidate_spot_ix(
                        authority, 
                        assets[0],
                        liabilities[0], 
                        2**128 - 1, # maxxx,
                        user_subaccount_id=sid,
                        liq_subaccount_id=self.liquidator_subacc,
                    )

                    promises.append(promise)
                    ixs_args.append({'asset_index': assets[0], 'liab_index': liabilities[0], 'auth_user_index': i})

        # ixs = await asyncio.gather(*promises)
        ixs = promises
        print(f'trying to spot liq {len(ixs)} users')

        promises = []
        for ix_args, ix in zip(ixs_args, ixs):
            promise = await self.send_ix(self.liq_ch, ix, 'liquidate_spot', ix_args, silent_fail=self.silent)

    async def try_liquidate_perp(self):
        ch: ClearingHouse
        promises = []

        for ch in self.user_chs.values(): 
            for sid in ch.subaccounts:
                for i in range(self.n_markets):
                    authority = ch.authority
                    if authority == self.liq_ch.authority: 
                        continue
                    position = await ch.get_user_position(i, sid)
                    # print('user position:', position)

                    if position and position.base_asset_amount != 0:
                        promise = await self.liq_ch.get_liquidate_perp_ix(
                            authority, 
                            i, 
                            abs(position.base_asset_amount),
                            user_subaccount_id=sid,
                            liq_subaccount_id=self.liquidator_subacc,
                        )
                        promises.append(promise)
        # ixs = await asyncio.gather(*promises)
        ixs = promises
        print(f'trying to perp liq {len(ixs)} users')

        promises = []
        for ix in ixs:
            ix_args = liq_perp_ix_args(ix)
            promise = await self.send_ix(self.liq_ch, ix, 'liquidate_perp', ix_args, silent_fail=self.silent)
        

    async def try_liquidate_pnl(self):
        promises = []
        for ch in self.user_chs.values(): 
            for sid in ch.subaccounts:
                for i in range(self.n_markets):
                    authority = ch.authority
                    if authority == self.liq_ch.authority: 
                        continue
                    position = await ch.get_user_position(i, sid)

                    if position and position.base_asset_amount == 0 and position.quote_asset_amount < 0:
                        promise = await self.liq_ch.get_liquidate_perp_pnl_for_deposit_ix(
                            authority,
                            i,
                            QUOTE_SPOT_MARKET_INDEX,
                            abs(position.quote_asset_amount), # take it fully on
                            user_subaccount_id=sid,
                            liq_subaccount_id=self.liquidator_subacc,
                        )
                        promises.append(promise)
        # ixs = await asyncio.gather(*promises)
        ixs = promises

        promises = []
        for ix in ixs:
            ix_args = liquidate_perp_pnl_for_deposit_ix_args(ix)
            promise = await self.send_ix(self.liq_ch, ix, 'liquidate_perp_pnl_for_deposit', ix_args, silent_fail=self.silent)

    async def resolve_bankruptcies(self):
        ch: ClearingHouse
        user_promises = []
        chs = []
        for ch in self.user_chs.values(): 
            authority = ch.authority
            if authority == self.liq_ch.authority: 
                continue
            for sid in ch.subaccounts:
                user = await ch.get_user(sid)
                user_promises.append(user)
                chs.append(ch)
        users = user_promises
        # users = await asyncio.gather(*user_promises)

        ix_names = []
        ix_args = []
        promises = []
        user: User
        for ch, user in zip(chs, users):
            if str(user.status) == "UserStatus.Bankrupt()":
                for i in range(self.n_markets):
                    position = await ch.get_user_position(i)
                    if position is not None and not is_available(position):
                        promise = await self.liq_ch.get_resolve_perp_bankruptcy_ix(
                            user.authority, i, user_subaccount_id=user.sub_account_id, liq_subaccount_id=self.liquidator_subacc,
                        )
                        ix_args.append({'market_index': i, 'authority': user.authority, 'subaccount_id': user.sub_account_id})
                        ix_names.append('perp_bankruptcy')
                        promises.append(promise)
                    
                for i in range(self.n_spot_markets):
                    position = await ch.get_user_spot_position(i)
                    if position is not None and not is_spot_position_available(position):
                        promise = await self.liq_ch.get_resolve_spot_bankruptcy_ix(
                            user.authority, i, user_subaccount_id=user.sub_account_id, liq_subaccount_id=self.liquidator_subacc,
                        )
                        ix_args.append({'market_index': i, 'authority': user.authority, 'subaccount_id': user.sub_account_id})
                        ix_names.append('spot_bankruptcy')
                        promises.append(promise)

        # ixs = await asyncio.gather(*promises)
        ixs = promises
        print(f'trying to resolve {len(ixs)} users bankruptcies')
        for args, ix, name in zip(ix_args, ixs, ix_names):
            await self.send_ix(self.liq_ch, ix, name, args, silent_fail=False, view_logs_flag=True)
        
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
                args = settle_pnl_ix_args(ix[1])
                await self.send_ix(ch, ix, SettlePnLEvent._event_name, args)
            else:
                print(f'=> liquidator derisking')
                ix = await ch.get_close_position_ix(i)
                args = place_and_take_ix_args(ix[1])
                await self.send_ix(ch, ix, ClosePositionEvent._event_name, args)