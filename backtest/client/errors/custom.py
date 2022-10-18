import typing
from anchorpy.error import ProgramError


class InvalidSpotMarketAuthority(ProgramError):
    def __init__(self) -> None:
        super().__init__(6000, "Invalid Spot Market Authority")

    code = 6000
    name = "InvalidSpotMarketAuthority"
    msg = "Invalid Spot Market Authority"


class InvalidInsuranceFundAuthority(ProgramError):
    def __init__(self) -> None:
        super().__init__(6001, "Clearing house not insurance fund authority")

    code = 6001
    name = "InvalidInsuranceFundAuthority"
    msg = "Clearing house not insurance fund authority"


class InsufficientDeposit(ProgramError):
    def __init__(self) -> None:
        super().__init__(6002, "Insufficient deposit")

    code = 6002
    name = "InsufficientDeposit"
    msg = "Insufficient deposit"


class InsufficientCollateral(ProgramError):
    def __init__(self) -> None:
        super().__init__(6003, "Insufficient collateral")

    code = 6003
    name = "InsufficientCollateral"
    msg = "Insufficient collateral"


class SufficientCollateral(ProgramError):
    def __init__(self) -> None:
        super().__init__(6004, "Sufficient collateral")

    code = 6004
    name = "SufficientCollateral"
    msg = "Sufficient collateral"


class MaxNumberOfPositions(ProgramError):
    def __init__(self) -> None:
        super().__init__(6005, "Max number of positions taken")

    code = 6005
    name = "MaxNumberOfPositions"
    msg = "Max number of positions taken"


class AdminControlsPricesDisabled(ProgramError):
    def __init__(self) -> None:
        super().__init__(6006, "Admin Controls Prices Disabled")

    code = 6006
    name = "AdminControlsPricesDisabled"
    msg = "Admin Controls Prices Disabled"


class MarketIndexNotInitialized(ProgramError):
    def __init__(self) -> None:
        super().__init__(6007, "Market Index Not Initialized")

    code = 6007
    name = "MarketIndexNotInitialized"
    msg = "Market Index Not Initialized"


class MarketIndexAlreadyInitialized(ProgramError):
    def __init__(self) -> None:
        super().__init__(6008, "Market Index Already Initialized")

    code = 6008
    name = "MarketIndexAlreadyInitialized"
    msg = "Market Index Already Initialized"


class UserAccountAndUserPositionsAccountMismatch(ProgramError):
    def __init__(self) -> None:
        super().__init__(6009, "User Account And User Positions Account Mismatch")

    code = 6009
    name = "UserAccountAndUserPositionsAccountMismatch"
    msg = "User Account And User Positions Account Mismatch"


class UserHasNoPositionInMarket(ProgramError):
    def __init__(self) -> None:
        super().__init__(6010, "User Has No Position In Market")

    code = 6010
    name = "UserHasNoPositionInMarket"
    msg = "User Has No Position In Market"


class InvalidInitialPeg(ProgramError):
    def __init__(self) -> None:
        super().__init__(6011, "Invalid Initial Peg")

    code = 6011
    name = "InvalidInitialPeg"
    msg = "Invalid Initial Peg"


class InvalidRepegRedundant(ProgramError):
    def __init__(self) -> None:
        super().__init__(6012, "AMM repeg already configured with amt given")

    code = 6012
    name = "InvalidRepegRedundant"
    msg = "AMM repeg already configured with amt given"


class InvalidRepegDirection(ProgramError):
    def __init__(self) -> None:
        super().__init__(6013, "AMM repeg incorrect repeg direction")

    code = 6013
    name = "InvalidRepegDirection"
    msg = "AMM repeg incorrect repeg direction"


class InvalidRepegProfitability(ProgramError):
    def __init__(self) -> None:
        super().__init__(6014, "AMM repeg out of bounds pnl")

    code = 6014
    name = "InvalidRepegProfitability"
    msg = "AMM repeg out of bounds pnl"


class SlippageOutsideLimit(ProgramError):
    def __init__(self) -> None:
        super().__init__(6015, "Slippage Outside Limit Price")

    code = 6015
    name = "SlippageOutsideLimit"
    msg = "Slippage Outside Limit Price"


class OrderSizeTooSmall(ProgramError):
    def __init__(self) -> None:
        super().__init__(6016, "Order Size Too Small")

    code = 6016
    name = "OrderSizeTooSmall"
    msg = "Order Size Too Small"


class InvalidUpdateK(ProgramError):
    def __init__(self) -> None:
        super().__init__(6017, "Price change too large when updating K")

    code = 6017
    name = "InvalidUpdateK"
    msg = "Price change too large when updating K"


class AdminWithdrawTooLarge(ProgramError):
    def __init__(self) -> None:
        super().__init__(
            6018, "Admin tried to withdraw amount larger than fees collected"
        )

    code = 6018
    name = "AdminWithdrawTooLarge"
    msg = "Admin tried to withdraw amount larger than fees collected"


class MathError(ProgramError):
    def __init__(self) -> None:
        super().__init__(6019, "Math Error")

    code = 6019
    name = "MathError"
    msg = "Math Error"


class BnConversionError(ProgramError):
    def __init__(self) -> None:
        super().__init__(
            6020, "Conversion to u128/u64 failed with an overflow or underflow"
        )

    code = 6020
    name = "BnConversionError"
    msg = "Conversion to u128/u64 failed with an overflow or underflow"


class ClockUnavailable(ProgramError):
    def __init__(self) -> None:
        super().__init__(6021, "Clock unavailable")

    code = 6021
    name = "ClockUnavailable"
    msg = "Clock unavailable"


class UnableToLoadOracle(ProgramError):
    def __init__(self) -> None:
        super().__init__(6022, "Unable To Load Oracles")

    code = 6022
    name = "UnableToLoadOracle"
    msg = "Unable To Load Oracles"


