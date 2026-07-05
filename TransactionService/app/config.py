from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "твій_дуже_складний_секретний_ключ_123")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Недійсний токен або термін його дії минув",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")  # "sub" (subject) - це зазвичай ID юзера
        print(payload)
        if username is None:
            raise credentials_exception

        return username  # Повертаємо ID юзера, щоб використати в ендпоінті

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="The token has expired.")
    except jwt.PyJWTError:
        raise credentials_exception