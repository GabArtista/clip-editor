from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.models import WalletTransactionType


class WalletDepositRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    description: Optional[str] = Field(default=None, max_length=255)


class WalletBalanceResponse(BaseModel):
    balance: Decimal
    currency: str


class WalletTransactionResponse(BaseModel):
    id: str
    transaction_type: WalletTransactionType
    amount_credits: Decimal
    description: Optional[str]
    created_at: datetime