class PriceBandsBreached(ProgramError):
    def __init__(self) -> None:
        super().__init__(6023, "Price Bands Breached")

    code = 6023
    name = "PriceBandsBreached"
    msg = "Price Bands Breached"


class ExchangePaused(ProgramError):
    def __init__(self) -> None:
        super().__init__(6024, "Exchange is paused")

    code = 6024
    name = "ExchangePaused"
    msg = "Exchange is paused"


class InvalidWhitelistToken(ProgramError):
    def __init__(self) -> None:
        super().__init__(6025, "Invalid whitelist token")

    code = 6025
    name = "InvalidWhitelistToken"
    msg = "Invalid whitelist token"


class WhitelistTokenNotFound(ProgramError):
    def __init__(self) -> None:
        super().__init__(6026, "Whitelist token not found")

    code = 6026
    name = "WhitelistTokenNotFound"
    msg = "Whitelist token not found"


class InvalidDiscountToken(ProgramError):
    def __init__(self) -> None:
        super().__init__(6027, "Invalid discount token")

    code = 6027
    name = "InvalidDiscountToken"
    msg = "Invalid discount token"


class DiscountTokenNotFound(ProgramError):
    def __init__(self) -> None:
        super().__init__(6028, "Discount token not found")

    code = 6028
    name = "DiscountTokenNotFound"
    msg = "Discount token not found"


class ReferrerNotFound(ProgramError):
    def __init__(self) -> None:
        super().__init__(6029, "Referrer not found")

    code = 6029
    name = "ReferrerNotFound"
    msg = "Referrer not found"


class ReferrerStatsNotFound(ProgramError):
    def __init__(self) -> None:
        super().__init__(6030, "ReferrerNotFound")

    code = 6030
    name = "ReferrerStatsNotFound"
    msg = "ReferrerNotFound"


class ReferrerMustBeWritable(ProgramError):
    def __init__(self) -> None:
        super().__init__(6031, "ReferrerMustBeWritable")

    code = 6031
    name = "ReferrerMustBeWritable"
    msg = "ReferrerMustBeWritable"


class ReferrerStatsMustBeWritable(ProgramError):
    def __init__(self) -> None:
        super().__init__(6032, "ReferrerMustBeWritable")

    code = 6032
    name = "ReferrerStatsMustBeWritable"
    msg = "ReferrerMustBeWritable"


class ReferrerAndReferrerStatsAuthorityUnequal(ProgramError):
    def __init__(self) -> None:
        super().__init__(6033, "ReferrerAndReferrerStatsAuthorityUnequal")

    code = 6033
    name = "ReferrerAndReferrerStatsAuthorityUnequal"
    msg = "ReferrerAndReferrerStatsAuthorityUnequal"


class InvalidReferrer(ProgramError):
    def __init__(self) -> None:
        super().__init__(6034, "InvalidReferrer")

    code = 6034
    name = "InvalidReferrer"
    msg = "InvalidReferrer"


class InvalidOracle(ProgramError):
    def __init__(self) -> None:
        super().__init__(6035, "InvalidOracle")

    code = 6035
    name = "InvalidOracle"
    msg = "InvalidOracle"


class OracleNotFound(ProgramError):
    def __init__(self) -> None:
        super().__init__(6036, "OracleNotFound")

    code = 6036
    name = "OracleNotFound"
    msg = "OracleNotFound"


class LiquidationsBlockedByOracle(ProgramError):
    def __init__(self) -> None:
        super().__init__(6037, "Liquidations Blocked By Oracle")

    code = 6037
    name = "LiquidationsBlockedByOracle"
    msg = "Liquidations Blocked By Oracle"


class MaxDeposit(ProgramError):
    def __init__(self) -> None:
        super().__init__(6038, "Can not deposit more than max deposit")

    code = 6038
    name = "MaxDeposit"
    msg = "Can not deposit more than max deposit"


class CantDeleteUserWithCollateral(ProgramError):
    def __init__(self) -> None:
        super().__init__(6039, "Can not delete user that still has collateral")

    code = 6039
    name = "CantDeleteUserWithCollateral"
    msg = "Can not delete user that still has collateral"


class InvalidFundingProfitability(ProgramError):
    def __init__(self) -> None:
        super().__init__(6040, "AMM funding out of bounds pnl")

    code = 6040
    name = "InvalidFundingProfitability"
    msg = "AMM funding out of bounds pnl"


class CastingFailure(ProgramError):
    def __init__(self) -> None:
        super().__init__(6041, "Casting Failure")

    code = 6041
    name = "CastingFailure"
    msg = "Casting Failure"


class InvalidOrder(ProgramError):
    def __init__(self) -> None:
        super().__init__(6042, "Invalid Order")

    code = 6042
    name = "InvalidOrder"
    msg = "Invalid Order"


class UserHasNoOrder(ProgramError):
    def __init__(self) -> None:
        super().__init__(6043, "User has no order")

    code = 6043
    name = "UserHasNoOrder"
    msg = "User has no order"


class OrderAmountTooSmall(ProgramError):
    def __init__(self) -> None:
        super().__init__(6044, "Order Amount Too Small")

    code = 6044
    name = "OrderAmountTooSmall"
    msg = "Order Amount Too Small"


class MaxNumberOfOrders(ProgramError):
    def __init__(self) -> None:
        super().__init__(6045, "Max number of orders taken")

    code = 6045
    name = "MaxNumberOfOrders"
    msg = "Max number of orders taken"


class OrderDoesNotExist(ProgramError):
    def __init__(self) -> None:
        super().__init__(6046, "Order does not exist")

    code = 6046
    name = "OrderDoesNotExist"
    msg = "Order does not exist"


