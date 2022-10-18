from __future__ import annotations
import typing
from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
import borsh_construct as borsh
from ..program_id import PROGRAM_ID


class LiquidateBorrowForPerpPnlArgs(typing.TypedDict):
    perp_market_index: int
    spot_market_index: int
    liquidator_max_liability_transfer: int


layout = borsh.CStruct(
    "perp_market_index" / borsh.U16,
    "spot_market_index" / borsh.U16,
    "liquidator_max_liability_transfer" / borsh.U128,
)


class LiquidateBorrowForPerpPnlAccounts(typing.TypedDict):
    state: PublicKey
    authority: PublicKey
    liquidator: PublicKey
    liquidator_stats: PublicKey
    user: PublicKey
    user_stats: PublicKey


def liquidate_borrow_for_perp_pnl(
    args: LiquidateBorrowForPerpPnlArgs,
    accounts: LiquidateBorrowForPerpPnlAccounts,
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
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xa9\x11 Z\xcf\x94\xd1\x1b"
    encoded_args = layout.build(
        {
            "perp_market_index": args["perp_market_index"],
            "spot_market_index": args["spot_market_index"],
            "liquidator_max_liability_transfer": args[
                "liquidator_max_liability_transfer"
            ],
        }
    )
    data = identifier + encoded_args
    return TransactionInstruction(keys, program_id, data)
