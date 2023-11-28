from flask import Flask, render_template, request, redirect, url_for
import psycopg2
from datetime import datetime
from credentials import databaseKeys

app = Flask(__name__)


# Database connection function
def get_db_connection():
    return psycopg2.connect(
        host='db-cc.co4twflu4ebv.us-east-1.rds.amazonaws.com',
        port=5432,
        user=databaseKeys.username,  # Replace with your actual username
        password=databaseKeys.password,  # Replace with your actual password
        database='lion_leftovers'
    )


@app.route("/")
def index():
    return render_template('index.html')


@app.route('/view_meals_student')
def view_meals_student():
    conn = get_db_connection()
    cursor = conn.cursor()

    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of items per page
    offset = (page - 1) * per_page

    # Current date and time
    now = datetime.now()

    # Fetch non-expired data with pagination, including DiningHallID
    cursor.execute("SELECT InventoryID, DiningHallID, FoodItem, Quantity, Price FROM Inventory WHERE ExpirationTime > %s LIMIT %s OFFSET %s", (now, per_page, offset))
    inventory = cursor.fetchall()

    # Get total number of non-expired items
    cursor.execute("SELECT COUNT(*) FROM Inventory WHERE ExpirationTime > %s", (now,))
    total_items = cursor.fetchone()[0]
    total_pages = (total_items + per_page - 1) // per_page

    return render_template('view_meals_student.html', inventory=inventory, total_pages=total_pages)


@app.route('/view_meals_worker')
def view_meals_worker():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Inventory")
    inventory = cursor.fetchall()

    return render_template('view_meals_worker.html', inventory=inventory)


@app.route('/manage_inventory', methods=['GET', 'POST'])
def manage_inventory():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')
        inventory_id = request.form.get('inventory_id')
        dining_hall_id = request.form['dining_hall_id']
        food_item = request.form['food_item']
        quantity = request.form['quantity']
        price = request.form['price']
        expiration_time = request.form['expiration_time']

        try:
            if action == 'add':
                cursor.execute(
                    "INSERT INTO Inventory (DiningHallID, FoodItem, Quantity, Price, ExpirationTime) VALUES (%s, %s, %s, %s, %s)",
                    (dining_hall_id, food_item, quantity, price, expiration_time))
            elif action == 'update':
                cursor.execute(
                    "UPDATE Inventory SET DiningHallID=%s, FoodItem=%s, Quantity=%s, Price=%s, ExpirationTime=%s WHERE InventoryID=%s",
                    (dining_hall_id, food_item, quantity, price, expiration_time, inventory_id))
            elif action == 'delete':
                cursor.execute("DELETE FROM Inventory WHERE InventoryID=%s", (inventory_id,))
            conn.commit()
        except Exception as e:
            print("An error occurred:", e)
            conn.rollback()

    cursor.execute("SELECT * FROM Inventory")
    inventory = cursor.fetchall()

    formatted_inventory = []
    for item in inventory:
        formatted_item = list(item)
        if formatted_item[5]:  # Assuming this is the datetime field
            formatted_item[5] = formatted_item[5].strftime('%Y-%m-%dT%H:%M')
        formatted_inventory.append(formatted_item)

    return render_template('manage_inventory.html', inventory=formatted_inventory)


if __name__ == '__main__':
    app.run(debug=True, port=8012)