class OrderNotOpen(ProgramError):
    def __init__(self) -> None:
        super().__init__(6047, "Order not open")

    code = 6047
    name = "OrderNotOpen"
    msg = "Order not open"


class FillOrderDidNotUpdateState(ProgramError):
    def __init__(self) -> None:
        super().__init__(6048, "FillOrderDidNotUpdateState")

    code = 6048
    name = "FillOrderDidNotUpdateState"
    msg = "FillOrderDidNotUpdateState"


class ReduceOnlyOrderIncreasedRisk(ProgramError):
    def __init__(self) -> None:
        super().__init__(6049, "Reduce only order increased risk")

    code = 6049
    name = "ReduceOnlyOrderIncreasedRisk"
    msg = "Reduce only order increased risk"


class UnableToLoadAccountLoader(ProgramError):
    def __init__(self) -> None:
        super().__init__(6050, "Unable to load AccountLoader")

    code = 6050
    name = "UnableToLoadAccountLoader"
    msg = "Unable to load AccountLoader"


class TradeSizeTooLarge(ProgramError):
    def __init__(self) -> None:
        super().__init__(6051, "Trade Size Too Large")

    code = 6051
    name = "TradeSizeTooLarge"
    msg = "Trade Size Too Large"


class UserCantReferThemselves(ProgramError):
    def __init__(self) -> None:
        super().__init__(6052, "User cant refer themselves")

    code = 6052
    name = "UserCantReferThemselves"
    msg = "User cant refer themselves"


class DidNotReceiveExpectedReferrer(ProgramError):
    def __init__(self) -> None:
        super().__init__(6053, "Did not receive expected referrer")

    code = 6053
    name = "DidNotReceiveExpectedReferrer"
    msg = "Did not receive expected referrer"


class CouldNotDeserializeReferrer(ProgramError):
    def __init__(self) -> None:
        super().__init__(6054, "Could not deserialize referrer")

    code = 6054
    name = "CouldNotDeserializeReferrer"
    msg = "Could not deserialize referrer"


class CouldNotDeserializeReferrerStats(ProgramError):
    def __init__(self) -> None:
        super().__init__(6055, "Could not deserialize referrer stats")

    code = 6055
    name = "CouldNotDeserializeReferrerStats"
    msg = "Could not deserialize referrer stats"


class UserOrderIdAlreadyInUse(ProgramError):
    def __init__(self) -> None:
        super().__init__(6056, "User Order Id Already In Use")

    code = 6056
    name = "UserOrderIdAlreadyInUse"
    msg = "User Order Id Already In Use"


class NoPositionsLiquidatable(ProgramError):
    def __init__(self) -> None:
        super().__init__(6057, "No positions liquidatable")

    code = 6057
    name = "NoPositionsLiquidatable"
    msg = "No positions liquidatable"


class InvalidMarginRatio(ProgramError):
    def __init__(self) -> None:
        super().__init__(6058, "Invalid Margin Ratio")

    code = 6058
    name = "InvalidMarginRatio"
    msg = "Invalid Margin Ratio"


class CantCancelPostOnlyOrder(ProgramError):
    def __init__(self) -> None:
        super().__init__(6059, "Cant Cancel Post Only Order")

    code = 6059
    name = "CantCancelPostOnlyOrder"
    msg = "Cant Cancel Post Only Order"


class InvalidOracleOffset(ProgramError):
    def __init__(self) -> None:
        super().__init__(6060, "InvalidOracleOffset")

    code = 6060
    name = "InvalidOracleOffset"
    msg = "InvalidOracleOffset"


class CantExpireOrders(ProgramError):
    def __init__(self) -> None:
        super().__init__(6061, "CantExpireOrders")

    code = 6061
    name = "CantExpireOrders"
    msg = "CantExpireOrders"


class CouldNotLoadMarketData(ProgramError):
    def __init__(self) -> None:
        super().__init__(6062, "CouldNotLoadMarketData")

    code = 6062
    name = "CouldNotLoadMarketData"
    msg = "CouldNotLoadMarketData"


class MarketNotFound(ProgramError):
    def __init__(self) -> None:
        super().__init__(6063, "MarketNotFound")

    code = 6063
    name = "MarketNotFound"
    msg = "MarketNotFound"


class InvalidMarketAccount(ProgramError):
    def __init__(self) -> None:
        super().__init__(6064, "InvalidMarketAccount")

    code = 6064
    name = "InvalidMarketAccount"
    msg = "InvalidMarketAccount"


class UnableToLoadMarketAccount(ProgramError):
    def __init__(self) -> None:
        super().__init__(6065, "UnableToLoadMarketAccount")

    code = 6065
    name = "UnableToLoadMarketAccount"
    msg = "UnableToLoadMarketAccount"


class MarketWrongMutability(ProgramError):
    def __init__(self) -> None:
        super().__init__(6066, "MarketWrongMutability")

    code = 6066
    name = "MarketWrongMutability"
    msg = "MarketWrongMutability"


class UnableToCastUnixTime(ProgramError):
    def __init__(self) -> None:
        super().__init__(6067, "UnableToCastUnixTime")

    code = 6067
    name = "UnableToCastUnixTime"
    msg = "UnableToCastUnixTime"


class CouldNotFindSpotPosition(ProgramError):
    def __init__(self) -> None:
        super().__init__(6068, "CouldNotFindSpotPosition")

    code = 6068
    name = "CouldNotFindSpotPosition"
    msg = "CouldNotFindSpotPosition"


class NoSpotPositionAvailable(ProgramError):
    def __init__(self) -> None:
        super().__init__(6069, "NoSpotPositionAvailable")

    code = 6069
    name = "NoSpotPositionAvailable"
    msg = "NoSpotPositionAvailable"


