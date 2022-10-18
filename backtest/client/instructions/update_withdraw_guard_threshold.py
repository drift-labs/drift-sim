from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateWithdrawGuardThresholdArgs(typing.TypedDict):
    withdraw_guard_threshold: int


layout = borsh.CStruct("withdraw_guard_threshold" / borsh.U128)


class UpdateWithdrawGuardThresholdAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    spot_market: PublicKey


def update_withdraw_guard_threshold(
    args: UpdateWithdrawGuardThresholdArgs,
    accounts: UpdateWithdrawGuardThresholdAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["spot_market"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"8\x12'=\x9b\xd3,\x85"
    encoded_args = layout.build(
        {
            "withdraw_guard_threshold": args["withdraw_guard_threshold"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
