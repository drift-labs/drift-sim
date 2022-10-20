from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class MoveAmmPriceArgs(typing.TypedDict):
    base_asset_reserve: int
    quote_asset_reserve: int
    sqrt_k: int


layout = borsh.CStruct(
    "base_asset_reserve" / borsh.U128,
    "quote_asset_reserve" / borsh.U128,
    "sqrt_k" / borsh.U128,
)


class MoveAmmPriceAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    perp_market: PublicKey


def move_amm_price(
    args: MoveAmmPriceArgs,
    accounts: MoveAmmPriceAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["perp_market"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xebm\x02R\xdbv\x06\x9f"
    encoded_args = layout.build(
        {
            "base_asset_reserve": args["base_asset_reserve"],
            "quote_asset_reserve": args["quote_asset_reserve"],
            "sqrt_k": args["sqrt_k"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
