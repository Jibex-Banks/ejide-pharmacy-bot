import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

class Database:
    def __init__(self, db_path: str = "database/pharmacy.db"):
        self.db_path = db_path
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def initialize(self):
        """Create all necessary tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Inventory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_name TEXT UNIQUE NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                category TEXT,
                description TEXT,
                dosage_days INTEGER DEFAULT 0,
                dosage_frequency TEXT DEFAULT 'as prescribed',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT NOT NULL,
                message TEXT NOT NULL,
                is_admin BOOLEAN,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Enhanced purchases table with medication tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT NOT NULL,
                drug_name TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                amount REAL DEFAULT 0,
                dosage_days INTEGER DEFAULT 0,
                dosage_frequency TEXT,
                treatment_end_date DATE,
                last_reminder_sent DATE,
                reminders_sent INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Shopping cart table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT NOT NULL,
                drug_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(phone_number, drug_name)
            )
        """)
        
        # Analytics table for predictive insights
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value TEXT NOT NULL,
                calculated_date DATE DEFAULT CURRENT_DATE
            )
        """)
        
        # Seed initial inventory with dosage information
        cursor.execute("SELECT COUNT(*) as count FROM inventory")
        if cursor.fetchone()['count'] == 0:
            initial_drugs = [
                ("paracetamol", 150, 500, "fever/pain", "For fever and pain relief", 3, "3 times daily"),
                ("amoxicillin", 80, 1200, "antibiotic", "Bacterial infection treatment", 7, "2 times daily"),
                ("chloroquine", 60, 800, "malaria", "Malaria treatment", 3, "Once daily"),
                ("artemether", 45, 1800, "malaria", "Severe malaria treatment", 3, "Twice daily"),
                ("coartem", 70, 2000, "malaria", "Combination antimalarial", 3, "Twice daily"),
                ("vitamin c", 200, 300, "supplement", "Immune system booster", 30, "Once daily"),
                ("ibuprofen", 120, 600, "pain", "Anti-inflammatory", 5, "3 times daily"),
                ("cough syrup", 45, 1500, "cold/flu", "Cough relief", 5, "3 times daily"),
            ]
            
            cursor.executemany("""
                INSERT INTO inventory (drug_name, quantity, price, category, description, dosage_days, dosage_frequency)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, initial_drugs)
        
        conn.commit()
        conn.close()
    
    def log_conversation(self, phone_number: str, message: str, is_admin: bool):
        """Log conversations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO conversations (phone_number, message, is_admin)
            VALUES (?, ?, ?)
        """, (phone_number, message, is_admin))
        conn.commit()
        conn.close()
    
    def get_customer_history(self, phone_number: str) -> Dict:
        """Get customer history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT message, timestamp
            FROM conversations
            WHERE phone_number = ?
            ORDER BY timestamp DESC
            LIMIT 10
        """, (phone_number,))
        
        conversations = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT drug_name, quantity, amount, purchase_date, dosage_days, completed
            FROM purchases
            WHERE phone_number = ?
            ORDER BY purchase_date DESC
            LIMIT 5
        """, (phone_number,))
        
        purchases = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "conversations": conversations,
            "purchases": purchases
        }
    
    def get_inventory(self) -> List[Dict]:
        """Get all inventory"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT drug_name, quantity, price, category, description, dosage_days, dosage_frequency
            FROM inventory
            ORDER BY drug_name
        """)
        inventory = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return inventory
    
    def update_inventory(self, drug_name: str, quantity: int, price: float, 
                        category: str, description: str = "", dosage_days: int = 0, 
                        dosage_frequency: str = "as prescribed"):
        """Add or update inventory"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO inventory (drug_name, quantity, price, category, description, dosage_days, dosage_frequency)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(drug_name) DO UPDATE SET
                quantity = excluded.quantity,
                price = excluded.price,
                category = excluded.category,
                description = excluded.description,
                dosage_days = excluded.dosage_days,
                dosage_frequency = excluded.dosage_frequency,
                last_updated = CURRENT_TIMESTAMP
        """, (drug_name.lower(), quantity, price, category, description, dosage_days, dosage_frequency))
        conn.commit()
        conn.close()
    
    def get_cart(self, phone_number: str) -> List[Dict]:
        """Get customer's shopping cart"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.drug_name, c.quantity, i.price, i.category, i.dosage_days, i.dosage_frequency
            FROM cart c
            JOIN inventory i ON c.drug_name = i.drug_name
            WHERE c.phone_number = ?
            ORDER BY c.added_date
        """, (phone_number,))
        cart = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return cart
    
    def add_to_cart(self, phone_number: str, drug_name: str, quantity: int):
        """Add item to cart"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT quantity FROM inventory WHERE drug_name = ?
        """, (drug_name.lower(),))
        
        result = cursor.fetchone()
        if not result or result['quantity'] < quantity:
            conn.close()
            return False
        
        cursor.execute("""
            INSERT INTO cart (phone_number, drug_name, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(phone_number, drug_name) DO UPDATE SET
                quantity = quantity + excluded.quantity
        """, (phone_number, drug_name.lower(), quantity))
        
        conn.commit()
        conn.close()
        return True
    
    def clear_cart(self, phone_number: str):
        """Clear customer's cart"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM cart WHERE phone_number = ?
        """, (phone_number,))
        conn.commit()
        conn.close()
    
    def record_purchase(self, phone_number: str, drug_name: str, 
                       quantity: int = 1, amount: float = 0):
        """Record purchase with medication tracking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get dosage information
        cursor.execute("""
            SELECT dosage_days, dosage_frequency FROM inventory WHERE drug_name = ?
        """, (drug_name.lower(),))
        
        drug_info = cursor.fetchone()
        dosage_days = drug_info['dosage_days'] if drug_info else 0
        dosage_frequency = drug_info['dosage_frequency'] if drug_info else 'as prescribed'
        
        # Calculate treatment end date
        treatment_end_date = (datetime.now() + timedelta(days=dosage_days)).date() if dosage_days > 0 else None
        
        cursor.execute("""
            INSERT INTO purchases (phone_number, drug_name, quantity, amount, dosage_days, 
                                 dosage_frequency, treatment_end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (phone_number, drug_name.lower(), quantity, amount, dosage_days, 
              dosage_frequency, treatment_end_date))
        
        # Update inventory
        cursor.execute("""
            UPDATE inventory 
            SET quantity = quantity - ?
            WHERE drug_name = ?
        """, (quantity, drug_name.lower()))
        
        conn.commit()
        conn.close()
    
    def get_medication_reminders(self) -> List[Dict]:
        """Get customers who need medication reminders"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        # Get active medications (not completed, within treatment period)
        cursor.execute("""
            SELECT 
                id,
                phone_number,
                drug_name,
                dosage_frequency,
                dosage_days,
                CAST(julianday(?) - julianday(purchase_date) AS INTEGER) as days_since_purchase,
                treatment_end_date,
                last_reminder_sent,
                reminders_sent,
                completed
            FROM purchases
            WHERE completed = 0
            AND (treatment_end_date IS NULL OR treatment_end_date >= ?)
            ORDER BY purchase_date DESC
        """, (today, today))
        
        reminders = []
        for row in cursor.fetchall():
            purchase = dict(row)
            days_since = purchase['days_since_purchase']
            last_sent = purchase['last_reminder_sent']
            
            # Determine if reminder is needed
            should_send = False
            reminder_type = 'daily'
            
            # Daily reminders during treatment
            if days_since <= purchase['dosage_days']:
                if last_sent is None or last_sent != str(today):
                    should_send = True
                    reminder_type = 'daily'
            
            # Follow-up after treatment completion
            elif days_since == purchase['dosage_days'] + 1:
                should_send = True
                reminder_type = 'completion'
            
            # Final checkup 3 days after completion
            elif days_since == purchase['dosage_days'] + 3:
                should_send = True
                reminder_type = 'checkup'
            
            if should_send:
                reminders.append({
                    'purchase_id': purchase['id'],
                    'phone_number': purchase['phone_number'],
                    'drug_name': purchase['drug_name'],
                    'dosage_frequency': purchase['dosage_frequency'],
                    'days_since_purchase': days_since,
                    'reminder_type': reminder_type
                })
        
        conn.close()
        return reminders
    
    def mark_reminder_sent(self, purchase_id: int):
        """Mark that reminder was sent"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        cursor.execute("""
            UPDATE purchases
            SET last_reminder_sent = ?,
                reminders_sent = reminders_sent + 1
            WHERE id = ?
        """, (today, purchase_id))
        
        conn.commit()
        conn.close()
    
    def mark_treatment_completed(self, purchase_id: int):
        """Mark treatment as completed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE purchases
            SET completed = 1
            WHERE id = ?
        """, (purchase_id,))
        
        conn.commit()
        conn.close()
    
    def get_predictive_analytics(self) -> Dict:
        """Generate predictive analytics and insights"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        analytics = {}
        
        # 1. Demand Forecasting (top selling drugs)
        cursor.execute("""
            SELECT drug_name, COUNT(*) as purchase_count, SUM(quantity) as total_qty
            FROM purchases
            WHERE purchase_date >= date('now', '-30 days')
            GROUP BY drug_name
            ORDER BY purchase_count DESC
            LIMIT 5
        """)
        analytics['top_drugs_30days'] = [dict(row) for row in cursor.fetchall()]
        
        # 2. Low Stock Prediction (items selling fast vs current stock)
        cursor.execute("""
            SELECT 
                i.drug_name,
                i.quantity as current_stock,
                COUNT(p.id) as sales_last_7days,
                ROUND(CAST(i.quantity AS FLOAT) / NULLIF(COUNT(p.id), 0), 1) as days_until_stockout
            FROM inventory i
            LEFT JOIN purchases p ON i.drug_name = p.drug_name 
                AND p.purchase_date >= date('now', '-7 days')
            WHERE i.quantity < 50
            GROUP BY i.drug_name
            HAVING COUNT(p.id) > 0
            ORDER BY days_until_stockout ASC
            LIMIT 5
        """)
        analytics['stockout_risk'] = [dict(row) for row in cursor.fetchall()]
        
        # 3. Customer Retention Metrics
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT phone_number) as total_customers,
                COUNT(DISTINCT CASE WHEN purchase_count > 1 THEN phone_number END) as returning_customers,
                ROUND(100.0 * COUNT(DISTINCT CASE WHEN purchase_count > 1 THEN phone_number END) / 
                      COUNT(DISTINCT phone_number), 1) as retention_rate
            FROM (
                SELECT phone_number, COUNT(*) as purchase_count
                FROM purchases
                WHERE purchase_date >= date('now', '-30 days')
                GROUP BY phone_number
            )
        """)
        analytics['retention_metrics'] = dict(cursor.fetchone())
        
        # 4. Revenue Trends (weekly comparison)
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN purchase_date >= date('now', '-7 days') THEN amount ELSE 0 END) as this_week,
                SUM(CASE WHEN purchase_date >= date('now', '-14 days') 
                    AND purchase_date < date('now', '-7 days') THEN amount ELSE 0 END) as last_week
            FROM purchases
        """)
        revenue = cursor.fetchone()
        analytics['revenue_trend'] = dict(revenue)
        if revenue['last_week'] and revenue['last_week'] > 0:
            analytics['revenue_trend']['growth_percent'] = round(
                ((revenue['this_week'] - revenue['last_week']) / revenue['last_week']) * 100, 1
            )
        else:
            analytics['revenue_trend']['growth_percent'] = 0
        
        # 5. Peak Hours Analysis
        cursor.execute("""
            SELECT 
                CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                COUNT(*) as message_count
            FROM conversations
            WHERE timestamp >= datetime('now', '-7 days')
            AND is_admin = 0
            GROUP BY hour
            ORDER BY message_count DESC
            LIMIT 3
        """)
        analytics['peak_hours'] = [dict(row) for row in cursor.fetchall()]
        
        # 6. Medication Adherence Rate
        cursor.execute("""
            SELECT 
                COUNT(*) as total_prescriptions,
                SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed_treatments,
                ROUND(100.0 * SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) as adherence_rate
            FROM purchases
            WHERE dosage_days > 0
            AND purchase_date >= date('now', '-30 days')
        """)
        adherence = cursor.fetchone()
        analytics['adherence_metrics'] = dict(adherence) if adherence['total_prescriptions'] else {
            'total_prescriptions': 0, 'completed_treatments': 0, 'adherence_rate': 0
        }
        
        conn.close()
        return analytics
    
    def get_inventory_analysis(self) -> Dict:
        """Generate comprehensive inventory analysis"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        analysis = {}
        
        # Total inventory value
        cursor.execute("""
            SELECT 
                COUNT(*) as total_items,
                SUM(quantity * price) as total_value,
                AVG(quantity) as avg_stock_level
            FROM inventory
        """)
        analysis['overview'] = dict(cursor.fetchone())
        
        # Low stock items
        cursor.execute("""
            SELECT drug_name, quantity, price, category
            FROM inventory
            WHERE quantity < 20
            ORDER BY quantity ASC
        """)
        analysis['low_stock'] = [dict(row) for row in cursor.fetchall()]
        
        # High value items
        cursor.execute("""
            SELECT drug_name, quantity, price, (quantity * price) as total_value
            FROM inventory
            ORDER BY total_value DESC
            LIMIT 5
        """)
        analysis['high_value_items'] = [dict(row) for row in cursor.fetchall()]
        
        # Stock by category
        cursor.execute("""
            SELECT 
                category,
                COUNT(*) as item_count,
                SUM(quantity) as total_quantity,
                SUM(quantity * price) as category_value
            FROM inventory
            GROUP BY category
            ORDER BY category_value DESC
        """)
        analysis['by_category'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return analysis
    
    def get_weekly_stats(self) -> Dict:
        """Get weekly statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM purchases
            WHERE purchase_date >= datetime('now', '-7 days')
        """)
        total_purchases = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT COUNT(DISTINCT phone_number) as count
            FROM purchases
            WHERE purchase_date >= datetime('now', '-7 days')
        """)
        unique_customers = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT drug_name, COUNT(*) as count
            FROM purchases
            WHERE purchase_date >= datetime('now', '-7 days')
            GROUP BY drug_name
            ORDER BY count DESC
            LIMIT 1
        """)
        top_result = cursor.fetchone()
        top_drug = top_result['drug_name'].title() if top_result else "N/A"
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM conversations
            WHERE timestamp >= datetime('now', '-7 days')
        """)
        total_messages = cursor.fetchone()['count']
        
        # Total revenue this week
        cursor.execute("""
            SELECT SUM(amount) as total
            FROM purchases
            WHERE purchase_date >= datetime('now', '-7 days')
        """)
        total_revenue = cursor.fetchone()['total'] or 0
        
        conn.close()
        
        return {
            "total_purchases": total_purchases,
            "unique_customers": unique_customers,
            "top_drug": top_drug,
            "total_messages": total_messages,
            "total_revenue": round(total_revenue, 2)
        }
    
    def search_inventory(self, query: str) -> List[Dict]:
        """Search inventory"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT drug_name, quantity, price, category, description, dosage_days, dosage_frequency
            FROM inventory
            WHERE drug_name LIKE ? OR category LIKE ? OR description LIKE ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results