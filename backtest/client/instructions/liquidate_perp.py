from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class LiquidatePerpArgs(typing.TypedDict):
    market_index: int
    liquidator_max_base_asset_amount: int


layout = borsh.CStruct(
    "market_index" / borsh.U16, "liquidator_max_base_asset_amount" / borsh.U64
)


class LiquidatePerpAccounts(typing.TypedDict):
    state: PublicKey
    authority: PublicKey
    liquidator: PublicKey
    liquidator_stats: PublicKey
    user: PublicKey
    user_stats: PublicKey


def liquidate_perp(
    args: LiquidatePerpArgs,
    accounts: LiquidatePerpAccounts,
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
    identifier = b"K#w\xf7\xbf\x12\x8b\x02"
    encoded_args = layout.build(
        {
            "market_index": args["market_index"],
            "liquidator_max_base_asset_amount": args[
                "liquidator_max_base_asset_amount"
            ],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
