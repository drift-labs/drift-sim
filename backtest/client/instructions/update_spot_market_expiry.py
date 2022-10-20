from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateSpotMarketExpiryArgs(typing.TypedDict):
    expiry_ts: int


layout = borsh.CStruct("expiry_ts" / borsh.I64)


class UpdateSpotMarketExpiryAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    spot_market: PublicKey


def update_spot_market_expiry(
    args: UpdateSpotMarketExpiryArgs,
    accounts: UpdateSpotMarketExpiryAccounts,
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
    identifier = b"\xd0\x0b\xd3\x9f\xe2\x18\x0b\xf7"
    encoded_args = layout.build(
        {
            "expiry_ts": args["expiry_ts"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