class InvalidSpotMarketInitialization(ProgramError):
    def __init__(self) -> None:
        super().__init__(6070, "InvalidSpotMarketInitialization")

    code = 6070
    name = "InvalidSpotMarketInitialization"
    msg = "InvalidSpotMarketInitialization"


class CouldNotLoadSpotMarketData(ProgramError):
    def __init__(self) -> None:
        super().__init__(6071, "CouldNotLoadSpotMarketData")

    code = 6071
    name = "CouldNotLoadSpotMarketData"
    msg = "CouldNotLoadSpotMarketData"


class SpotMarketNotFound(ProgramError):
    def __init__(self) -> None:
        super().__init__(6072, "SpotMarketNotFound")

    code = 6072
    name = "SpotMarketNotFound"
    msg = "SpotMarketNotFound"


class InvalidSpotMarketAccount(ProgramError):
    def __init__(self) -> None:
        super().__init__(6073, "InvalidSpotMarketAccount")

    code = 6073
    name = "InvalidSpotMarketAccount"
    msg = "InvalidSpotMarketAccount"


class UnableToLoadSpotMarketAccount(ProgramError):
    def __init__(self) -> None:
        super().__init__(6074, "UnableToLoadSpotMarketAccount")

    code = 6074
    name = "UnableToLoadSpotMarketAccount"
    msg = "UnableToLoadSpotMarketAccount"


class SpotMarketWrongMutability(ProgramError):
    def __init__(self) -> None:
        super().__init__(6075, "SpotMarketWrongMutability")

    code = 6075
    name = "SpotMarketWrongMutability"
    msg = "SpotMarketWrongMutability"


class SpotMarketInterestNotUpToDate(ProgramError):
    def __init__(self) -> None:
        super().__init__(6076, "SpotInterestNotUpToDate")

    code = 6076
    name = "SpotMarketInterestNotUpToDate"
    msg = "SpotInterestNotUpToDate"


class SpotMarketInsufficientDeposits(ProgramError):
    def __init__(self) -> None:
        super().__init__(6077, "SpotMarketInsufficientDeposits")

    code = 6077
    name = "SpotMarketInsufficientDeposits"
    msg = "SpotMarketInsufficientDeposits"


class UserMustSettleTheirOwnPositiveUnsettledPNL(ProgramError):
    def __init__(self) -> None:
        super().__init__(6078, "UserMustSettleTheirOwnPositiveUnsettledPNL")

    code = 6078
    name = "UserMustSettleTheirOwnPositiveUnsettledPNL"
    msg = "UserMustSettleTheirOwnPositiveUnsettledPNL"


class CantUpdatePoolBalanceType(ProgramError):
    def __init__(self) -> None:
        super().__init__(6079, "CantUpdatePoolBalanceType")

    code = 6079
    name = "CantUpdatePoolBalanceType"
    msg = "CantUpdatePoolBalanceType"


class InsufficientCollateralForSettlingPNL(ProgramError):
    def __init__(self) -> None:
        super().__init__(6080, "InsufficientCollateralForSettlingPNL")

    code = 6080
    name = "InsufficientCollateralForSettlingPNL"
    msg = "InsufficientCollateralForSettlingPNL"


class AMMNotUpdatedInSameSlot(ProgramError):
    def __init__(self) -> None:
        super().__init__(6081, "AMMNotUpdatedInSameSlot")

    code = 6081
    name = "AMMNotUpdatedInSameSlot"
    msg = "AMMNotUpdatedInSameSlot"


class AuctionNotComplete(ProgramError):
    def __init__(self) -> None:
        super().__init__(6082, "AuctionNotComplete")

    code = 6082
    name = "AuctionNotComplete"
    msg = "AuctionNotComplete"


class MakerNotFound(ProgramError):
    def __init__(self) -> None:
        super().__init__(6083, "MakerNotFound")

    code = 6083
    name = "MakerNotFound"
    msg = "MakerNotFound"


class MakerStatsNotFound(ProgramError):
    def __init__(self) -> None:
        super().__init__(6084, "MakerNotFound")

    code = 6084
    name = "MakerStatsNotFound"
    msg = "MakerNotFound"


class MakerMustBeWritable(ProgramError):
    def __init__(self) -> None:
        super().__init__(6085, "MakerMustBeWritable")

    code = 6085
    name = "MakerMustBeWritable"
    msg = "MakerMustBeWritable"


class MakerStatsMustBeWritable(ProgramError):
    def __init__(self) -> None:
        super().__init__(6086, "MakerMustBeWritable")

    code = 6086
    name = "MakerStatsMustBeWritable"
    msg = "MakerMustBeWritable"


class MakerOrderNotFound(ProgramError):
    def __init__(self) -> None:
        super().__init__(6087, "MakerOrderNotFound")

    code = 6087
    name = "MakerOrderNotFound"
    msg = "MakerOrderNotFound"


class CouldNotDeserializeMaker(ProgramError):
    def __init__(self) -> None:
        super().__init__(6088, "CouldNotDeserializeMaker")

    code = 6088
    name = "CouldNotDeserializeMaker"
    msg = "CouldNotDeserializeMaker"


class CouldNotDeserializeMakerStats(ProgramError):
    def __init__(self) -> None:
        super().__init__(6089, "CouldNotDeserializeMaker")

    code = 6089
    name = "CouldNotDeserializeMakerStats"
    msg = "CouldNotDeserializeMaker"


class AuctionPriceDoesNotSatisfyMaker(ProgramError):
    def __init__(self) -> None:
        super().__init__(6090, "AuctionPriceDoesNotSatisfyMaker")

    code = 6090
    name = "AuctionPriceDoesNotSatisfyMaker"
    msg = "AuctionPriceDoesNotSatisfyMaker"


class MakerCantFulfillOwnOrder(ProgramError):
    def __init__(self) -> None:
        super().__init__(6091, "MakerCantFulfillOwnOrder")

    code = 6091
    name = "MakerCantFulfillOwnOrder"
    msg = "MakerCantFulfillOwnOrder"


