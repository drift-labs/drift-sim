from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class LiquidateSpotArgs(typing.TypedDict):
    asset_market_index: int
    liability_market_index: int
    liquidator_max_liability_transfer: int


layout = borsh.CStruct(
    "asset_market_index" / borsh.U16,
    "liability_market_index" / borsh.U16,
    "liquidator_max_liability_transfer" / borsh.U128,
)


class LiquidateSpotAccounts(typing.TypedDict):
    state: PublicKey
    authority: PublicKey
    liquidator: PublicKey
    liquidator_stats: PublicKey
    user: PublicKey
    user_stats: PublicKey


def liquidate_spot(
    args: LiquidateSpotArgs,
    accounts: LiquidateSpotAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["liquidator"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["liquidator_stats"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["user"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["user_stats"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"k\x00\x80)#\xe5\xfb\x12"
    encoded_args = layout.build(
        {
            "asset_market_index": args["asset_market_index"],
            "liability_market_index": args["liability_market_index"],
            "liquidator_max_liability_transfer": args[
                "liquidator_max_liability_transfer"
            ],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
