from driftpy.accounts import *
from driftpy.clearing_house import ClearingHouse as SDKClearingHouse
from driftpy.setup.helpers import get_feed_data
from driftpy.math.amm import calculate_price
from driftpy.constants.numeric_constants import AMM_RESERVE_PRECISION, QUOTE_PRECISION
from driftpy.clearing_house import ClearingHouse as ClearingHouseSDK
from driftpy.types import PositionDirection

import json 
from dataclasses import dataclass
from backtest.helpers import adjust_oracle_pretrade, set_price_feed_detailed
from driftpy.setup.helpers import get_set_price_feed_detailed_ix
from sim.driftsim.clearing_house.lib import ClearingHouse

@dataclass
class Event:     
    timestamp: int 
    
    def serialize_parameters(self):
        try:
            params = json.dumps(
                self, 
                default=lambda o: o.__dict__, 
                sort_keys=True, 
                indent=4
            )
            return json.loads(params)
        except Exception as e:
            print(self._event_name)
            print(e)
            print("ERRRRR")
            print(self.__dict__)
            print([(x, type(x)) for key, x in self.__dict__.items()])
            return {}
        
    def serialize_to_row(self):
        parameters = self.serialize_parameters()
        # print(parameters)
        timestamp = parameters.pop("timestamp")
        event_name = parameters.pop("_event_name")
        row = {
            "event_name": event_name, 
            "timestamp": timestamp, 
            "parameters": json.dumps(parameters)
        }
        return row 
    
    @staticmethod
    def deserialize_from_row(class_type, event_row):
        event = json.loads(event_row.to_json())
        params = json.loads(event["parameters"])
        params["_event_name"] = event["event_name"]
        params["timestamp"] = event["timestamp"]
        event = class_type(**params)
        return event
    
    # this works for all Event subclasses
    @staticmethod
    def run_row(class_type, clearing_house: ClearingHouse, event_row) -> ClearingHouse:
        event = Event.deserialize_from_row(class_type, event_row)
        return event.run(clearing_house)
    
    @staticmethod
    def run_row_sdk(class_type, clearing_house: ClearingHouse, event_row) -> ClearingHouse:
        event = Event.deserialize_from_row(class_type, event_row)
        return event.run_sdk(clearing_house)
    
    def run(self, clearing_house: ClearingHouse) -> ClearingHouse:
        raise NotImplementedError

    # theres a lot of different inputs for this :/ 
    async def run_sdk(self, *args, **kwargs) -> ClearingHouse:
        raise NotImplementedError

@dataclass
class NullEvent(Event):     
    _event_name: str = "null"
    
    def run(self, clearing_house: ClearingHouse, verbose=False) -> ClearingHouse:
        return clearing_house

    def run_sdk(self):
        pass

@dataclass
class DepositCollateralEvent(Event): 
    user_index: int 
    deposit_amount: int
    spot_market_index: int = 0
    mint_amount: int = 0
    username: str = "u"
    
    _event_name: str = "deposit_collateral"
    
    def run(self, clearing_house: ClearingHouse, verbose=False) -> ClearingHouse:
        if verbose:
            print(f'u{self.user_index} deposit...')
        clearing_house = clearing_house.deposit_user_collateral(
            self.user_index, 
            self.deposit_amount, 
            name=self.username
        )    
        return clearing_house

    async def run_sdk(self, provider, program, usdc_mint, user_keypair, is_initialized):
        # if not initialized .. initialize ... // mint + deposit ix 
        user_clearing_house = SDKClearingHouse(program, user_keypair)

        if not is_initialized:
            await user_clearing_house.intialize_user()

        sig = await user_clearing_house.deposit(self.deposit_amount, self.spot_market_index, user_keypair.public_key)
        return sig

from driftpy.clearing_house_user import get_token_amount
from driftpy.setup.helpers import _mint_usdc_tx