class MakerOrderMustBePostOnly(ProgramError):
    def __init__(self) -> None:
        super().__init__(6092, "MakerOrderMustBePostOnly")

    code = 6092
    name = "MakerOrderMustBePostOnly"
    msg = "MakerOrderMustBePostOnly"


class CantMatchTwoPostOnlys(ProgramError):
    def __init__(self) -> None:
        super().__init__(6093, "CantMatchTwoPostOnlys")

    code = 6093
    name = "CantMatchTwoPostOnlys"
    msg = "CantMatchTwoPostOnlys"


class OrderBreachesOraclePriceLimits(ProgramError):
    def __init__(self) -> None:
        super().__init__(6094, "OrderBreachesOraclePriceLimits")

    code = 6094
    name = "OrderBreachesOraclePriceLimits"
    msg = "OrderBreachesOraclePriceLimits"


class OrderMustBeTriggeredFirst(ProgramError):
    def __init__(self) -> None:
        super().__init__(6095, "OrderMustBeTriggeredFirst")

    code = 6095
    name = "OrderMustBeTriggeredFirst"
    msg = "OrderMustBeTriggeredFirst"


class OrderNotTriggerable(ProgramError):
    def __init__(self) -> None:
        super().__init__(6096, "OrderNotTriggerable")

    code = 6096
    name = "OrderNotTriggerable"
    msg = "OrderNotTriggerable"


class OrderDidNotSatisfyTriggerCondition(ProgramError):
    def __init__(self) -> None:
        super().__init__(6097, "OrderDidNotSatisfyTriggerCondition")

    code = 6097
    name = "OrderDidNotSatisfyTriggerCondition"
    msg = "OrderDidNotSatisfyTriggerCondition"


class PositionAlreadyBeingLiquidated(ProgramError):
    def __init__(self) -> None:
        super().__init__(6098, "PositionAlreadyBeingLiquidated")

    code = 6098
    name = "PositionAlreadyBeingLiquidated"
    msg = "PositionAlreadyBeingLiquidated"


class PositionDoesntHaveOpenPositionOrOrders(ProgramError):
    def __init__(self) -> None:
        super().__init__(6099, "PositionDoesntHaveOpenPositionOrOrders")

    code = 6099
    name = "PositionDoesntHaveOpenPositionOrOrders"
    msg = "PositionDoesntHaveOpenPositionOrOrders"


class AllOrdersAreAlreadyLiquidations(ProgramError):
    def __init__(self) -> None:
        super().__init__(6100, "AllOrdersAreAlreadyLiquidations")

    code = 6100
    name = "AllOrdersAreAlreadyLiquidations"
    msg = "AllOrdersAreAlreadyLiquidations"


class CantCancelLiquidationOrder(ProgramError):
    def __init__(self) -> None:
        super().__init__(6101, "CantCancelLiquidationOrder")

    code = 6101
    name = "CantCancelLiquidationOrder"
    msg = "CantCancelLiquidationOrder"


class UserIsBeingLiquidated(ProgramError):
    def __init__(self) -> None:
        super().__init__(6102, "UserIsBeingLiquidated")

    code = 6102
    name = "UserIsBeingLiquidated"
    msg = "UserIsBeingLiquidated"


class LiquidationsOngoing(ProgramError):
    def __init__(self) -> None:
        super().__init__(6103, "LiquidationsOngoing")

    code = 6103
    name = "LiquidationsOngoing"
    msg = "LiquidationsOngoing"


class WrongSpotBalanceType(ProgramError):
    def __init__(self) -> None:
        super().__init__(6104, "WrongSpotBalanceType")

    code = 6104
    name = "WrongSpotBalanceType"
    msg = "WrongSpotBalanceType"


class UserCantLiquidateThemself(ProgramError):
    def __init__(self) -> None:
        super().__init__(6105, "UserCantLiquidateThemself")

    code = 6105
    name = "UserCantLiquidateThemself"
    msg = "UserCantLiquidateThemself"


class InvalidPerpPositionToLiquidate(ProgramError):
    def __init__(self) -> None:
        super().__init__(6106, "InvalidPerpPositionToLiquidate")

    code = 6106
    name = "InvalidPerpPositionToLiquidate"
    msg = "InvalidPerpPositionToLiquidate"


class InvalidBaseAssetAmountForLiquidatePerp(ProgramError):
    def __init__(self) -> None:
        super().__init__(6107, "InvalidBaseAssetAmountForLiquidatePerp")

    code = 6107
    name = "InvalidBaseAssetAmountForLiquidatePerp"
    msg = "InvalidBaseAssetAmountForLiquidatePerp"


class InvalidPositionLastFundingRate(ProgramError):
    def __init__(self) -> None:
        super().__init__(6108, "InvalidPositionLastFundingRate")

    code = 6108
    name = "InvalidPositionLastFundingRate"
    msg = "InvalidPositionLastFundingRate"


class InvalidPositionDelta(ProgramError):
    def __init__(self) -> None:
        super().__init__(6109, "InvalidPositionDelta")

    code = 6109
    name = "InvalidPositionDelta"
    msg = "InvalidPositionDelta"


class UserBankrupt(ProgramError):
    def __init__(self) -> None:
        super().__init__(6110, "UserBankrupt")

    code = 6110
    name = "UserBankrupt"
    msg = "UserBankrupt"


class UserNotBankrupt(ProgramError):
    def __init__(self) -> None:
        super().__init__(6111, "UserNotBankrupt")

    code = 6111
    name = "UserNotBankrupt"
    msg = "UserNotBankrupt"


class UserHasInvalidBorrow(ProgramError):
    def __init__(self) -> None:
        super().__init__(6112, "UserHasInvalidBorrow")

    code = 6112
    name = "UserHasInvalidBorrow"
    msg = "UserHasInvalidBorrow"


