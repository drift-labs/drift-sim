from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateStateSettlementDurationArgs(typing.TypedDict):
    settlement_duration: int


layout = borsh.CStruct("settlement_duration" / borsh.U16)


class UpdateStateSettlementDurationAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey


def update_state_settlement_duration(
    args: UpdateStateSettlementDurationArgs,
    accounts: UpdateStateSettlementDurationAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"aD\xc7\xeb\x83P=\xad"
    encoded_args = layout.build(
        {
            "settlement_duration": args["settlement_duration"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
