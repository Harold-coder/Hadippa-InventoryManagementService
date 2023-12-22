from flask import Flask, request, jsonify
import psycopg2
from datetime import datetime
from graphene import ObjectType, String, List, Schema
from flask_graphql import GraphQLView

app = Flask(__name__)

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        host='db-cc.co4twflu4ebv.us-east-1.rds.amazonaws.com',
        port=5432,
        user='master',
        password='MasterPassword',
        database='lion_leftovers'
    )

# GraphQL setup
class MealType(ObjectType):
    inventory_id = String()
    dining_hall_id = String()
    food_item = String()
    quantity = String()
    price = String()
    expiration_time = String()

class Query(ObjectType):
    all_meals = List(MealType)

    def resolve_all_meals(self, info):
        conn = get_db_connection()
        cursor = conn.cursor()
        current_time = datetime.now()
        query = """
        SELECT InventoryID, DiningHallID, FoodItem, Quantity, Price, ExpirationTime 
        FROM Inventory 
        WHERE ExpirationTime > %s
        """
        cursor.execute(query, (current_time,))  # Filter out expired meals
        result = cursor.fetchall()
        conn.close()
        return [MealType(
            inventory_id=str(row[0]),
            dining_hall_id=str(row[1]),
            food_item=row[2],
            quantity=str(row[3]),
            price=str(row[4]),
            expiration_time=row[5].strftime('%Y-%m-%d %H:%M:%S')
        ) for row in result]

# Setup GraphQL Schema
schema = Schema(query=Query)

# Adding GraphQL route
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True  # Enables GraphiQL interface
    )
)

@app.route('/available_meals', methods=['GET'])
def available_meals():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Get the current time
    current_time = datetime.now()

    # Modify the SQL query to only select non-expired meals
    query = """
    SELECT * FROM Inventory 
    WHERE ExpirationTime > %s
    """
    cursor.execute(query, (current_time,))
    inventory_items = cursor.fetchall()
    conn.close()

    meals = [
        {
            "inventory_id": item[0],
            "dining_hall_id": item[1],
            "food_item": item[2],
            # ... add other fields as needed
        }
        for item in inventory_items
    ]

    return jsonify(meals)

# Endpoint for viewing the inventory
@app.route('/view_inventory', methods=['GET'])
def view_inventory():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all inventory items
    cursor.execute("SELECT * FROM Inventory")
    inventory = cursor.fetchall()
    conn.close()

    # Format the inventory for JSON response
    formatted_inventory = [
        {
            "inventory_id": item[0],
            "dining_hall_id": item[1],
            "food_item": item[2],
            # ... add other fields as needed
        }
        for item in inventory
    ]

    return jsonify(formatted_inventory)

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        data = request.get_json(force=True)  # force=True will force the parsing

        action = data.get('action')
        inventory_id = data.get('inventory_id')
        dining_hall_id = data.get('dining_hall_id')
        food_item = data.get('food_item')
        quantity = data.get('quantity')
        price = data.get('price')
        expiration_time = data.get('expiration_time')

        print(data)

        if action == 'update':
            cursor.execute(
                "UPDATE Inventory SET DiningHallID=%s, FoodItem=%s, Quantity=%s, Price=%s, ExpirationTime=%s WHERE InventoryID=%s",
                (dining_hall_id, food_item, quantity, price, expiration_time, inventory_id))
        elif action == 'delete':
            cursor.execute("DELETE FROM Inventory WHERE InventoryID=%s", (inventory_id,))
        elif action == 'add':
            cursor.execute(
                "INSERT INTO Inventory (DiningHallID, FoodItem, Quantity, Price, ExpirationTime) VALUES (%s, %s, %s, %s, %s)",
                (dining_hall_id, food_item, quantity, price, expiration_time))
        else:
            return jsonify({"error": "Invalid action"}), 400

        conn.commit()
        return jsonify({"success": f"Inventory item {action}d successfully"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/meals_by_dining_hall/<string:dining_hall_id>", methods=['GET'])
def meals_by_dining_hall(dining_hall_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT * FROM Inventory 
        WHERE DiningHallID = %s 
    """
    cursor.execute(query, (dining_hall_id,))
    meals = cursor.fetchall()
    conn.close()

    formatted_meals = [
        {
            "inventory_id": meal[0],
            "dining_hall_id": meal[1],
            "food_item": meal[2],
            # ... add other fields as needed
        }
        for meal in meals
    ]

    return jsonify(formatted_meals)

@app.route("/inventory_item/<int:inventory_id>", methods=['GET'])
def inventory_item(inventory_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
            SELECT * FROM Inventory 
            WHERE InventoryID = %s
    """
    cursor.execute(query, (inventory_id,))
    item = cursor.fetchone()
    conn.close()

    if item is None:
        return jsonify({"error": "Inventory item not found"}), 404

    print(item)
    formatted_item = {
        "inventory_id": item[0],
        "dining_hall_id": item[1],
        "food_item": item[2],
        "quantity:": item[3], 
        "price:": item[4]
    }

    return jsonify(formatted_item)

@app.route("/")
def index():
    return jsonify({"message": "Welcome to the InventoryManagement API Hosted on EC2!"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8012)

