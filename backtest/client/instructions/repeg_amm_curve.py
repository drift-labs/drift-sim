from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class RepegAmmCurveArgs(typing.TypedDict):
    new_peg_candidate: int


layout = borsh.CStruct("new_peg_candidate" / borsh.U128)


class RepegAmmCurveAccounts(typing.TypedDict):
    state: PublicKey
    perp_market: PublicKey
    oracle: PublicKey
    admin: PublicKey


def repeg_amm_curve(
    args: RepegAmmCurveArgs,
    accounts: RepegAmmCurveAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["perp_market"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["oracle"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x03$fY\xb4\x80x\xd5"
    encoded_args = layout.build(
        {
            "new_peg_candidate": args["new_peg_candidate"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
