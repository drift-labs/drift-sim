from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class AddPerpLpSharesArgs(typing.TypedDict):
    n_shares: int
    market_index: int


layout = borsh.CStruct("n_shares" / borsh.U64, "market_index" / borsh.U16)

class AddPerpLpSharesAccounts(typing.TypedDict):
    state: PublicKey
    user: PublicKey
    authority: PublicKey


def add_perp_lp_shares(
    args: AddPerpLpSharesArgs,
    accounts: AddPerpLpSharesAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["user"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"8\xd18\xc5w\xfe\xbcu"
    encoded_args = layout.build(
        {
            "n_shares": args["n_shares"],
            "market_index": args["market_index"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
