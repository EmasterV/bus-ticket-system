from app.database import db
from datetime import datetime, timedelta
import random

async def seed_initial_data():
    if db.connection is None:
        await db.connect()
    
    print("Checking existing data...")
    
    route_count = await db.connection.execute("SELECT COUNT(*) FROM routes")
    result = await route_count.fetchone()
    route_count = result[0]
    
    if route_count == 0:
        print("Seeding routes...")
        routes = [
            ("Tehran", "Mashhad", 350000, 900),
            ("Tehran", "Isfahan", 250000, 450),
            ("Tehran", "Shiraz", 400000, 950),
            ("Tehran", "Tabriz", 320000, 650),
            ("Tehran", "Ahvaz", 380000, 800),
            ("Mashhad", "Tehran", 350000, 900),
            ("Mashhad", "Isfahan", 300000, 750),
            ("Isfahan", "Shiraz", 280000, 500),
            ("Isfahan", "Tehran", 250000, 450),
            ("Shiraz", "Tehran", 400000, 950),
            ("Tabriz", "Tehran", 320000, 650),
            ("Ahvaz", "Tehran", 380000, 800),
            ("Qom", "Mashhad", 280000, 700),
            ("Karaj", "Mashhad", 330000, 850),
            ("Kermanshah", "Tehran", 350000, 550),
        ]
        for route in routes:
            await db.connection.execute(
                "INSERT INTO routes (origin, destination, base_price, distance_km) VALUES (?, ?, ?, ?)",
                route
            )
        await db.connection.commit()
        print(f"  {len(routes)} routes created")
    
    bus_count = await db.connection.execute("SELECT COUNT(*) FROM buses")
    result = await bus_count.fetchone()
    bus_count = result[0]
    
    if bus_count == 0:
        print("Seeding buses...")
        drivers = [
            "Ali Mohammadi", "Reza Karimi", "Saeed Ahmadi", "Mahdi Hosseini", 
            "Hossein Rezaei", "Mohammad Jafari", "Hamid Nazari", "Karim Ahmadi",
            "Majid Hashemi", "Reza Mohammadi", "Sasan Karimi", "Behrouz Ahmadi"
        ]
        models = ["Volvo", "Scania", "Mercedes", "MAN", "Iveco", "David Brown"]
        
        for i in range(30):
            bus_number = f"IR-{random.randint(100, 999)}-{random.randint(10, 99)}"
            driver = random.choice(drivers)
            capacity = random.choice([30, 40, 44, 50])
            route_id = random.randint(1, max(1, route_count))
            model = random.choice(models)
            
            await db.connection.execute(
                "INSERT INTO buses (bus_number, driver_name, capacity, route_id, model) VALUES (?, ?, ?, ?, ?)",
                (bus_number, driver, capacity, route_id, model)
            )
        await db.connection.commit()
        print("  30 buses created")
    
    trip_count = await db.connection.execute("SELECT COUNT(*) FROM trips")
    result = await trip_count.fetchone()
    trip_count = result[0]
    
    if trip_count < 50:
        print("Seeding trips...")
        rows = await db.connection.execute("SELECT id, capacity, route_id FROM buses")
        buses = await rows.fetchall()
        
        price_rows = await db.connection.execute("SELECT id, base_price FROM routes")
        routes_data_rows = await price_rows.fetchall()
        routes_data = {row[0]: row[1] for row in routes_data_rows}
        
        created_count = 0
        for bus in buses:
            bus_id = bus[0]
            capacity = bus[1]
            route_id = bus[2]
            base_price = routes_data.get(route_id, 300000)
            
            for day_offset in range(1, 8):
                departure = datetime.now() + timedelta(days=day_offset)
                departure = departure.replace(hour=random.choice([6, 8, 10, 12, 14, 16, 18, 20]), minute=0, second=0, microsecond=0)
                arrival = departure + timedelta(hours=random.randint(5, 12))
                price = base_price + random.randint(-50000, 50000)
                
                await db.connection.execute("""
                    INSERT INTO trips (bus_id, route_id, departure_time, arrival_time, price, available_seats) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (bus_id, route_id, departure, arrival, price, capacity))
                
                result = await db.connection.execute("SELECT last_insert_rowid()")
                row = await result.fetchone()
                trip_id = row[0]
                
                for seat_num in range(1, capacity + 1):
                    await db.connection.execute(
                        "INSERT INTO seats (trip_id, seat_number, is_booked) VALUES (?, ?, 0)",
                        (trip_id, seat_num)
                    )
                created_count += 1
        
        await db.connection.commit()
        print(f"  {created_count} trips created with seats")
    
    user_count = await db.connection.execute("SELECT COUNT(*) FROM users")
    result = await user_count.fetchone()
    user_count = result[0]
    
    if user_count < 10:
        print("Seeding users...")
        for i in range(10, 110):
            phone = f"09{random.randint(100000000, 999999999)}"
            token = f"user_token_{i}"
            balance = random.randint(100000, 5000000)
            role = random.choice(['passenger', 'operator'])
            await db.connection.execute(
                "INSERT INTO users (phone_number, token, wallet_balance, role) VALUES (?, ?, ?, ?)",
                (phone, token, balance, role)
            )
        await db.connection.commit()
        print("  100 additional users created")
        print("Ensuring main tokens exist...")
        await db.connection.execute("""
            INSERT OR REPLACE INTO users (id, phone_number, token, wallet_balance, role) 
            VALUES (1, '09123456789', 'user_token_123', 5000000, 'passenger')
        """)
        await db.connection.execute("""
            INSERT OR REPLACE INTO users (id, phone_number, token, wallet_balance, role) 
            VALUES (2, '09123456788', 'operator_token_123', 5000000, 'operator')
        """)
        await db.connection.execute("""
            INSERT OR REPLACE INTO users (id, phone_number, token, wallet_balance, role) 
            VALUES (3, '09123456787', 'admin_token_123', 5000000, 'admin')
        """)
        await db.connection.commit()
        print("  Main tokens added: user_token_123, operator_token_123, admin_token_123")
    
    print("Seeding complete!")