class DailyWithdrawLimit(ProgramError):
    def __init__(self) -> None:
        super().__init__(6113, "DailyWithdrawLimit")

    code = 6113
    name = "DailyWithdrawLimit"
    msg = "DailyWithdrawLimit"


class DefaultError(ProgramError):
    def __init__(self) -> None:
        super().__init__(6114, "DefaultError")

    code = 6114
    name = "DefaultError"
    msg = "DefaultError"


class InsufficientLPTokens(ProgramError):
    def __init__(self) -> None:
        super().__init__(6115, "Insufficient LP tokens")

    code = 6115
    name = "InsufficientLPTokens"
    msg = "Insufficient LP tokens"


class CantLPWithPerpPosition(ProgramError):
    def __init__(self) -> None:
        super().__init__(6116, "Cant LP with a market position")

    code = 6116
    name = "CantLPWithPerpPosition"
    msg = "Cant LP with a market position"


class UnableToBurnLPTokens(ProgramError):
    def __init__(self) -> None:
        super().__init__(6117, "Unable to burn LP tokens")

    code = 6117
    name = "UnableToBurnLPTokens"
    msg = "Unable to burn LP tokens"


class TryingToRemoveLiquidityTooFast(ProgramError):
    def __init__(self) -> None:
        super().__init__(6118, "Trying to remove liqudity too fast after adding it")

    code = 6118
    name = "TryingToRemoveLiquidityTooFast"
    msg = "Trying to remove liqudity too fast after adding it"


class InvalidSpotMarketVault(ProgramError):
    def __init__(self) -> None:
        super().__init__(6119, "Invalid Spot Market Vault")

    code = 6119
    name = "InvalidSpotMarketVault"
    msg = "Invalid Spot Market Vault"


class InvalidSpotMarketState(ProgramError):
    def __init__(self) -> None:
        super().__init__(6120, "Invalid Spot Market State")

    code = 6120
    name = "InvalidSpotMarketState"
    msg = "Invalid Spot Market State"


class InvalidSerumProgram(ProgramError):
    def __init__(self) -> None:
        super().__init__(6121, "InvalidSerumProgram")

    code = 6121
    name = "InvalidSerumProgram"
    msg = "InvalidSerumProgram"


class InvalidSerumMarket(ProgramError):
    def __init__(self) -> None:
        super().__init__(6122, "InvalidSerumMarket")

    code = 6122
    name = "InvalidSerumMarket"
    msg = "InvalidSerumMarket"


class InvalidSerumBids(ProgramError):
    def __init__(self) -> None:
        super().__init__(6123, "InvalidSerumBids")

    code = 6123
    name = "InvalidSerumBids"
    msg = "InvalidSerumBids"


class InvalidSerumAsks(ProgramError):
    def __init__(self) -> None:
        super().__init__(6124, "InvalidSerumAsks")

    code = 6124
    name = "InvalidSerumAsks"
    msg = "InvalidSerumAsks"


class InvalidSerumOpenOrders(ProgramError):
    def __init__(self) -> None:
        super().__init__(6125, "InvalidSerumOpenOrders")

    code = 6125
    name = "InvalidSerumOpenOrders"
    msg = "InvalidSerumOpenOrders"


class FailedSerumCPI(ProgramError):
    def __init__(self) -> None:
        super().__init__(6126, "FailedSerumCPI")

    code = 6126
    name = "FailedSerumCPI"
    msg = "FailedSerumCPI"


class FailedToFillOnSerum(ProgramError):
    def __init__(self) -> None:
        super().__init__(6127, "FailedToFillOnSerum")

    code = 6127
    name = "FailedToFillOnSerum"
    msg = "FailedToFillOnSerum"


class InvalidSerumFulfillmentConfig(ProgramError):
    def __init__(self) -> None:
        super().__init__(6128, "InvalidSerumFulfillmentConfig")

    code = 6128
    name = "InvalidSerumFulfillmentConfig"
    msg = "InvalidSerumFulfillmentConfig"


class InvalidFeeStructure(ProgramError):
    def __init__(self) -> None:
        super().__init__(6129, "InvalidFeeStructure")

    code = 6129
    name = "InvalidFeeStructure"
    msg = "InvalidFeeStructure"


class InsufficientIFShares(ProgramError):
    def __init__(self) -> None:
        super().__init__(6130, "Insufficient IF shares")

    code = 6130
    name = "InsufficientIFShares"
    msg = "Insufficient IF shares"


class MarketActionPaused(ProgramError):
    def __init__(self) -> None:
        super().__init__(6131, "the Market has paused this action")

    code = 6131
    name = "MarketActionPaused"
    msg = "the Market has paused this action"


class AssetTierViolation(ProgramError):
    def __init__(self) -> None:
        super().__init__(6132, "Action violates the asset tier rules")

    code = 6132
    name = "AssetTierViolation"
    msg = "Action violates the asset tier rules"


class UserCantBeDeleted(ProgramError):
    def __init__(self) -> None:
        super().__init__(6133, "User Cant Be Deleted")

    code = 6133
    name = "UserCantBeDeleted"
    msg = "User Cant Be Deleted"


class ReduceOnlyWithdrawIncreasedRisk(ProgramError):
    def __init__(self) -> None:
        super().__init__(6134, "Reduce Only Withdraw Increased Risk")

    code = 6134
    name = "ReduceOnlyWithdrawIncreasedRisk"
    msg = "Reduce Only Withdraw Increased Risk"


