from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class UpdateSpotMarketOracleArgs(typing.TypedDict):
    oracle: PublicKey
    oracle_source: types.oracle_source.OracleSourceKind


layout = borsh.CStruct(
    "oracle" / BorshPubkey, "oracle_source" / types.oracle_source.layout
)


class UpdateSpotMarketOracleAccounts(typing.TypedDict):
    admin: PublicKey
    state: PublicKey
    spot_market: PublicKey


def update_spot_market_oracle(
    args: UpdateSpotMarketOracleArgs,
    accounts: UpdateSpotMarketOracleAccounts,
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
    identifier = b"r\xb8f%\xf6\xba\xb4c"
    encoded_args = layout.build(
        {
            "oracle": args["oracle"],
            "oracle_source": args["oracle_source"].to_encodable(),
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
