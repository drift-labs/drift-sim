from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class ResolvePerpBankruptcyArgs(typing.TypedDict):
    quote_spot_market_index: int
    market_index: int


layout = borsh.CStruct(
    "quote_spot_market_index" / borsh.U16, "market_index" / borsh.U16
)


class ResolvePerpBankruptcyAccounts(typing.TypedDict):
    state: PublicKey
    authority: PublicKey
    liquidator: PublicKey
    liquidator_stats: PublicKey
    user: PublicKey
    user_stats: PublicKey
    spot_market_vault: PublicKey
    insurance_fund_vault: PublicKey
    clearing_house_signer: PublicKey
    token_program: PublicKey


def resolve_perp_bankruptcy(
    args: ResolvePerpBankruptcyArgs,
    accounts: ResolvePerpBankruptcyAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["authority"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["liquidator"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["liquidator_stats"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["user"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["user_stats"], is_signer=False, is_writable=True),
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
    identifier = b"\xe0\x10\xb0\xd6\xa2\xd5\xb7\xde"
    encoded_args = layout.build(
        {
            "quote_spot_market_index": args["quote_spot_market_index"],
            "market_index": args["market_index"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
