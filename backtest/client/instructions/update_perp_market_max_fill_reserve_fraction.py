from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdatePerpMarketMaxFillReserveFractionArgs(typing.TypedDict):
    max_fill_reserve_fraction: int


layout = borsh.CStruct("max_fill_reserve_fraction" / borsh.U16)


class UpdatePerpMarketMaxFillReserveFractionAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    perp_market: PublicKey


def update_perp_market_max_fill_reserve_fraction(
    args: UpdatePerpMarketMaxFillReserveFractionArgs,
    accounts: UpdatePerpMarketMaxFillReserveFractionAccounts,
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
    identifier = b"\x13\xacr\x9a*\x87\xa1\x85"
    encoded_args = layout.build(
        {
            "max_fill_reserve_fraction": args["max_fill_reserve_fraction"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
