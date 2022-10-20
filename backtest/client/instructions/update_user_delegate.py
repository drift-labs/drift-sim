from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateUserDelegateArgs(typing.TypedDict):
    sub_account_id: int
    delegate: PublicKey


layout = borsh.CStruct("sub_account_id" / borsh.U8, "delegate" / BorshPubkey)


class UpdateUserDelegateAccounts(typing.TypedDict):
    user: PublicKey
    authority: PublicKey


def update_user_delegate(
    args: UpdateUserDelegateArgs,
    accounts: UpdateUserDelegateAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["user"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x8b\xcd\x8d\x8dq$^\xbb"
    encoded_args = layout.build(
        {
            "sub_account_id": args["sub_account_id"],
            "delegate": args["delegate"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
