from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.config import get_current_user
from fastapi import HTTPException
from app.models import Account, Card
from pydantic import BaseModel
app = FastAPI(title="Accounts API")

@app.get("/")
async def root():
    return {"message": "Сервер працює! 🚀"}

# Перевіряємо, чи жива база
@app.get("/db-ping")
async def ping_db(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    return {"status": "База даних підключена успішно!", "result": result.scalar()}

@app.get("/my-accounts")
async def get_my_accounts(db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    accounts = await Account.get_accounts_by_username(db, current_user)
    res = [x.get_iban() for x in accounts]
    return {
        "message": "Ти успішно пройшов авторизацію!",
        "user": current_user,
        "accounts": res
    }

@app.post("/create_account")
async def create_account(db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    account = await Account.create_account(db, current_user)
    print(account)
    return {
        "message": "Account created!",
        "user": current_user,
        "account": account.get_iban()
    }


class CardInfo(BaseModel):
    iban: str

@app.post("/create_card")
async def create_card(card_data: CardInfo, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    account = await Account.get_account_by_iban(db, card_data.iban)
    if not account:
        raise HTTPException(status_code=404, detail="Account with this IBAN not found.")

    if account.username != current_user:
        raise HTTPException(status_code=403, detail="You cannot create a card for someone else's account.")

    new_card = await Card.create_card(db, account.id)
    if not new_card:
        return {
            "message": "You already have an active card."
        }

    await new_card.activate(db)

    return {
        "message": "The card has been successfully created!",
        "iban": card_data.iban,
        "card_number": new_card.card_number,
        "expiration_date": new_card.expiration_date,
        "cvv": new_card.cvv,
        "is_active": new_card.is_active
    }



async def get_and_validate_card(card_id: int, current_user: str, db: AsyncSession):
    card = await Card.get_card_by_id(db, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    account = await db.get(Account, card.account_id)
    if not account or account.username != current_user:
        raise HTTPException(status_code=403, detail="Access denied: This card does not belong to you")

    return card, account


@app.post("/activate_card/{card_id}")
async def activate_card(card_id: int, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    card, account = await get_and_validate_card(card_id, current_user, db)

    if await account.get_active_cards_by_account(db):
        raise HTTPException(status_code=403, detail="Access denied: You already have an active card for this account.")

    await card.activate(db)
    return {"message": f"Card {card.card_number} successfully activated!"}

@app.post("/deactivate_card/{card_id}")
async def deactivate_card(card_id: int, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    card, account = await get_and_validate_card(card_id, current_user, db)

    await card.deactivate(db)
    return {"message": f"Card {card.card_number} successfully deactivated!"}

@app.post("/reissue_card/{card_id}")
async def reissue_card(card_id: int, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    card, account = await get_and_validate_card(card_id, current_user, db)

    await Card.reissue_card(db, card_id)
    return {"message": f"Card {card.card_number} successfully reissue!"}