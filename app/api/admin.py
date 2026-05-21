from fastapi import APIRouter, HTTPException, Depends
from app.database import db
from app.models import BusCreate, TripCreate, RouteCreate
from app.utils.auth import require_admin, require_operator_or_admin

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.post("/routes")
async def create_route(route: RouteCreate, admin: dict = Depends(require_admin)):
    try:
        await db.connection.execute(
            "INSERT INTO routes (origin, destination, base_price, distance_km) VALUES (?, ?, ?, ?)",
            (route.origin, route.destination, route.base_price, route.distance_km)
        )
        await db.connection.commit()
        return {"success": True, "message": "Route created successfully"}
    except:
        raise HTTPException(status_code=400, detail="Route already exists")

@router.get("/routes")
async def get_routes(admin: dict = Depends(require_admin)):
    async with db.connection.execute("SELECT id, origin, destination, base_price, distance_km FROM routes") as cursor:
        rows = await cursor.fetchall()
    
    return {
        "routes": [
            {"id": row[0], "origin": row[1], "destination": row[2], "base_price": row[3], "distance_km": row[4]}
            for row in rows
        ]
    }

@router.post("/buses")
async def create_bus(bus: BusCreate, admin: dict = Depends(require_operator_or_admin)):
    async with db.connection.execute("SELECT id FROM routes WHERE id = ?", (bus.route_id,)) as cursor:
        route = await cursor.fetchone()
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")
    
    try:
        await db.connection.execute(
            "INSERT INTO buses (bus_number, driver_name, capacity, route_id, model) VALUES (?, ?, ?, ?, ?)",
            (bus.bus_number, bus.driver_name, bus.capacity, bus.route_id, bus.model)
        )
        await db.connection.commit()
        return {"success": True, "message": "Bus created successfully"}
    except:
        raise HTTPException(status_code=400, detail="Bus number already exists")

@router.post("/trips")
async def create_trip(trip: TripCreate, admin: dict = Depends(require_operator_or_admin)):
    async with db.connection.execute("SELECT capacity FROM buses WHERE id = ?", (trip.bus_id,)) as cursor:
        bus = await cursor.fetchone()
        if not bus:
            raise HTTPException(status_code=404, detail="Bus not found")
    
    async with db.connection.execute("SELECT id FROM routes WHERE id = ?", (trip.route_id,)) as cursor:
        route = await cursor.fetchone()
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")
    
    capacity = bus[0]
    
    await db.connection.execute(
        "INSERT INTO trips (bus_id, route_id, departure_time, arrival_time, price, available_seats) VALUES (?, ?, ?, ?, ?, ?)",
        (trip.bus_id, trip.route_id, trip.departure_time, trip.arrival_time, trip.price, capacity)
    )
    
    result = await db.connection.execute("SELECT last_insert_rowid()")
    trip_id_row = await result.fetchone()
    trip_id = trip_id_row[0]
    
    for seat_num in range(1, capacity + 1):
        await db.connection.execute(
            "INSERT INTO seats (trip_id, seat_number, is_booked) VALUES (?, ?, 0)",
            (trip_id, seat_num)
        )
    
    await db.connection.commit()
    
    return {"success": True, "trip_id": trip_id}

@router.post("/reset-user/{user_id}")
async def reset_user_bookings(user_id: int, admin: dict = Depends(require_admin)):
    async with db.connection.execute("SELECT id FROM users WHERE id = ?", (user_id,)) as cursor:
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    
    await db.connection.execute("DELETE FROM bookings WHERE user_id = ?", (user_id,))
    
    await db.connection.execute("UPDATE users SET wallet_balance = 5000000 WHERE id = ?", (user_id,))
    
    await db.connection.commit()
    
    async with db.connection.execute("SELECT wallet_balance FROM users WHERE id = ?", (user_id,)) as cursor:
        user_data = await cursor.fetchone()
    
    return {
        "success": True,
        "user_id": user_id,
        "new_balance": user_data[0],
        "message": f"User {user_id} has been reset. All bookings deleted, balance set to 5,000,000"
    }

@router.get("/buses")
async def get_buses(admin: dict = Depends(require_admin)):
    async with db.connection.execute("SELECT id, bus_number, driver_name, capacity, route_id, model FROM buses") as cursor:
        rows = await cursor.fetchall()
    
    return {
        "buses": [
            {"id": row[0], "bus_number": row[1], "driver_name": row[2], "capacity": row[3], "route_id": row[4], "model": row[5]}
            for row in rows
        ]
    }