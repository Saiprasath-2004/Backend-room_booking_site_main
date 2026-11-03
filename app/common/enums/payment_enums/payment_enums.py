# ============================================================
# Standard Library
# ============================================================

from enum import Enum


# ============================================================
# Payment Status
# ============================================================

class PaymentStatus(str, Enum):
    """
    Represents the lifecycle of a payment.
    """

    PENDING = "PENDING"

    SUCCESS = "SUCCESS"

    FAILED = "FAILED"

    REFUNDED = "REFUNDED"

    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"


# ============================================================
# Payment Method
# ============================================================

class PaymentMethod(str, Enum):
    """
    Supported payment methods.
    """

    CREDIT_CARD = "CREDIT_CARD"

    DEBIT_CARD = "DEBIT_CARD"

    UPI = "UPI"

    NET_BANKING = "NET_BANKING"

    WALLET = "WALLET"


# ============================================================
# Payment Gateway
# ============================================================

class PaymentGateway(str, Enum):
    """
    Supported payment gateways.
    """

    RAZORPAY = "RAZORPAY"

    STRIPE = "STRIPE"

    PAYPAL = "PAYPAL"

    MANUAL = "MANUAL"


# ============================================================
# Invoice Status
# ============================================================

class InvoiceStatus(str, Enum):
    """
    Status of an invoice.
    """

    GENERATED = "GENERATED"

    CANCELLED = "CANCELLED"