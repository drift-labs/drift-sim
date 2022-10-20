from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateUserCustomMarginRatioArgs(typing.TypedDict):
    sub_account_id: int
    margin_ratio: int


layout = borsh.CStruct("sub_account_id" / borsh.U8, "margin_ratio" / borsh.U32)


class UpdateUserCustomMarginRatioAccounts(typing.TypedDict):
    user: PublicKey
    authority: PublicKey


def update_user_custom_margin_ratio(
    args: UpdateUserCustomMarginRatioArgs,
    accounts: UpdateUserCustomMarginRatioAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["user"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x15\xdd\x8c\xbb \x81\x0b{"
    encoded_args = layout.build(
        {
            "sub_account_id": args["sub_account_id"],
            "margin_ratio": args["margin_ratio"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