@dataclass 
class MidSimDepositEvent(DepositCollateralEvent):
    reduce_only: bool = True
    _event_name: str = '_mid_sim_deposit_collateral'

    async def run_sdk(self, clearing_house: ClearingHouseSDK, admin_clearing_house: ClearingHouseSDK, spot_mints: list[int]):
        # # balance: int, spot_market: SpotMarket, balance_type: SpotBalanceType
        spot_market = await get_spot_market_account(clearing_house.program, self.spot_market_index)

        position = await clearing_house.get_user_spot_position(self.spot_market_index)
        if position is not None and str(position.balance_type) == "SpotBalanceType.Borrow()":
            token_amount = int(get_token_amount(
                position.scaled_balance, 
                spot_market,
                position.balance_type
            ))
            # pay back full debt here 
            self.deposit_amount = token_amount

            connection = clearing_house.program.provider.connection
            current_amount = (await connection.get_token_account_balance(
                clearing_house.spot_market_atas[self.spot_market_index]
            ))['result']['value']['amount']

            difference_amount = token_amount - int(current_amount)
            if difference_amount > 0:
                difference_amount = int(difference_amount) + 1

                print(f'minting an extra {difference_amount}...')
                mint_tx = _mint_usdc_tx(
                    spot_mints[self.spot_market_index], 
                    clearing_house.program.provider, 
                    difference_amount, 
                    clearing_house.spot_market_atas[self.spot_market_index]
                )
                await admin_clearing_house.send_ixs(mint_tx.instructions)

        ix = await clearing_house.get_deposit_collateral_ix(
            int(self.deposit_amount),
            self.spot_market_index,
            clearing_house.spot_market_atas[self.spot_market_index],
            reduce_only=self.reduce_only
        )
        return ix

@dataclass
class WithdrawEvent(Event): 
    user_index: int 
    spot_market_index: int
    withdraw_amount: int
    reduce_only: bool
    username: str = "u"
    
    _event_name: str = "withdraw_collateral"
    
    def run(self, clearing_house: ClearingHouse, verbose=False) -> ClearingHouse:
        # pass
        return clearing_house

    async def run_sdk(self, clearing_house: ClearingHouseSDK):
        # if not initialized .. initialize ... // mint + deposit ix 
        ix = await clearing_house.get_withdraw_collateral_ix(
            self.withdraw_amount, 
            self.spot_market_index, 
            clearing_house.spot_market_atas[self.spot_market_index], 
            self.reduce_only
        )
        return ix 

@dataclass 
class SpotOracleUpdateEvent(Event):
    market_index: int = 0 
    price: int = 0 
    conf: int = 0
    slot: int = 0
    _event_name: str = "spot_oracle_price"

    def run(self, clearing_house: ClearingHouse, verbose=False) -> ClearingHouse:
        return clearing_house

    async def run_sdk(self, program, oracle_program): 
        spot_market = await get_spot_market_account(
            program,
            self.market_index
        )
        return await get_set_price_feed_detailed_ix(
            oracle_program, spot_market.oracle, self.price, self.conf, self.slot
        )
        
@dataclass 
class PerpOracleUpdateEvent(Event):
    market_index: int = 0 
    price: int = 0 
    conf: int = 0
    slot: int = 0
    _event_name: str = "perp_oracle_price"

    def run(self, clearing_house: ClearingHouse, verbose=False) -> ClearingHouse:
        return clearing_house

    async def run_sdk(self, program, oracle_program): 
        market = await get_perp_market_account(
            program,
            self.market_index
        )
        return await get_set_price_feed_detailed_ix(
            oracle_program, market.amm.oracle, self.price, self.conf, self.slot
        )

@dataclass 
class addLiquidityEvent(Event):
    market_index: int = 0 
    user_index: int = 0 
    token_amount: int = 0 

    _event_name: str = "add_liquidity"

    def run(self, clearing_house: ClearingHouse, verbose=False) -> ClearingHouse:
        if verbose:
            print(f'u{self.user_index} {self._event_name}...')

        clearing_house = clearing_house.add_liquidity(
            market_index=self.market_index,
            user_index=self.user_index,
            token_amount=self.token_amount
        )
        return clearing_house

    async def run_sdk(self, clearing_house: ClearingHouseSDK): 
        return await clearing_house.get_add_liquidity_ix(
            self.token_amount, 
            self.market_index
        )

@dataclass
class removeLiquidityEvent(Event):
    market_index: int = 0 
    user_index: int = 0 
    lp_token_amount: int = -1

    _event_name: str = "remove_liquidity"
    
    def run(self, clearing_house: ClearingHouse, verbose=False) -> ClearingHouse:
        if verbose:
            print(f'u{self.user_index} {self._event_name}...')
        
        clearing_house = clearing_house.remove_liquidity(
            self.market_index, 
            self.user_index, 
            self.lp_token_amount
        )    
        return clearing_house
    
    async def run_sdk(self, clearing_house: ClearingHouseSDK):
        if self.lp_token_amount == -1: 
            user = await get_user_account(clearing_house.program, clearing_house.authority)
            position = None 
            for _position in user.perp_positions: 
                if _position.market_index == self.market_index: 
                    position = _position
                    break 
            assert position is not None, "user not in market"

            self.lp_token_amount = position.lp_shares
            if position.lp_shares == 0:
                return None

            # assert self.lp_token_amount > 0, 'trying to burn full zero tokens'

        ix = await clearing_house.get_remove_liquidity_ix(
            self.lp_token_amount, 
            self.market_index
        )
        return ix
    
