import sqlite3
import csv
import json
import time

def create_or_update_database():
    conn = sqlite3.connect('restaurants.db')
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(menu_items)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'price_issue' not in columns:
        cursor.execute('ALTER TABLE menu_items ADD COLUMN price_issue BOOLEAN')
        cursor.execute('ALTER TABLE menu_items ADD COLUMN original_price TEXT')
        print("Updated menu_items table schema")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS restaurants (
        id INTEGER PRIMARY KEY,
        name TEXT,
        location TEXT,
        lat REAL,
        long REAL,
        cuisines TEXT,
        average_cost_for_two INTEGER,
        price_range INTEGER,
        user_rating_aggregate REAL,
        user_rating_votes INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS menu_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        restaurant_id INTEGER,
        item_name TEXT,
        price REAL,
        price_issue BOOLEAN,
        original_price TEXT,
        FOREIGN KEY (restaurant_id) REFERENCES restaurants (id)
    )
    ''')

    conn.commit()
    return conn, cursor

def process_restaurant(cursor, row):
    try:
        data = json.loads(row['full_details'])
    except json.JSONDecodeError:
        print(f"Error decoding JSON for restaurant ID {row['id']}.")
        print(f"Problematic JSON string: {row['full_details']}")
        data = {}
        
    name = row.get('name', f"Unknown Restaurant {row['id']}")
    
    try:
        lat, long = map(float, row['lat_long'].split(','))
    except (ValueError, KeyError):
        print(f"Error parsing lat_long for restaurant {name} (ID: {row['id']}). Using default values.")
        lat, long = 0.0, 0.0

    cursor.execute('''
    INSERT OR REPLACE INTO restaurants 
    (id, name, location, lat, long, cuisines, average_cost_for_two, price_range, user_rating_aggregate, user_rating_votes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        int(row['id']),
        name,
        row.get('location', 'Unknown'),
        lat,
        long,
        data.get('cuisines', ''),
        data.get('average_cost_for_two', 0),
        data.get('price_range', 0),
        float(data.get('user_rating', {}).get('aggregate_rating', 0)),
        int(data.get('user_rating', {}).get('votes', 0))
    ))

    try:
        items = json.loads(row['items'])
    except json.JSONDecodeError:
        print(f"Error decoding items JSON for restaurant {name} (ID: {row['id']}). Skipping menu items.")
        return

    menu_items = []
    for item, price in items.items():
        try:
            clean_price = ''.join(c for c in price if c.isdigit() or c == '.')
            price_float = float(clean_price)
            menu_items.append((int(row['id']), item, price_float, False, price))
        except ValueError:
            menu_items.append((int(row['id']), item, -1, True, price))
            print(f"Warning: Could not convert price '{price}' for item '{item}' in restaurant {name} (ID: {row['id']}) to float. Using default value and marking as issue.")

    cursor.executemany('''
    INSERT INTO menu_items (restaurant_id, item_name, price, price_issue, original_price)
    VALUES (?, ?, ?, ?, ?)
    ''', menu_items)

def process_csv(csv_file_path, batch_size=1000):
    conn, cursor = create_or_update_database()
    start_time = time.time()
    total_rows = 0
    processed_rows = 0

    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            batch = []

            for row in csv_reader:
                batch.append(row)
                total_rows += 1

                if len(batch) >= batch_size:
                    conn.execute('BEGIN TRANSACTION')
                    for item in batch:
                        process_restaurant(cursor, item)
                        processed_rows += 1
                    conn.commit()
                    print(f"Processed {processed_rows} rows...")
                    batch = []

            if batch:
                conn.execute('BEGIN TRANSACTION')
                for item in batch:
                    process_restaurant(cursor, item)
                    processed_rows += 1
                conn.commit()

        end_time = time.time()
        print(f"Total rows read: {total_rows}")
        print(f"Total rows processed: {processed_rows}")
        print(f"Total time taken: {end_time - start_time:.2f} seconds")

    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    csv_file_path = r'C:\Users\chait\OneDrive\Documents\sqlite3\restaurants_small.csv'
    process_csv(csv_file_path)

    conn = sqlite3.connect('restaurants.db')
    cursor = conn.cursor()

    print("\nRestaurant count:")
    cursor.execute("SELECT COUNT(*) FROM restaurants")
    print(cursor.fetchone()[0])

    print("\nSample restaurants (first 5):")
    cursor.execute("SELECT id, name, location FROM restaurants LIMIT 5")
    for row in cursor.fetchall():
        print(row)

    print("\nTotal menu items:")
    cursor.execute("SELECT COUNT(*) FROM menu_items")
    print(cursor.fetchone()[0])

    print("\nAverage price of menu items per restaurant (first 5):")
    cursor.execute("""
        SELECT r.name, AVG(m.price) as avg_price
        FROM restaurants r
        JOIN menu_items m ON r.id = m.restaurant_id
        WHERE m.price_issue = 0
        GROUP BY r.id
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(row)

    print("\nMenu items with price issues (first 5):")
    cursor.execute("""
        SELECT r.name, m.item_name, m.original_price
        FROM restaurants r
        JOIN menu_items m ON r.id = m.restaurant_id
        WHERE m.price_issue = 1
        LIMIT 5
    """)
    for row in cursor.fetchall():
        print(row)

    conn.close()

if __name__ == "__main__":
    main()