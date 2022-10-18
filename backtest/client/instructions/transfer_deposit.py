from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class TransferDepositArgs(typing.TypedDict):
    market_index: int
    amount: int


layout = borsh.CStruct("market_index" / borsh.U16, "amount" / borsh.U64)


class TransferDepositAccounts(typing.TypedDict):
    from_user: PublicKey
    to_user: PublicKey
    user_stats: PublicKey
    authority: PublicKey
    state: PublicKey


def transfer_deposit(
    args: TransferDepositArgs,
    accounts: TransferDepositAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["from_user"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["to_user"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["user_stats"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x14\x14\x93\xdf)?\xcco"
    encoded_args = layout.build(
        {
            "market_index": args["market_index"],
            "amount": args["amount"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
