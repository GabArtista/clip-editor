from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import User, WalletAccount, WalletTransaction, WalletTransactionType


@dataclass
class WalletSnapshot:
    balance_credits: Decimal
    currency: str


class InsufficientCreditsError(Exception):
    def __init__(self, required: Decimal, available: Decimal):
        super().__init__("Saldo insuficiente para processar esta operação.")
        self.required = required
        self.available = available


class WalletManager:
    def __init__(self, db: Session):
        self.db = db

    def _to_decimal(self, value: Decimal | float | int | str) -> Decimal:
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))

    def get_or_create_account(self, user: User) -> WalletAccount:
        if user.wallet_account:
            return user.wallet_account
        account = WalletAccount(user_id=user.id)
        self.db.add(account)
        self.db.flush()
        self.db.refresh(account)
        return account

    def get_snapshot(self, user: User) -> WalletSnapshot:
        account = self.get_or_create_account(user)
        return WalletSnapshot(balance_credits=self._to_decimal(account.balance_credits), currency=account.currency)

    def _record_transaction(
        self,
        account: WalletAccount,
        tx_type: WalletTransactionType,
        amount: Decimal,
        description: str | None = None,
        reference_id: UUID | None = None,
    ) -> WalletTransaction:
        tx = WalletTransaction(
            wallet_account_id=account.id,
            transaction_type=tx_type,
            amount_credits=amount,
            description=description,
            reference_id=reference_id,
        )
        account.updated_at = datetime.now(timezone.utc)
        self.db.add(tx)
        self.db.flush()
        self.db.refresh(tx)
        return tx

    def deposit(self, user: User, amount: Decimal, description: str | None = None) -> WalletSnapshot:
        amount = self._to_decimal(amount)
        if amount <= 0:
            raise ValueError("Depósitos devem ser maiores que zero.")
        account = self.get_or_create_account(user)
        account.balance_credits = self._to_decimal(account.balance_credits) + amount
        self._record_transaction(account, WalletTransactionType.deposit, amount, description)
        return self.get_snapshot(user)

    def spend(
        self,
        user: User,
        amount: Decimal,
        description: str,
        reference_id: UUID | None = None,
    ) -> WalletTransaction:
        amount = self._to_decimal(amount)
        if amount <= 0:
            raise ValueError("Valores de consumo precisam ser positivos.")
        account = self.get_or_create_account(user)
        balance = self._to_decimal(account.balance_credits)
        if balance < amount:
            raise InsufficientCreditsError(required=amount, available=balance)
        account.balance_credits = balance - amount
        return self._record_transaction(account, WalletTransactionType.usage, amount, description, reference_id)

    def list_transactions(self, user: User, limit: int = 50) -> List[WalletTransaction]:
        account = self.get_or_create_account(user)
        return (
            self.db.query(WalletTransaction)
            .filter(WalletTransaction.wallet_account_id == account.id)
            .order_by(WalletTransaction.created_at.desc())
            .limit(limit)
            .all()
        )
