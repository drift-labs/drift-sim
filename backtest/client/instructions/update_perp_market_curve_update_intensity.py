from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdatePerpMarketCurveUpdateIntensityArgs(typing.TypedDict):
    curve_update_intensity: int


layout = borsh.CStruct("curve_update_intensity" / borsh.U8)


class UpdatePerpMarketCurveUpdateIntensityAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    perp_market: PublicKey


def update_perp_market_curve_update_intensity(
    args: UpdatePerpMarketCurveUpdateIntensityArgs,
    accounts: UpdatePerpMarketCurveUpdateIntensityAccounts,
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
    identifier = b"2\x83\x06\x9c\xe2\xe7\xbdH"
    encoded_args = layout.build(
        {
            "curve_update_intensity": args["curve_update_intensity"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
