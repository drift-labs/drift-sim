from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdatePerpMarketStepSizeAndTickSizeArgs(typing.TypedDict):
    step_size: int
    tick_size: int


layout = borsh.CStruct("step_size" / borsh.U64, "tick_size" / borsh.U64)


class UpdatePerpMarketStepSizeAndTickSizeAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    perp_market: PublicKey


def update_perp_market_step_size_and_tick_size(
    args: UpdatePerpMarketStepSizeAndTickSizeArgs,
    accounts: UpdatePerpMarketStepSizeAndTickSizeAccounts,
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
    identifier = b"\xe7\xffa\x19\x92\x8b\xae\x04"
    encoded_args = layout.build(
        {
            "step_size": args["step_size"],
            "tick_size": args["tick_size"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