CustomError = typing.Union[
    InvalidSpotMarketAuthority,
    InvalidInsuranceFundAuthority,
    InsufficientDeposit,
    InsufficientCollateral,
    SufficientCollateral,
    MaxNumberOfPositions,
    AdminControlsPricesDisabled,
    MarketIndexNotInitialized,
    MarketIndexAlreadyInitialized,
    UserAccountAndUserPositionsAccountMismatch,
    UserHasNoPositionInMarket,
    InvalidInitialPeg,
    InvalidRepegRedundant,
    InvalidRepegDirection,
    InvalidRepegProfitability,
    SlippageOutsideLimit,
    OrderSizeTooSmall,
    InvalidUpdateK,
    AdminWithdrawTooLarge,
    MathError,
    BnConversionError,
    ClockUnavailable,
    UnableToLoadOracle,
    PriceBandsBreached,
    ExchangePaused,
    InvalidWhitelistToken,
    WhitelistTokenNotFound,
    InvalidDiscountToken,
    DiscountTokenNotFound,
    ReferrerNotFound,
    ReferrerStatsNotFound,
    ReferrerMustBeWritable,
    ReferrerStatsMustBeWritable,
    ReferrerAndReferrerStatsAuthorityUnequal,
    InvalidReferrer,
    InvalidOracle,
    OracleNotFound,
    LiquidationsBlockedByOracle,
    MaxDeposit,
    CantDeleteUserWithCollateral,
    InvalidFundingProfitability,
    CastingFailure,
    InvalidOrder,
    UserHasNoOrder,
    OrderAmountTooSmall,
    MaxNumberOfOrders,
    OrderDoesNotExist,
    OrderNotOpen,
    FillOrderDidNotUpdateState,
    ReduceOnlyOrderIncreasedRisk,
    UnableToLoadAccountLoader,
    TradeSizeTooLarge,
    UserCantReferThemselves,
    DidNotReceiveExpectedReferrer,
    CouldNotDeserializeReferrer,
    CouldNotDeserializeReferrerStats,
    UserOrderIdAlreadyInUse,
    NoPositionsLiquidatable,
    InvalidMarginRatio,
    CantCancelPostOnlyOrder,
    InvalidOracleOffset,
    CantExpireOrders,
    CouldNotLoadMarketData,
    MarketNotFound,
    InvalidMarketAccount,
    UnableToLoadMarketAccount,
    MarketWrongMutability,
    UnableToCastUnixTime,
    CouldNotFindSpotPosition,
    NoSpotPositionAvailable,
    InvalidSpotMarketInitialization,
    CouldNotLoadSpotMarketData,
    SpotMarketNotFound,
    InvalidSpotMarketAccount,
    UnableToLoadSpotMarketAccount,
    SpotMarketWrongMutability,
    SpotMarketInterestNotUpToDate,
    SpotMarketInsufficientDeposits,
    UserMustSettleTheirOwnPositiveUnsettledPNL,
    CantUpdatePoolBalanceType,
    InsufficientCollateralForSettlingPNL,
    AMMNotUpdatedInSameSlot,
    AuctionNotComplete,
    MakerNotFound,
    MakerStatsNotFound,
    MakerMustBeWritable,
    MakerStatsMustBeWritable,
    MakerOrderNotFound,
    CouldNotDeserializeMaker,
    CouldNotDeserializeMakerStats,
    AuctionPriceDoesNotSatisfyMaker,
    MakerCantFulfillOwnOrder,
    MakerOrderMustBePostOnly,
    CantMatchTwoPostOnlys,
    OrderBreachesOraclePriceLimits,
    OrderMustBeTriggeredFirst,
    OrderNotTriggerable,
    OrderDidNotSatisfyTriggerCondition,
    PositionAlreadyBeingLiquidated,
    PositionDoesntHaveOpenPositionOrOrders,
    AllOrdersAreAlreadyLiquidations,
    CantCancelLiquidationOrder,
    UserIsBeingLiquidated,
    LiquidationsOngoing,
    WrongSpotBalanceType,
    UserCantLiquidateThemself,
    InvalidPerpPositionToLiquidate,
    InvalidBaseAssetAmountForLiquidatePerp,
    InvalidPositionLastFundingRate,
    InvalidPositionDelta,
    UserBankrupt,
    UserNotBankrupt,
    UserHasInvalidBorrow,
    DailyWithdrawLimit,
    DefaultError,
    InsufficientLPTokens,
    CantLPWithPerpPosition,
    UnableToBurnLPTokens,
    TryingToRemoveLiquidityTooFast,
    InvalidSpotMarketVault,
    InvalidSpotMarketState,
    InvalidSerumProgram,
    InvalidSerumMarket,
    InvalidSerumBids,
    InvalidSerumAsks,
    InvalidSerumOpenOrders,
    FailedSerumCPI,
    FailedToFillOnSerum,
    InvalidSerumFulfillmentConfig,
    InvalidFeeStructure,
    InsufficientIFShares,
    MarketActionPaused,
    AssetTierViolation,
    UserCantBeDeleted,
    ReduceOnlyWithdrawIncreasedRisk,
]
CUSTOM_ERROR_MAP: dict[int, CustomError] = {
    6000: InvalidSpotMarketAuthority(),
    6001: InvalidInsuranceFundAuthority(),
    6002: InsufficientDeposit(),
    6003: InsufficientCollateral(),
    6004: SufficientCollateral(),
    6005: MaxNumberOfPositions(),
    6006: AdminControlsPricesDisabled(),
    6007: MarketIndexNotInitialized(),
    6008: MarketIndexAlreadyInitialized(),
    6009: UserAccountAndUserPositionsAccountMismatch(),
    6010: UserHasNoPositionInMarket(),
    6011: InvalidInitialPeg(),
    6012: InvalidRepegRedundant(),
    6013: InvalidRepegDirection(),
    6014: InvalidRepegProfitability(),
    6015: SlippageOutsideLimit(),
    6016: OrderSizeTooSmall(),
    6017: InvalidUpdateK(),
    6018: AdminWithdrawTooLarge(),
    6019: MathError(),
    6020: BnConversionError(),
    6021: ClockUnavailable(),
    6022: UnableToLoadOracle(),
    6023: PriceBandsBreached(),
    6024: ExchangePaused(),
    6025: InvalidWhitelistToken(),
    6026: WhitelistTokenNotFound(),
    6027: InvalidDiscountToken(),
    6028: DiscountTokenNotFound(),
    6029: ReferrerNotFound(),
    6030: ReferrerStatsNotFound(),
    6031: ReferrerMustBeWritable(),
    6032: ReferrerStatsMustBeWritable(),
    6033: ReferrerAndReferrerStatsAuthorityUnequal(),
    6034: InvalidReferrer(),
    6035: InvalidOracle(),
    6036: OracleNotFound(),
    6037: LiquidationsBlockedByOracle(),
    6038: MaxDeposit(),
    6039: CantDeleteUserWithCollateral(),
    6040: InvalidFundingProfitability(),
    6041: CastingFailure(),
    6042: InvalidOrder(),
    6043: UserHasNoOrder(),
    6044: OrderAmountTooSmall(),
    6045: MaxNumberOfOrders(),
    6046: OrderDoesNotExist(),
    6047: OrderNotOpen(),
    6048: FillOrderDidNotUpdateState(),
    6049: ReduceOnlyOrderIncreasedRisk(),
    6050: UnableToLoadAccountLoader(),
    6051: TradeSizeTooLarge(),
    6052: UserCantReferThemselves(),
    6053: DidNotReceiveExpectedReferrer(),
    6054: CouldNotDeserializeReferrer(),
    6055: CouldNotDeserializeReferrerStats(),
    6056: UserOrderIdAlreadyInUse(),
    6057: NoPositionsLiquidatable(),
    6058: InvalidMarginRatio(),
    6059: CantCancelPostOnlyOrder(),
    6060: InvalidOracleOffset(),
    6061: CantExpireOrders(),
    6062: CouldNotLoadMarketData(),
    6063: MarketNotFound(),
    6064: InvalidMarketAccount(),
    6065: UnableToLoadMarketAccount(),
    6066: MarketWrongMutability(),
    6067: UnableToCastUnixTime(),
    6068: CouldNotFindSpotPosition(),
    6069: NoSpotPositionAvailable(),
    6070: InvalidSpotMarketInitialization(),
    6071: CouldNotLoadSpotMarketData(),
    6072: SpotMarketNotFound(),
    6073: InvalidSpotMarketAccount(),
    6074: UnableToLoadSpotMarketAccount(),
    6075: SpotMarketWrongMutability(),
    6076: SpotMarketInterestNotUpToDate(),
    6077: SpotMarketInsufficientDeposits(),
    6078: UserMustSettleTheirOwnPositiveUnsettledPNL(),
    6079: CantUpdatePoolBalanceType(),
    6080: InsufficientCollateralForSettlingPNL(),
    6081: AMMNotUpdatedInSameSlot(),
    6082: AuctionNotComplete(),
    6083: MakerNotFound(),
    6084: MakerStatsNotFound(),
    6085: MakerMustBeWritable(),
    6086: MakerStatsMustBeWritable(),
    6087: MakerOrderNotFound(),
    6088: CouldNotDeserializeMaker(),
    6089: CouldNotDeserializeMakerStats(),
    6090: AuctionPriceDoesNotSatisfyMaker(),
    6091: MakerCantFulfillOwnOrder(),
    6092: MakerOrderMustBePostOnly(),
    6093: CantMatchTwoPostOnlys(),
    6094: OrderBreachesOraclePriceLimits(),
    6095: OrderMustBeTriggeredFirst(),
    6096: OrderNotTriggerable(),
    6097: OrderDidNotSatisfyTriggerCondition(),
    6098: PositionAlreadyBeingLiquidated(),
    6099: PositionDoesntHaveOpenPositionOrOrders(),
    6100: AllOrdersAreAlreadyLiquidations(),
    6101: CantCancelLiquidationOrder(),
    6102: UserIsBeingLiquidated(),
    6103: LiquidationsOngoing(),
    6104: WrongSpotBalanceType(),
    6105: UserCantLiquidateThemself(),
    6106: InvalidPerpPositionToLiquidate(),
    6107: InvalidBaseAssetAmountForLiquidatePerp(),
    6108: InvalidPositionLastFundingRate(),
    6109: InvalidPositionDelta(),
    6110: UserBankrupt(),
    6111: UserNotBankrupt(),
    6112: UserHasInvalidBorrow(),
    6113: DailyWithdrawLimit(),
    6114: DefaultError(),
    6115: InsufficientLPTokens(),
    6116: CantLPWithPerpPosition(),
    6117: UnableToBurnLPTokens(),
    6118: TryingToRemoveLiquidityTooFast(),
    6119: InvalidSpotMarketVault(),
    6120: InvalidSpotMarketState(),
    6121: InvalidSerumProgram(),
    6122: InvalidSerumMarket(),
    6123: InvalidSerumBids(),
    6124: InvalidSerumAsks(),
    6125: InvalidSerumOpenOrders(),
    6126: FailedSerumCPI(),
    6127: FailedToFillOnSerum(),
    6128: InvalidSerumFulfillmentConfig(),
    6129: InvalidFeeStructure(),
    6130: InsufficientIFShares(),
    6131: MarketActionPaused(),
    6132: AssetTierViolation(),
    6133: UserCantBeDeleted(),
    6134: ReduceOnlyWithdrawIncreasedRisk(),
}


def from_code(code: int) -> typing.Optional[CustomError]:
    maybe_err = CUSTOM_ERROR_MAP.get(code)
    if maybe_err is None:
        return None
    return maybe_err
