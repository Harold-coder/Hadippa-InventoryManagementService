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

@app.route('/view_meals_student')
def view_meals_student():
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

@app.route('/manage_inventory', methods=['GET', 'POST'])
def manage_inventory():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')
        inventory_id = request.form.get('inventory_id')

    cursor.execute("SELECT * FROM Inventory")
    inventory = cursor.fetchall()
    conn.close()

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

@app.route("/view_meals_student/<string:dining_hall_id>")
def meals_by_dining_hall(dining_hall_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT * FROM Inventory 
        WHERE DiningHallID = %s 
        AND expirationtime > %s
    """
    cursor.execute(query, (dining_hall_id, datetime.now()))
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

@app.route("/view_meals_student/<int:inventory_id>")
def inventory_item(inventory_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
            SELECT * FROM Inventory 
            WHERE InventoryID = %s 
            AND expirationtime > %s
    """
    cursor.execute(query, (inventory_id, datetime.now()))
    item = cursor.fetchone()
    conn.close()

    if item is None:
        return jsonify({"error": "Inventory item not found"}), 404

    formatted_item = {
        "inventory_id": item[0],
        "dining_hall_id": item[1],
        "food_item": item[2],
        # ... add other fields as needed
    }

    return jsonify(formatted_item)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8012)

