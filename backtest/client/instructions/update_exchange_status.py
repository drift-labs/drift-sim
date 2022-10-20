from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class UpdateExchangeStatusArgs(typing.TypedDict):
    exchange_status: types.exchange_status.ExchangeStatusKind


layout = borsh.CStruct("exchange_status" / types.exchange_status.layout)


class UpdateExchangeStatusAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey


def update_exchange_status(
    args: UpdateExchangeStatusArgs,
    accounts: UpdateExchangeStatusAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"S\xa0\xfc\xfa\x81t1\xdf"
    encoded_args = layout.build(
        {
            "exchange_status": args["exchange_status"].to_encodable(),
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
