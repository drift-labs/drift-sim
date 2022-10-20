from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdatePerpMarketConcentrationCoefArgs(typing.TypedDict):
    concentration_scale: int


layout = borsh.CStruct("concentration_scale" / borsh.U128)


class UpdatePerpMarketConcentrationCoefAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    perp_market: PublicKey


def update_perp_market_concentration_coef(
    args: UpdatePerpMarketConcentrationCoefArgs,
    accounts: UpdatePerpMarketConcentrationCoefAccounts,
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
    identifier = b"\x18N\xe8~\xa9\xb0\xe6\x10"
    encoded_args = layout.build(
        {
            "concentration_scale": args["concentration_scale"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
