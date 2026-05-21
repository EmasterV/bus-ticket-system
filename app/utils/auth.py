from fastapi import HTTPException, Header, Depends
from app.database import db

async def get_current_user(token: str = Header(...)):
    async with db.connection.execute(
        "SELECT id, role, phone_number FROM users WHERE token = ?", (token,)
    ) as cursor:
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"id": user[0], "role": user[1], "phone_number": user[2]}

async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

async def require_operator_or_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["operator", "admin"]:
        raise HTTPException(status_code=403, detail="Operator or admin access required")
    return current_user

async def require_passenger(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "passenger":
        raise HTTPException(status_code=403, detail="Passenger access required")
    return current_user