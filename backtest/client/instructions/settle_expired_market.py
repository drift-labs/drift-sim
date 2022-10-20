from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class SettleExpiredMarketArgs(typing.TypedDict):
    market_index: int


layout = borsh.CStruct("market_index" / borsh.U16)


class SettleExpiredMarketAccounts(typing.TypedDict):
    state: PublicKey
    authority: PublicKey


def settle_expired_market(
    args: SettleExpiredMarketArgs,
    accounts: SettleExpiredMarketAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"xY\x0b\x19zMH\xc1"
    encoded_args = layout.build(
        {
            "market_index": args["market_index"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
