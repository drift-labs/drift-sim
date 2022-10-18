from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateSpotMarketLiquidationFeeArgs(typing.TypedDict):
    liquidator_fee: int
    if_liquidation_fee: int


layout = borsh.CStruct("liquidator_fee" / borsh.U128, "if_liquidation_fee" / borsh.U128)


class UpdateSpotMarketLiquidationFeeAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    spot_market: PublicKey


def update_spot_market_liquidation_fee(
    args: UpdateSpotMarketLiquidationFeeArgs,
    accounts: UpdateSpotMarketLiquidationFeeAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["spot_market"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x0b\r\xff58\x88h\xb1"
    encoded_args = layout.build(
        {
            "liquidator_fee": args["liquidator_fee"],
            "if_liquidation_fee": args["if_liquidation_fee"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
