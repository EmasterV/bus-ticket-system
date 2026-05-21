from app.database import db

async def init_database():
    if db.connection is None:
        await db.connect()
    
    print("Checking and initializing data...")
    
    route_count = await db.connection.execute("SELECT COUNT(*) FROM routes")
    route_count = (await route_count.fetchone())[0]
    
    if route_count == 0:
        print("Creating routes...")
        routes = [
            ("Tehran", "Mashhad", 350000, 900),
            ("Tehran", "Isfahan", 250000, 450),
            ("Tehran", "Shiraz", 400000, 950),
            ("Mashhad", "Tehran", 350000, 900),
            ("Isfahan", "Shiraz", 280000, 500),
            ("Tabriz", "Tehran", 320000, 650),
            ("Ahvaz", "Tehran", 380000, 800),
        ]
        for route in routes:
            await db.connection.execute(
                "INSERT OR IGNORE INTO routes (origin, destination, base_price, distance_km) VALUES (?, ?, ?, ?)",
                route
            )
    
    bus_count = await db.connection.execute("SELECT COUNT(*) FROM buses")
    bus_count = (await bus_count.fetchone())[0]
    
    if bus_count == 0:
        print("Creating buses...")
        buses = [
            ("IR-999-99", "John Doe", 40, 1, "Volvo"),
            ("IR-888-77", "Ali Rezaei", 50, 2, "Scania"),
            ("IR-777-66", "Saeed Ahmadi", 44, 1, "Mercedes"),
            ("IR-666-55", "Hossein Rezaei", 40, 3, "MAN"),
        ]
        for bus in buses:
            await db.connection.execute(
                "INSERT INTO buses (bus_number, driver_name, capacity, route_id, model) VALUES (?, ?, ?, ?, ?)",
                bus
            )
    
    trip_count = await db.connection.execute("SELECT COUNT(*) FROM trips")
    trip_count = (await trip_count.fetchone())[0]
    
    if trip_count < 5:
        print("Creating trips...")
        from datetime import datetime, timedelta
        
        async with db.connection.execute("SELECT id, capacity FROM buses LIMIT 1") as cursor:
            bus = await cursor.fetchone()
            bus_id = bus[0]
            capacity = bus[1]
        
        async with db.connection.execute("SELECT id FROM routes LIMIT 1") as cursor:
            route = await cursor.fetchone()
            route_id = route[0]
        
        for i in range(5):
            departure = datetime.now() + timedelta(days=i+1)
            departure = departure.replace(hour=10, minute=0, second=0, microsecond=0)
            arrival = departure + timedelta(hours=8)
            
            await db.connection.execute("""
                INSERT INTO trips (bus_id, route_id, departure_time, arrival_time, price, available_seats) 
                VALUES (?, ?, ?, ?, 350000, ?)
            """, (bus_id, route_id, departure, arrival, capacity))
            
            trip_id = (await db.connection.execute("SELECT last_insert_rowid()")).fetchone()[0]
            
            for seat_num in range(1, capacity + 1):
                await db.connection.execute(
                    "INSERT INTO seats (trip_id, seat_number, is_booked) VALUES (?, ?, 0)",
                    (trip_id, seat_num)
                )
    
    await db.connection.commit()
    print("Database initialization complete!")