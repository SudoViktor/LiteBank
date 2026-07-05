from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, select
from sqlalchemy.orm import relationship
from sqlalchemy.util import await_only

from app.database import Base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import random


def generate_ua_iban(bank_code: str = None, account_number: str = None) -> str:
    if not bank_code:
        bank_code = str(random.randint(300000, 399999))
    else:
        bank_code = bank_code.zfill(6)

    if not account_number:
        account_number = "".join([str(random.randint(0, 9)) for _ in range(19)])
    else:
        account_number = account_number.zfill(19)

    bban = bank_code + account_number
    numeric_string = bban + "301000"
    mod97 = int(numeric_string) % 97
    check_digits = 98 - mod97
    check_digits_str = f"{check_digits:02d}"
    full_iban = f"UA{check_digits_str}{bban}"

    return full_iban


def generate_card_number(bin_prefix="4149"):
    length = 15
    number = [int(x) for x in bin_prefix]
    number.extend([random.randint(0, 9) for _ in range(length - len(number))])

    checksum = 0
    for i, digit in enumerate(reversed(number)):
        if i % 2 == 0:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit

    check_digit = (10 - (checksum % 10)) % 10
    number.append(check_digit)
    return "".join(map(str, number))


def generate_cvv() -> str:
    return f"{random.randint(0, 999):03d}"


def generate_expiration_date(years_valid: int = 4) -> str:
    future_date = datetime.now() + timedelta(days=365 * years_valid)
    return future_date.strftime("%m/%y")


# alembic upgrade head && alembic revision --autogenerate -m "-"
class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    iban = Column(String, unique=True)
    cards = relationship("Card", back_populates="account", cascade="all, delete-orphan")

    def get_iban(self):
        return self.iban

    @staticmethod
    async def get_accounts_by_username(db: AsyncSession, username: str):
        query = select(Account).where(Account.username == username)
        result = await db.execute(query)
        existing_accounts = result.scalars().all()
        return existing_accounts

    @staticmethod
    async def get_account_by_iban(db: AsyncSession, iban: str):
        query = select(Account).where(Account.iban == iban)
        result = await db.execute(query)
        existing_account = result.scalar_one_or_none()
        return existing_account

    @staticmethod
    async def create_account(db: AsyncSession, username: str):

        while True:
            new_iban = generate_ua_iban()
            account = await Account.get_account_by_iban(db, new_iban)
            if not account: break


        new_account = Account(username=username, iban=new_iban)

        db.add(new_account)
        await db.commit()
        await db.refresh(new_account)
        return new_account


    async def get_active_cards_by_account(self, db: AsyncSession):
        query = select(Card).where(Card.account_id == self.id).where(Card.is_active == True)
        result = await db.execute(query)
        return result.all()


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    card_number = Column(String(16), unique=True, index=True, nullable=False)
    expiration_date = Column(String(5), nullable=False)
    cvv = Column(String(3), nullable=False)
    is_active = Column(Boolean, default=False)

    # Зворотний зв'язок з рахунком
    account = relationship("Account", back_populates="cards")

    @staticmethod
    async def get_card_by_number(db: AsyncSession, card_number: str):
        query = select(Card).where(Card.card_number == card_number)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_card_by_id(db: AsyncSession, card_id: int):
        query = select(Card).where(Card.id == card_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_active_cards_by_account_id(db: AsyncSession, account_id: int):
        query = select(Card).where(Card.account_id == account_id).where(Card.is_active == True)
        result = await db.execute(query)
        return result.all()

    @staticmethod
    async def create_card(db: AsyncSession, account_id: int):
        cards = await Card.get_active_cards_by_account_id(db, account_id)
        if cards:
            return None

        while True:
            new_number = generate_card_number()
            existing = await Card.get_card_by_number(db, new_number)
            if not existing:
                break

        new_card = Card(
            account_id=account_id,
            card_number=new_number,
            expiration_date=generate_expiration_date(),
            cvv=generate_cvv(),
            is_active=False
        )
        db.add(new_card)
        await db.commit()
        await db.refresh(new_card)
        return new_card


    async def activate(self, db: AsyncSession):
        if self and not self.is_active:
            self.is_active = True
            await db.commit()
            await db.refresh(self)
        return self


    async def deactivate(self, db: AsyncSession):
        if self and self.is_active:
            self.is_active = False
            await db.commit()
            await db.refresh(self)
        return self

    @staticmethod
    async def reissue_card(db: AsyncSession, card_id: int):
        old_card = await Card.get_card_by_id(db, card_id)
        if not old_card:
            return None

        old_card.is_active = False

        account_id = old_card.account_id

        while True:
            new_number = generate_card_number()
            existing = await Card.get_card_by_number(db, new_number)
            if not existing:
                break

        new_card = Card(
            account_id=account_id,
            card_number=new_number,
            expiration_date=generate_expiration_date(),
            cvv=generate_cvv(),
            is_active=True
        )

        db.add(new_card)
        await db.commit()
        await db.refresh(new_card)

        return new_card
