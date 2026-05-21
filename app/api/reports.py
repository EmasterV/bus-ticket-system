from fastapi import APIRouter, Depends
from app.database import db
from app.utils.auth import require_admin

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("/hourly-bookings")
async def hourly_bookings(admin: dict = Depends(require_admin)):
    async with db.connection.execute("""
        SELECT strftime('%Y-%m-%d %H:00', booked_at) as hour, COUNT(*) 
        FROM bookings 
        WHERE status = 'active'
        GROUP BY hour 
        ORDER BY hour DESC 
        LIMIT 24
    """) as cursor:
        rows = await cursor.fetchall()
    
    return [{"hour": row[0], "bookings": row[1]} for row in rows]

@router.get("/bus-monthly-revenue")
async def bus_monthly_revenue(admin: dict = Depends(require_admin)):
    async with db.connection.execute("""
        SELECT 
            b.bus_number,
            strftime('%Y-%m', bk.booked_at) as month,
            COUNT(bk.id) as total_bookings,
            SUM(bk.price) as total_revenue
        FROM bookings bk
        JOIN trips t ON bk.trip_id = t.id
        JOIN buses b ON t.bus_id = b.id
        WHERE bk.status = 'active'
        GROUP BY b.id, month
        ORDER BY month DESC, total_revenue DESC
        LIMIT 20
    """) as cursor:
        rows = await cursor.fetchall()
    
    return [
        {
            "bus_number": row[0],
            "month": row[1],
            "total_bookings": row[2],
            "total_revenue": row[3]
        }
        for row in rows
    ]

@router.get("/best-driver")
async def best_driver(admin: dict = Depends(require_admin)):
    async with db.connection.execute("""
        SELECT 
            b.driver_name,
            b.bus_number,
            COUNT(DISTINCT t.id) as total_trips,
            COUNT(bk.id) as total_bookings
        FROM buses b
        JOIN trips t ON b.id = t.bus_id
        LEFT JOIN bookings bk ON t.id = bk.trip_id AND bk.status = 'active'
        GROUP BY b.id
        ORDER BY total_trips DESC
        LIMIT 1
    """) as cursor:
        row = await cursor.fetchone()
    
    if row:
        return {
            "driver_name": row[0],
            "bus_number": row[1],
            "total_trips": row[2],
            "total_bookings": row[3]
        }
    return {"message": "No data found"}

@router.get("/route-popularity")
async def route_popularity(admin: dict = Depends(require_admin)):
    async with db.connection.execute("""
        SELECT 
            r.origin,
            r.destination,
            COUNT(bk.id) as total_bookings,
            SUM(bk.price) as total_revenue
        FROM routes r
        JOIN trips t ON r.id = t.route_id
        LEFT JOIN bookings bk ON t.id = bk.trip_id AND bk.status = 'active'
        GROUP BY r.id
        ORDER BY total_bookings DESC
        LIMIT 10
    """) as cursor:
        rows = await cursor.fetchall()
    
    return [
        {
            "origin": row[0],
            "destination": row[1],
            "total_bookings": row[2],
            "total_revenue": row[3]
        }
        for row in rows
    ]