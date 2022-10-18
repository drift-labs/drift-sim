from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class InitializeSerumFulfillmentConfigArgs(typing.TypedDict):
    market_index: int


layout = borsh.CStruct("market_index" / borsh.U16)


class InitializeSerumFulfillmentConfigAccounts(typing.TypedDict):
    base_spot_market: PublicKey
    quote_spot_market: PublicKey
    state: PublicKey
    serum_program: PublicKey
    serum_market: PublicKey
    serum_open_orders: PublicKey
    clearing_house_signer: PublicKey
    serum_fulfillment_config: PublicKey
    admin: PublicKey
    rent: PublicKey
    system_program: PublicKey


def initialize_serum_fulfillment_config(
    args: InitializeSerumFulfillmentConfigArgs,
    accounts: InitializeSerumFulfillmentConfigAccounts,
    program_id: PublicKey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> TransactionInstruction:
    keys: list[AccountMeta] = [
        AccountMeta(
            pubkey=accounts["base_spot_market"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["quote_spot_market"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["state"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["serum_program"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["serum_market"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["serum_open_orders"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["clearing_house_signer"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["serum_fulfillment_config"],
            is_signer=False,
            is_writable=True,
        ),
        AccountMeta(pubkey=accounts["admin"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["rent"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["system_program"], is_signer=False, is_writable=False
        ),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xc1\xd3\x84\xacF\xab\x07^"
    encoded_args = layout.build(
        {
            "market_index": args["market_index"],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
