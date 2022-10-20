from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class UpdateSpotMarketIfFactorArgs(typing.TypedDict):
    spot_market_index: int
    user_if_factor: int
    total_if_factor: int


layout = borsh.CStruct(
    "spot_market_index" / borsh.U16,
    "user_if_factor" / borsh.U32,
    "total_if_factor" / borsh.U32,
)


class UpdateSpotMarketIfFactorAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    spot_market: PublicKey


def update_spot_market_if_factor(
    args: UpdateSpotMarketIfFactorArgs,
    accounts: UpdateSpotMarketIfFactorAccounts,
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
    identifier = b'\x93\x1e\xe0"\x12\xe6i\x04'
    encoded_args = layout.build(
        {
            "spot_market_index": args["spot_market_index"],
            "user_if_factor": args["user_if_factor"],
            "total_if_factor": args["total_if_factor"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
