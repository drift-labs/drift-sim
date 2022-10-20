from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class ResolvePerpPnlDeficitArgs(typing.TypedDict):
    spot_market_index: int
    perp_market_index: int


layout = borsh.CStruct("spot_market_index" / borsh.U16, "perp_market_index" / borsh.U16)


class ResolvePerpPnlDeficitAccounts(typing.TypedDict):
    state: PublicKey
    authority: PublicKey
    spot_market_vault: PublicKey
    insurance_fund_vault: PublicKey
    clearing_house_signer: PublicKey
    token_program: PublicKey


def resolve_perp_pnl_deficit(
    args: ResolvePerpPnlDeficitArgs,
    accounts: ResolvePerpPnlDeficitAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
        AccountMeta(
            pubkey=accounts["spot_market_vault"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["insurance_fund_vault"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["clearing_house_signer"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["token_program"], is_signer=False, is_writable=False
        ),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xa8\xccD\x96\x9f~_\x94"
    encoded_args = layout.build(
        {
            "spot_market_index": args["spot_market_index"],
            "perp_market_index": args["perp_market_index"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
