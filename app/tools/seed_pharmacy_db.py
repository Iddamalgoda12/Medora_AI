import sqlite3
import os

DB_PATH = "pharmacy_mock.db"

def setup_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create Tables
    cursor.execute('''
        CREATE TABLE pharmacies (
            id INTEGER PRIMARY KEY,
            name TEXT,
            address TEXT,
            lat REAL,
            lng REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE inventory (
            id INTEGER PRIMARY KEY,
            pharmacy_id INTEGER,
            drug_name TEXT,
            stock_level INTEGER,
            price REAL,
            FOREIGN KEY(pharmacy_id) REFERENCES pharmacies(id)
        )
    ''')

    # Expanded list of pharmacies across diverse regions for rigorous location testing
    # Pre-calculated real lat/long coordinates matching the text addresses
    pharmacies = [
        (1, "Healthguard Pharmacy", "Dharmapala Mawatha, Colombo 07", 6.9147, 79.8576),
        (2, "Rajya Osu Sala", "C. W. W. Kannangara Mawatha, Town Hall, Colombo 07", 6.9155, 79.8636),
        (3, "Union Chemists", "Galle Road, Bambalapitiya, Colombo 04", 6.8850, 79.8550),
        (4, "Suburban Pharmacy", "High Level Road, Nugegoda", 6.8700, 79.8900),
        (5, "Rajya Osu Sala", "De Saram Place, Maradana, Colombo 10", 6.9240, 79.8655),
        (6, "Healthguard Pharmacy", "Galle Road, Kollupitiya, Colombo 03", 6.9092, 79.8498),
        (7, "Suhada Pharmacy", "Kandy Road, Kadawatha", 7.0012, 79.9540),
        (8, "City Pharma", "Main Street, Pettah, Colombo 11", 6.9366, 79.8502),
        # New Mock Locations added below:
        (9, "Healthguard Pharmacy", "Sri Jayawardenepura Kotte Road, Welikada, Rajagiriya", 6.9085, 79.8974),
        (10, "Lanka Chemists", "Galle Road, Dehiwala", 6.8386, 79.8642),
        (11, "Central Pharma", "Peradeniya Road, Kandy", 7.2906, 80.6337),
        (12, "Negombo Medi-Station", "Main Street, Negombo", 7.2091, 79.8354)
    ]
    cursor.executemany("INSERT INTO pharmacies VALUES (?, ?, ?, ?, ?)", pharmacies)

    # Master inventory dataset matching the new locations
    inventory_data = [
        # --- Diabetes Management (Metformin) ---
        (1, "Metformin 500mg", 450, 5.00), (2, "Metformin 500mg", 0, 4.20), (3, "Metformin 500mg", 800, 5.50), 
        (5, "Metformin 500mg", 1200, 4.20), (9, "Metformin 500mg", 300, 5.10), (10, "Metformin 500mg", 600, 4.90),
        (11, "Metformin 500mg", 400, 4.50),

        # --- Analgesics & Pain Relief (Panadol) ---
        (1, "Panadol 500mg", 5000, 4.00), (2, "Panadol 500mg", 10000, 4.00), (3, "Panadol 500mg", 3000, 4.00), 
        (4, "Panadol 500mg", 4500, 4.00), (5, "Panadol 500mg", 8000, 4.00), (6, "Panadol 500mg", 2500, 4.00), 
        (7, "Panadol 500mg", 1200, 4.00), (8, "Panadol 500mg", 15000, 4.00), (9, "Panadol 500mg", 3500, 4.00),
        (10, "Panadol 500mg", 6000, 4.00), (11, "Panadol 500mg", 7000, 4.00), (12, "Panadol 500mg", 5000, 4.00),

        # --- Antibiotics (Amoxicillin) ---
        (1, "Amoxicillin 250mg", 0, 15.00), (2, "Amoxicillin 250mg", 600, 12.00), (4, "Amoxicillin 250mg", 400, 14.50), 
        (5, "Amoxicillin 250mg", 800, 12.00), (10, "Amoxicillin 250mg", 200, 13.80), (12, "Amoxicillin 250mg", 500, 14.00),
        (9, "Amoxicillin 500mg", 150, 29.00), (11, "Amoxicillin 500mg", 350, 27.50)
    ]
    
    cursor.executemany(
        "INSERT INTO inventory (pharmacy_id, drug_name, stock_level, price) VALUES (?, ?, ?, ?)", 
        inventory_data
    )

    conn.commit()
    conn.close()
    print(f"✅ Database re-seeded! {len(pharmacies)} pharmacies are now live across multiple provinces.")

if __name__ == "__main__":
    setup_database()
