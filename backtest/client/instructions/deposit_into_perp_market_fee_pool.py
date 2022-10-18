from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class DepositIntoPerpMarketFeePoolArgs(typing.TypedDict):
    amount: int


layout = borsh.CStruct("amount" / borsh.U64)


class DepositIntoPerpMarketFeePoolAccounts(typing.TypedDict):
    state: PublicKey
    perp_market: PublicKey
    admin: PublicKey
    source_vault: PublicKey
    clearing_house_signer: PublicKey
    quote_spot_market: PublicKey
    spot_market_vault: PublicKey
    token_program: PublicKey


def deposit_into_perp_market_fee_pool(
    args: DepositIntoPerpMarketFeePoolArgs,
    accounts: DepositIntoPerpMarketFeePoolAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["perp_market"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["source_vault"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["clearing_house_signer"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["quote_spot_market"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["spot_market_vault"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["token_program"], is_signer=False, is_writable=False
        ),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b'":9DaP\xf4\x06'
    encoded_args = layout.build(
        {
            "amount": args["amount"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
