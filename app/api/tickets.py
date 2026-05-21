from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import random
import string
from app.database import db
from app.models import BookingRequest, CancelRequest
from app.utils.auth import get_current_user
from app.utils.security import hash_token, generate_token

hashed_user_token = hash_token("user_token_123")
hashed_admin_token = hash_token("admin_token_123")
hashed_operator_token = hash_token("operator_token_123")

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])

async def generate_booking_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

async def check_daily_limit(user_id: int):
    async with db.connection.execute(
        "SELECT COUNT(*) FROM bookings WHERE user_id = ? AND date(booked_at) = date('now') AND status = 'active'",
        (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        count = row[0] if row else 0
        return count < 20

@router.post("/book")
async def book_ticket(request: BookingRequest, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != request.user_id:
        raise HTTPException(status_code=403, detail="You can only book tickets for yourself")
    
    async with db.connection.execute(
        "SELECT id, available_seats, price FROM trips WHERE id = ?",
        (request.trip_id,)
    ) as cursor:
        trip = await cursor.fetchone()
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip[1] <= 0:
        raise HTTPException(status_code=400, detail="No available seats")
    
    async with db.connection.execute(
        "SELECT id, is_booked FROM seats WHERE trip_id = ? AND seat_number = ?",
        (request.trip_id, request.seat_number)
    ) as cursor:
        seat = await cursor.fetchone()
        if not seat:
            raise HTTPException(status_code=404, detail="Seat not found")
        if seat[1] == 1:
            raise HTTPException(status_code=400, detail="Seat already booked")
    
    if not await check_daily_limit(request.user_id):
        raise HTTPException(status_code=400, detail="Daily booking limit exceeded (20 max)")
    
    async with db.connection.execute(
        "SELECT wallet_balance FROM users WHERE id = ?",
        (request.user_id,)
    ) as cursor:
        user = await cursor.fetchone()
        if user[0] < trip[2]:
            raise HTTPException(status_code=400, detail="Insufficient balance")
    
    booking_code = await generate_booking_code()
    
    await db.connection.execute(
        "UPDATE users SET wallet_balance = wallet_balance - ? WHERE id = ?",
        (trip[2], request.user_id)
    )
    
    await db.connection.execute(
        "UPDATE seats SET is_booked = 1, booked_by = ?, booked_at = ? WHERE trip_id = ? AND seat_number = ?",
        (request.user_id, datetime.now(), request.trip_id, request.seat_number)
    )
    
    await db.connection.execute(
        "UPDATE trips SET available_seats = available_seats - 1 WHERE id = ?",
        (request.trip_id,)
    )
    
    await db.connection.execute(
        "INSERT INTO bookings (user_id, trip_id, seat_id, booking_code, price) VALUES (?, ?, ?, ?, ?)",
        (request.user_id, request.trip_id, seat[0], booking_code, trip[2])
    )
    
    await db.connection.execute(
        "INSERT INTO wallet_transactions (user_id, booking_id, amount, transaction_type) VALUES (?, (SELECT last_insert_rowid()), ?, 'payment')",
        (request.user_id, -trip[2])
    )
    
    await db.connection.commit()
    
    return {
        "success": True,
        "booking_code": booking_code,
        "price": trip[2],
        "seat_number": request.seat_number
    }

@router.post("/cancel")
async def cancel_booking(request: CancelRequest, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != request.user_id:
        raise HTTPException(status_code=403, detail="You can only cancel your own tickets")
    
    async with db.connection.execute(
        "SELECT id, user_id, price, status, seat_id, trip_id FROM bookings WHERE booking_code = ?",
        (request.booking_code,)
    ) as cursor:
        booking = await cursor.fetchone()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking[1] != request.user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        if booking[3] == 'cancelled':
            raise HTTPException(status_code=400, detail="Booking already cancelled")
    
    await db.connection.execute(
        "UPDATE bookings SET status = 'cancelled', cancelled_at = ? WHERE booking_code = ?",
        (datetime.now(), request.booking_code)
    )
    
    await db.connection.execute(
        "UPDATE users SET wallet_balance = wallet_balance + ? WHERE id = ?",
        (booking[2], request.user_id)
    )
    
    await db.connection.execute(
        "UPDATE seats SET is_booked = 0, booked_by = NULL, booked_at = NULL WHERE id = ?",
        (booking[4],)
    )
    
    await db.connection.execute(
        "UPDATE trips SET available_seats = available_seats + 1 WHERE id = ?",
        (booking[5],)
    )
    
    await db.connection.execute(
        "INSERT INTO wallet_transactions (user_id, booking_id, amount, transaction_type) VALUES (?, ?, ?, 'refund')",
        (request.user_id, booking[0], booking[2])
    )
    
    await db.connection.commit()
    
    return {"success": True, "refund_amount": booking[2]}

@router.get("/")
async def get_tickets(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    sort: str = None,
    origin: str = None,
    destination: str = None,
    skip: int = 0,
    limit: int = 50
):
    if current_user["id"] != user_id and current_user["role"] not in ["operator", "admin"]:
        raise HTTPException(status_code=403, detail="You can only view your own tickets")
    
    query = """
        SELECT 
            b.booking_code, 
            b.trip_id, 
            b.price, 
            b.status, 
            b.booked_at, 
            s.seat_number,
            r.origin, 
            r.destination, 
            t.departure_time, 
            t.arrival_time
        FROM bookings b
        JOIN seats s ON b.seat_id = s.id
        JOIN trips t ON b.trip_id = t.id
        JOIN routes r ON t.route_id = r.id
        WHERE b.user_id = ? AND b.status = 'active'
    """
    params = [user_id]
    
    if origin:
        query += " AND r.origin = ?"
        params.append(origin)
    if destination:
        query += " AND r.destination = ?"
        params.append(destination)
    
    if sort == 'price_asc':
        query += " ORDER BY b.price ASC"
    elif sort == 'price_desc':
        query += " ORDER BY b.price DESC"
    else:
        query += " ORDER BY b.booked_at DESC"
    
    query += " LIMIT ? OFFSET ?"
    params.append(limit)
    params.append(skip)
    
    async with db.connection.execute(query, params) as cursor:
        rows = await cursor.fetchall()
    
    tickets = []
    for row in rows:
        tickets.append({
            "booking_code": row[0],
            "trip_id": row[1],
            "price": row[2],
            "status": row[3],
            "booked_at": row[4],
            "seat_number": row[5],
            "origin": row[6],
            "destination": row[7],
            "departure_time": row[8],
            "arrival_time": row[9]
        })
    
    return {"tickets": tickets, "count": len(tickets)}

@router.post("/create-user")
async def create_user():
    try:
        if db.connection is None:
            await db.connect()
        
        await db.connection.execute(
            "INSERT OR REPLACE INTO users (id, phone_number, token, wallet_balance, role) VALUES (1, '09123456789', 'user_token_123', 5000000, 'passenger')"
        )
        await db.connection.execute(
            "INSERT OR REPLACE INTO users (id, phone_number, token, wallet_balance, role) VALUES (2, '09123456788', 'operator_token_123', 5000000, 'operator')"
        )
        await db.connection.execute(
            "INSERT OR REPLACE INTO users (id, phone_number, token, wallet_balance, role) VALUES (3, '09123456787', 'admin_token_123', 5000000, 'admin')"
        )
        await db.connection.commit()
        return {
            "success": True, 
            "message": "Test users created. Passenger token: user_token_123, Operator token: operator_token_123, Admin token: admin_token_123"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-seats/{trip_id}")
async def get_available_seats(trip_id: int, current_user: dict = Depends(get_current_user)):
    async with db.connection.execute(
        "SELECT seat_number FROM seats WHERE trip_id = ? AND is_booked = 0 ORDER BY seat_number",
        (trip_id,)
    ) as cursor:
        rows = await cursor.fetchall()
    
    available_seats = [row[0] for row in rows]
    
    async with db.connection.execute(
        "SELECT available_seats FROM trips WHERE id = ?", (trip_id,)
    ) as cursor:
        trip = await cursor.fetchone()
        total_available = trip[0] if trip else 0
    
    return {
        "trip_id": trip_id,
        "total_available": total_available,
        "available_seats": available_seats[:20]
    }

@router.get("/available-seats/{trip_id}")
async def get_available_seats(trip_id: int, current_user: dict = Depends(get_current_user)):
    async with db.connection.execute(
        "SELECT id, origin, destination FROM routes WHERE id = (SELECT route_id FROM trips WHERE id = ?)",
        (trip_id,)
    ) as cursor:
        route = await cursor.fetchone()
        if not route:
            raise HTTPException(status_code=404, detail="Trip not found")
    
    async with db.connection.execute(
        "SELECT seat_number FROM seats WHERE trip_id = ? AND is_booked = 0 ORDER BY seat_number",
        (trip_id,)
    ) as cursor:
        rows = await cursor.fetchall()
    
    available_seats = [row[0] for row in rows]
    
    async with db.connection.execute(
        "SELECT available_seats, price FROM trips WHERE id = ?", (trip_id,)
    ) as cursor:
        trip = await cursor.fetchone()
        total_available = trip[0] if trip else 0
        price = trip[1] if trip else 0
    
    return {
        "trip_id": trip_id,
        "origin": route[1],
        "destination": route[2],
        "price": price,
        "total_available": total_available,
        "available_seats": available_seats[:20]
    }

@router.get("/test-bookings")
async def test_bookings(current_user: dict = Depends(get_current_user)):
    async with db.connection.execute("SELECT booking_code, user_id, trip_id, price, status FROM bookings") as cursor:
        rows = await cursor.fetchall()
    
    return {"bookings": [{"code": r[0], "user_id": r[1], "trip_id": r[2], "price": r[3], "status": r[4]} for r in rows]}