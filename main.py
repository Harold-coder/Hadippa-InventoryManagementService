from flask import Flask, render_template, request, redirect, url_for
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


@app.route("/")
def index():
    return render_template('index.html')

#GRAPHQL
class MealType(ObjectType):
    inventory_id = String()
    dining_hall_id = String()
    food_item = String()
    quantity = String()
    price = String()
    expiration_time = String()
# GraphQL Query

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

@app.route('/view_meals_student')
def view_meals_student():
    return render_template('view_meals_student.html')
@app.route('/view_meals_worker')
def view_meals_worker():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    dining_hall_id = request.args.get('dining_hall_id', default=None, type=str)
    inventory_id = request.args.get('inventory_id', default=None, type=int)

    conn = get_db_connection()
    cursor = conn.cursor()

    if inventory_id:
        cursor.execute("SELECT * FROM Inventory WHERE InventoryID = %s LIMIT %s OFFSET %s",
                       (inventory_id, per_page, (page - 1) * per_page))
    elif dining_hall_id:
        cursor.execute("SELECT * FROM Inventory WHERE DiningHallID = %s LIMIT %s OFFSET %s",
                       (dining_hall_id, per_page, (page - 1) * per_page))
    else:
        cursor.execute("SELECT * FROM Inventory LIMIT %s OFFSET %s", (per_page, (page - 1) * per_page))

    inventory_items = cursor.fetchall()
    conn.close()

    # Pass the paginated inventory items to the template
    return render_template('view_meals_worker.html', inventory=inventory_items, page=page, per_page=per_page)


@app.route('/manage_inventory', methods=['GET', 'POST'])
def manage_inventory():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')
        inventory_id = request.form.get('inventory_id')

        try:
            if action == 'add' or action == 'update':
                # Fetching form fields common to both add and update actions
                dining_hall_id = request.form.get('dining_hall_id')
                food_item = request.form.get('food_item')
                quantity = request.form.get('quantity', type=int)
                price = request.form.get('price', type=float)
                expiration_time = request.form.get('expiration_time')

                # Convert expiration_time from string to datetime
                expiration_time = datetime.strptime(expiration_time, '%Y-%m-%dT%H:%M') if expiration_time else None

                if action == 'add':
                    # SQL query to add a new inventory item
                    cursor.execute(
                        "INSERT INTO Inventory (DiningHallID, FoodItem, Quantity, Price, ExpirationTime) VALUES (%s, %s, %s, %s, %s)",
                        (dining_hall_id, food_item, quantity, price, expiration_time))
                    conn.commit()
                elif action == 'update':
                    # SQL query to update an existing inventory item
                    cursor.execute(
                        "UPDATE Inventory SET DiningHallID=%s, FoodItem=%s, Quantity=%s, Price=%s, ExpirationTime=%s WHERE InventoryID=%s",
                        (dining_hall_id, food_item, quantity, price, expiration_time, inventory_id))
                    conn.commit()

            elif action == 'delete':
                # SQL query to delete an inventory item
                cursor.execute("DELETE FROM Inventory WHERE InventoryID=%s", (inventory_id,))
                conn.commit()

            conn.commit()

        except Exception as e:
            print("An error occurred:", e)
            conn.rollback()

    cursor.execute("SELECT * FROM Inventory")
    inventory = cursor.fetchall()
    conn.close()

    formatted_inventory = []
    for item in inventory:
        formatted_item = list(item)
        # Format datetime fields
        if formatted_item[5]:  # Assuming this is the ExpirationTime field
            formatted_item[5] = formatted_item[5].strftime('%Y-%m-%dT%H:%M')
        formatted_inventory.append(formatted_item)

    return render_template('manage_inventory.html', inventory=formatted_inventory)


@app.route("/view_meals_student/<string:dining_hall_id>")
def meals_by_dining_hall(dining_hall_id):
    current_datetime = datetime.now()

    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT * FROM Inventory 
        WHERE DiningHallID = %s 
        AND expirationtime > %s
        """
    cursor.execute(query, (dining_hall_id, current_datetime))
    meals = cursor.fetchall()
    conn.close()
    return render_template('meals_by_dining_hall.html', meals=meals, dining_hall_id=dining_hall_id)



@app.route("/view_meals_student/<int:inventory_id>")
def inventory_item(inventory_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    current_datetime = datetime.now()  # Get the current date and time

    query = """
            SELECT * FROM Inventory 
            WHERE InventoryID = %s 
            AND expirationtime > %s
            """

    # Provide both inventory_id and current_datetime as parameters
    cursor.execute(query, (inventory_id, current_datetime))
    item = cursor.fetchone()

    cursor.close()
    conn.close()

    if item is None:
        return "Inventory item not found", 404

    print(item)

    return render_template('inventory_item.html', item=item)

# Adding GraphQL route
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True  # Enables GraphiQL interface
    )
)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8012)

