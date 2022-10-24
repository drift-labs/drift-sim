from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdatePerpMarketMaxOpenInterestArgs(typing.TypedDict):
    max_open_interest: int


layout = borsh.CStruct("max_open_interest" / borsh.U128)


class UpdatePerpMarketMaxOpenInterestAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    perp_market: PublicKey


def update_perp_market_max_open_interest(
    args: UpdatePerpMarketMaxOpenInterestArgs,
    accounts: UpdatePerpMarketMaxOpenInterestAccounts,
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
    identifier = b"\xc2O\x95\xe0\xf6f\xba\x8c"
    encoded_args = layout.build(
        {
            "max_open_interest": args["max_open_interest"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