@dataclass
class OpenPositionEvent(Event): 
    user_index: int 
    direction: str 
    quote_amount: int 
    market_index: int
    
    _event_name: str = "open_position"
    
    def run(self, clearing_house: ClearingHouse, verbose=False) -> ClearingHouse:
        if verbose:
            print(f'u{self.user_index} {self._event_name} {self.direction} {self.quote_amount}...')
        direction = {
            "long": PositionDirection.LONG,
            "short": PositionDirection.SHORT,
        }[self.direction]
        
        clearing_house = clearing_house.open_position(
            direction, 
            self.user_index, 
            self.quote_amount, 
            self.market_index
        )
        
        return clearing_house

    async def run_sdk(self, clearing_house: ClearingHouseSDK, init_leverage=None, oracle_program=None, adjust_oracle_pre_trade=False) -> ClearingHouse:
        # tmp -- sim is quote open position v2 is base only
        market = await get_perp_market_account(clearing_house.program, self.market_index)

        mark_price = calculate_price(
            market.amm.base_asset_reserve,
            market.amm.quote_asset_reserve,
            market.amm.peg_multiplier,
        )
        baa = int(self.quote_amount * AMM_RESERVE_PRECISION / QUOTE_PRECISION / mark_price)
        baa = min(baa, market.amm.base_asset_reserve // 2)
        if baa == 0: 
            print('warning: baa too small -> rounding up')
            baa = market.amm.base_asset_amount_step_size
        is_ioc = False
        direction = {
            "long": PositionDirection.LONG(),
            "short": PositionDirection.SHORT(),
        }[self.direction]

        if adjust_oracle_pre_trade: 
            assert oracle_program is not None
            await adjust_oracle_pretrade(
                baa, 
                direction, 
                market, 
                oracle_program
            )

        if init_leverage:
            data = await get_feed_data(oracle_program, market.amm.oracle)
            price = data.price
            print('get_feed_data oracle price:', price, data)
            user = await clearing_house.get_user()
            from driftpy.clearing_house_user import ClearingHouseUser
            chu = ClearingHouseUser(clearing_house) 
            collateral = await chu.get_total_collateral()

            pos = None
            for position in user.perp_positions:
                # print(position)
                if position.market_index == self.market_index and (position.base_asset_amount!=0 or position.quote_asset_amount!=0):
                    pos = position

            if pos is not None:
                if pos.open_orders > 15:
                    return await clearing_house.cancel_orders()

            max_baa = collateral * init_leverage / price
            # update 
            baa = int(min(max_baa, baa))

        if baa == 0:
            print('trying to open position with baa == 0 : early exiting open position')
            return 

        print(f'opening baa: {baa} {direction} {self.market_index}')

        pchange = 0.99 # 50% change
        if self.direction == 'long':
            limit_price = price * (1 + pchange)
        else: 
            limit_price = price * (1 - pchange)

        ix = await clearing_house.get_open_position_ix(
            direction, 
            baa, 
            self.market_index, 
            ioc=is_ioc,
            limit_price=limit_price,
        )
        return ix
                
@dataclass
class ClosePositionEvent(Event): 
    user_index: int 
    market_index: int
    _event_name: str = "close_position"
    
    def run(self, clearing_house: ClearingHouse, verbose=False) -> ClearingHouse:
        if verbose:
            print(f'u{self.user_index} {self._event_name}...')
        clearing_house = clearing_house.close_position(
            self.user_index, 
            self.market_index
        )
        
        return clearing_house
    
    async def run_sdk(self, clearing_house: ClearingHouseSDK, oracle_program=None, adjust_oracle_pre_trade=False) -> ClearingHouse:
        # tmp -- sim is quote open position v2 is base only
        market = await get_perp_market_account(clearing_house.program, self.market_index)
        user = await get_user_account(clearing_house.program, clearing_house.authority)

        position = None 
        for _position in user.perp_positions: 
            if _position.market_index == self.market_index: 
                position = _position
                break 
        assert position is not None, "user not in market"

        direction = PositionDirection.LONG() if position.base_asset_amount < 0 else PositionDirection.SHORT()

        print(f'closing: {abs(position.base_asset_amount)} {direction}')

        if adjust_oracle_pre_trade: 
            assert oracle_program is not None
            await adjust_oracle_pretrade(
                position.base_asset_amount, 
                direction, 
                market, 
                oracle_program
            )

        return await clearing_house.get_close_position_ix(self.market_index)
         
@dataclass
class SettleLPEvent(Event): 
    user_index: int 
    market_index: int
    _event_name: str = "settle_lp"
    
    def run(self, clearing_house: ClearingHouse, verbose=False) -> ClearingHouse:
        if verbose:
            print(f'u{self.user_index} {self._event_name}...')
            
        clearing_house = clearing_house.settle_lp(
            self.market_index,
            self.user_index, 
        )
        
        return clearing_house

    async def run_sdk(self, clearing_house: ClearingHouseSDK):
        return await clearing_house.get_settle_lp_ix(
            clearing_house.authority, 
            self.market_index
        )
         
@dataclass
class SettlePnLEvent(Event): 
    user_index: int 
    market_index: int
    _event_name: str = "settle_pnl"
    
    def run(self, clearing_house: ClearingHouse, verbose=False) -> ClearingHouse:
        pass 
        # not implemented yet... 
        return clearing_house

    async def run_sdk(self, clearing_house: ClearingHouseSDK):
        position = await clearing_house.get_user_position(self.market_index)
        if position is None or position.base_asset_amount == 0: 
            return None

        return await clearing_house.get_settle_pnl_ix(
            clearing_house.authority, 
            self.market_index
        )
         
@dataclass
class InitIfStakeEvent(Event): 
    user_index: int 
    market_index: int
    _event_name: str = "init_if_stake"
    
    def run(self, clearing_house: ClearingHouse, verbose=False) -> ClearingHouse:
        pass 
        # not implemented yet... 
        return clearing_house

    async def run_sdk(self, clearing_house: ClearingHouseSDK):
        return clearing_house.get_initialize_insurance_fund_stake_ix(
            self.market_index, 
        )

@dataclass
class AddIfStakeEvent(Event): 
    user_index: int 
    market_index: int
    amount: int
    _event_name: str = "add_if_stake"
    
    def run(self, clearing_house: ClearingHouse, verbose=False) -> ClearingHouse:
        pass 
        # not implemented yet... 
        return clearing_house

    async def run_sdk(self, clearing_house: ClearingHouseSDK):
        return await clearing_house.get_add_insurance_fund_stake_ix(
            self.market_index, 
            self.amount
        )

@dataclass
class LiquidateEvent(Event): 
    user_index: int 
    _event_name: str = "liquidate"

    def run(self, _): 
        return _
    
    def run_sdk(self, _): 
        return _

@dataclass
class RemoveIfStakeEvent(Event): 
    user_index: int 
    market_index: int
    amount: int
    _event_name: str = "remove_if_stake"
    
    def run(self, clearing_house: ClearingHouse, verbose=False) -> ClearingHouse:
        pass 
        # not implemented yet... 
        return clearing_house

    async def run_sdk(self, clearing_house: ClearingHouseSDK):
        spot = await get_spot_market_account(clearing_house.program, self.market_index)
        total_shares = spot.insurance_fund.total_shares
        if_stake = await get_if_stake_account(clearing_house.program, clearing_house.authority, self.market_index)
        n_shares = if_stake.if_shares

        conn = clearing_house.program.provider.connection
        vault_pk = get_insurance_fund_vault_public_key(clearing_house.program_id, self.market_index)
        v_amount = int((await conn.get_token_account_balance(vault_pk))['result']['value']['amount'])

        print(
            f'vault_amount: {v_amount} n_shares: {n_shares} total_shares: {total_shares}'
        )

        withdraw_amount = int(v_amount * n_shares / total_shares)
        
        if withdraw_amount == 0:
            print('WARNING: if_stake withdraw amount == 0')
            return

        ix1 = await clearing_house.get_request_remove_insurance_fund_stake_ix(
            self.market_index, 
            withdraw_amount
        )
        ix2 = await clearing_house.get_remove_insurance_fund_stake_ix(
            self.market_index, 
        )
        return [ix1, ix2]

# %%
