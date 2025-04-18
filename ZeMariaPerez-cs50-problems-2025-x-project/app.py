import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.express as px
import io
from flask import Flask, flash, redirect, render_template, send_file, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helper import login_required, one_decimal, two_decimals


# Initialize the Flask application
app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Create hardcoded credentials for admin login
hashed_password = generate_password_hash("CS50wine")
credentials = {"user": "CS50user", "hashed_password": hashed_password}

# Function to get a new DB connection for each request
def get_db_connection():
    conn = sqlite3.connect("wine.db")
    conn.row_factory = sqlite3.Row
    return conn

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Define login page
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        # Clear any previous session data
        session.clear()

        # Check username first
        if request.form.get("username") != credentials["user"]:
            flash("This user name does not exist!", "danger")
            return redirect("/login")

        # Check password, if username is correct
        if not check_password_hash(credentials["hashed_password"], request.form.get("password")):
            flash("Incorrect password!", "danger")
            return redirect("/login")

        # If credentials are valid, login the user
        session["user_id"] = credentials["user"]
        return redirect("/")

    else:
        return render_template("login.html")


# Define homepage
@app.route("/", methods=["GET"])
@login_required
def homepage():

    return render_template("homepage.html")

# Define logout button
@app.route("/logout")
def logout():

    #Clear session
    session.clear()

    #Redirect user to login form
    return redirect("/")

# Route to register wines in the wine catalog
@app.route("/register_wine", methods=["GET", "POST"])
@login_required
def register_wine():

    # Get a new DB connection
    connection = get_db_connection()
    cursor = connection.cursor()

    if request.method == "POST":

        # Ensure all required input fields are filled by the user
        wine_parameters = ["wine_name", "brand", "region", "wine_type", "year", "alcohol", "bottle_size"]
        for parameter in wine_parameters:
            if not request.form.get(parameter):
                flash("Make sure all required fields are filled!", "danger")
                return redirect("/register_wine")

        wine_name = request.form.get("wine_name").title()
        brand = request.form.get("brand").title()
        region = request.form.get("region").title()
        wine_type = request.form.get("wine_type").title()
        subtype = request.form.get("subtype").title() or "-"
        year = request.form.get("year")
        alcohol = float(request.form.get("alcohol"))
        size = float(request.form.get("bottle_size"))
        description = request.form.get("description").capitalize() or "-"

        # If the wine doesn't already exist in the DB, insert entered fields into the database
        try:
            query = """INSERT INTO wines
                (wine_name, brand, region, wine_type, subtype, year, alcohol, bottle_size, description)
                VALUES (?,?,?,?,?,?,?,?,?)"""
            cursor.execute(query, (wine_name, brand, region, wine_type, subtype, year, alcohol, size, description))
            connection.commit()
            flash("Wine registered successfully!", "success")
        except sqlite3.IntegrityError:
            flash("This wine already exists in the catalog!", "danger")
        finally:
            connection.close()
        return redirect("/catalog")

    else:

        # Fetch distinct values for each wine attribute to populate form suggestions
        fields = ["region", "wine_name", "brand", "wine_type", "subtype", "year", "bottle_size"]
        queries = {}

        for field in fields:
            cursor.execute(f"SELECT DISTINCT {field} FROM wines")
            queries[field] = cursor.fetchall()

        regions = queries["region"]
        wine_names = queries["wine_name"]
        brands = queries["brand"]
        wine_types = queries["wine_type"]
        subtypes = queries["subtype"]
        years = queries["year"]
        bottle_sizes = queries["bottle_size"]

        connection.close()

        return render_template("register_wine.html", regions=regions, wine_names=wine_names, brands=brands, types=wine_types, subtypes=subtypes, years=years, bottle_sizes=bottle_sizes)


# Route to visualize the catalogue and add wines to the inventory
@app.route("/catalog", methods=["GET", "POST"])
@login_required
def catalog():

    # Get a new DB connection
    connection = get_db_connection()
    cursor = connection.cursor()

    if request.method == "POST":

        wine_id = request.form.get("wine_id")

        # Ensure a wine was selected
        if not wine_id:
            flash("Select a wine first!", "danger")
            return redirect("/catalog")

        # Handle adding wine to inventory
        if request.form.get("action_type") == "add":

            # Ensure the inputs are valid and a wine was selected
            try:
                new_quantity = int(request.form.get("quantity"))
                selling_price = float(request.form.get("selling_price"))
                buying_price = float(request.form.get("buying_price"))
            except ValueError:
                flash("Invalid quantity or selling price!", "danger")
                return redirect("/catalog")
            if new_quantity <= 0 or selling_price <= 0 or buying_price <= 0:
                flash("Invalid quantity or selling price!", "danger")
                return redirect("/catalog")

            # Adding the new or existing wine in the inventory
            cursor.execute("SELECT quantity FROM inventory WHERE wine_id = ?", (wine_id,))
            quantity_row = cursor.fetchone()
            if quantity_row is None:
                cursor.execute("INSERT INTO inventory (wine_id, selling_price, quantity, buying_price) VALUES (?,?,?,?)", (wine_id, selling_price, new_quantity, buying_price))
            else:
                existing_quantity = quantity_row["quantity"]
                total_quantity = existing_quantity + new_quantity
                cursor.execute("SELECT buying_price FROM inventory WHERE wine_id = ?", (wine_id,))
                avg_buying_price = float(cursor.fetchone()[0])
                avg_buying_price = (buying_price * new_quantity + avg_buying_price * existing_quantity) / total_quantity
                cursor.execute("UPDATE inventory SET selling_price = ?, quantity = ?, buying_price = ? WHERE wine_id = ?", (selling_price, total_quantity, avg_buying_price, wine_id))

            connection.commit()
            connection.close()

            flash("Wine inventory updated successfully!", "success")
            return redirect("/inventory")

        # Handle deleting wine from the database and inventory
        elif request.form.get("action_type") == "delete":

            cursor.execute("SELECT wine_id FROM sales")
            sold_wines_rows = cursor.fetchall()
            sold_wines_ids = [str(row[0]) for row in sold_wines_rows]
            if wine_id in sold_wines_ids:

                flash("This wine cannot be deleted because it has already been sold once before!", "danger")

            else:

                cursor.execute("DELETE FROM inventory WHERE wine_id = ?", (wine_id,))
                cursor.execute("DELETE FROM wines WHERE id = ?", (wine_id,))

                connection.commit()

                flash("Wine deleted succesfully!", "success")

            connection.close()
            return redirect("/catalog")

    else:

        #Access and fetch all the registered wines to display in the catalog table
        cursor.execute("SELECT * FROM wines")
        catalog = cursor.fetchall()

        connection.close()
        return render_template("catalog.html", catalog=catalog, one_decimal=one_decimal, two_decimals=two_decimals)


# Route to display the inventory and handle updates (adding/removing items)
@app.route("/inventory", methods=["GET", "POST"])
@login_required
def inventory():

    # Get a connection to the DB
    connection = get_db_connection()
    cursor = connection.cursor()

    if request.method == "POST":

        if request.form.get("form_action") == "add_sell":

            # Ensure the input is valid
            try:
                quantity = int(request.form.get("quantity"))
            except ValueError:
                flash("Invalid quantity!", "danger")
                return redirect("/inventory")

            if quantity <= 0 or not quantity:
                flash("Invalid quantity!", "danger")
                return redirect("/inventory")

            wine_id = request.form.get("wine_id")
            cursor.execute("SELECT quantity FROM inventory WHERE wine_id = ?", (wine_id,))
            quantity_row = cursor.fetchone()
            existing_quantity = quantity_row["quantity"]

            # Handles the case the user chooses to add bottles to their inventory
            if request.form.get("action_type") == "add":

                total_quantity = existing_quantity + quantity
                cursor.execute("UPDATE inventory SET quantity = ? WHERE wine_id = ?", (total_quantity, wine_id))

                connection.commit()
                connection.close()

                flash("Wine inventory updated successfully!", "success")
                return redirect("/inventory")

            # Handles the case the user chooses to sell bottles from their inventory
            elif request.form.get("action_type") == "sell":

                if quantity > existing_quantity:
                    flash("Insufficient quantity available for this wine!", "danger")
                    return redirect("/inventory")

                cursor.execute("SELECT selling_price, buying_price FROM inventory WHERE wine_id = ?", (wine_id,))
                row = cursor.fetchone()
                buying_price_per_bottle = row["buying_price"]
                total_buying_price = buying_price_per_bottle * quantity
                selling_price_per_bottle = row["selling_price"]
                total_selling_price = selling_price_per_bottle * quantity
                profit = total_selling_price - total_buying_price

                date_time = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
                cursor.execute("INSERT INTO sales (wine_id, bottle_quantity, sale_value, sale_date) VALUES (?,?,?,?)", (wine_id, quantity, profit, date_time))

                if quantity == existing_quantity:
                    cursor.execute("INSERT INTO inventory_backup (wine_id, selling_price, buying_price, quantity) VALUES (?,?,?,?)", (wine_id, selling_price_per_bottle, buying_price_per_bottle, existing_quantity)) # Auxiliary table to use later in the "sales" function
                    cursor.execute("DELETE FROM inventory WHERE wine_id = ?", (wine_id,))

                else:
                    new_quantity = existing_quantity - quantity
                    cursor.execute("UPDATE inventory SET quantity = ? WHERE wine_id = ?", (new_quantity, wine_id))

                connection.commit()
                connection.close()

                flash("Sale registered successfully!", "success")
                return redirect("/sales")

        # Handles the case the user wants to delete some or every bottle of a specific type from the inventory
        elif request.form.get("form_action") == "delete":

            # Ensure the input is valid
            try:
                quantity = int(request.form.get("quantity_del"))
            except ValueError:
                flash("Invalid quantity!", "danger")
                return redirect("/inventory")

            if quantity <= 0 or not quantity:
                flash("Invalid quantity!", "danger")
                return redirect("/inventory")

            # Ensure a wine is selected
            wine_id = request.form.get("wine_id_2")
            if not wine_id:
                flash("Select a wine first!", "danger")
                return redirect("/inventory")

            cursor.execute("SELECT quantity FROM inventory WHERE wine_id = ?", (wine_id,))
            quantity_row = cursor.fetchone()
            existing_quantity = quantity_row["quantity"]

            # Delete the bottles
            if quantity >= existing_quantity:
                    cursor.execute("DELETE FROM inventory WHERE wine_id = ?", (wine_id,))
            else:
                new_quantity = existing_quantity - quantity
                cursor.execute("UPDATE inventory SET quantity = ? WHERE wine_id = ?", (new_quantity, wine_id))

            connection.commit()
            connection.close()

            flash("Bottles deleted successfully!", "success")
            return redirect("/inventory")

    else:

        # Select the columns needed from the database to display in the inventory table
        cursor.execute("SELECT * FROM wines JOIN inventory ON wines.id = inventory.wine_id")
        inventory = cursor.fetchall()

        connection.close()
        return render_template("inventory.html", inventory=inventory, two_decimals=two_decimals)


@app.route("/sales", methods=["GET", "POST"])
@login_required
def sales():

    # Get a connection to the DB
    connection = get_db_connection()
    cursor = connection.cursor()

    if request.method == "POST":

        sale_id = request.form.get("sale_id")
        wine_id = request.form.get("wine_id")

        # Check if a sale was chosen
        if not sale_id:
            flash("Select a sale to undo!", "danger")
            return redirect("/sales")

        # Get the quantity in inventory after a wrongful sale
        cursor.execute("SELECT quantity FROM inventory WHERE wine_id = ?", (wine_id,))
        wrong_quantity_row = cursor.fetchone()

        # Handle the case where a wrong sale was registered, but the respective wine still exists in the inventory
        if wrong_quantity_row is not None:

            wrong_quantity = wrong_quantity_row["quantity"]

            # Get the quantity of the wrongful sale
            cursor.execute("SELECT bottle_quantity FROM sales WHERE id = ?", (sale_id,))
            sale_quantity = cursor.fetchone()["bottle_quantity"]

            # Introduce the original quantity of the wine in question in the inventory
            original_quantity = wrong_quantity + sale_quantity
            cursor.execute("UPDATE inventory SET quantity = ? WHERE wine_id = ?", (original_quantity, wine_id))
            cursor.execute("DELETE FROM sales WHERE id = ?", (sale_id,))

        #Handle the case when a wrong wine was registered and there was no more bottles of that wine in the inventory
        else:

            cursor.execute("SELECT * FROM inventory_backup WHERE wine_id = ?", (wine_id,))
            row = cursor.fetchone()
            selling_price = row["selling_price"]
            buying_price = row["buying_price"]
            quantity = row["quantity"]
            cursor.execute("INSERT INTO inventory (wine_id, selling_price, buying_price, quantity) VALUES (?,?,?,?)", (wine_id, selling_price, buying_price, quantity))
            cursor.execute("DELETE FROM inventory_backup")

        cursor.execute("DELETE FROM sales WHERE id = ?", (sale_id,))

        connection.commit()
        connection.close()

        flash("Sale removed from records!", "success")
        return redirect("/sales")

    else:
        cursor.execute("""
            SELECT
                sales.id AS sale_id,
                sales.wine_id AS wine_id,
                sales.bottle_quantity,
                sales.sale_value,
                sales.sale_date,
                wines.wine_name,
                wines.brand,
                wines.wine_type,
                wines.year,
                wines.bottle_size
            FROM sales
            JOIN wines ON wines.id = sales.wine_id
        """)
        sales = cursor.fetchall()

        connection.close()
        return render_template("sales.html", sales=sales, two_decimals=two_decimals)


# Route to display graphs about sales and inventory
@app.route("/analytics", methods=["GET"])
@login_required
def analytics():

    return render_template('analytics.html')

# Route to Generate and Serve the Sales Chart
@app.route('/sales_plot.png')
@login_required
def sales_plot():

    return generate_chart("sales")

# Route to Generate and Serve the Inventory Chart
@app.route('/inventory_plot.png')
@login_required
def inventory_plot():

    return generate_chart("inventory")

# Function to Generate Chart
def generate_chart(chart_type):

    # Get user selection, defaulting to wine_type
    group_by = request.args.get("group_by", "wine_type")

    # Read tables
    connection = get_db_connection()
    wines_df = pd.read_sql_query("SELECT * FROM wines", connection)

    if chart_type == "sales":
        sales_df = pd.read_sql_query("SELECT * FROM sales", connection)
        dataframe = pd.merge(sales_df, wines_df, left_on='wine_id', right_on='id')
        data_series = dataframe.groupby(group_by)['sale_value'].sum()
        y_label = "Sales Profit (€)"

    elif chart_type == "inventory":
        inventory_df = pd.read_sql_query("SELECT * FROM inventory", connection)
        dataframe = pd.merge(inventory_df, wines_df, left_on='wine_id', right_on='id')
        data_series = dataframe.groupby(group_by)['quantity'].sum()
        y_label = "Quantity in Stock"

    connection.close()

    # Apply Styling
    plt.rcParams.update({
        'font.size': 10,
        'font.family': 'DejaVu Sans',
        'text.color': '#7b1e1e',
        'axes.labelcolor': '#7b1e1e',
        'xtick.color': '#7b1e1e',
        'ytick.color': '#7b1e1e',
        'axes.titlecolor': '#7b1e1e'
    })

    colors = ["#7b1e1e", "#f3db9e"]

    # Generate Matplotlib figure
    fig, ax = plt.subplots(figsize=(11, 5))
    bar_colors = [colors[i % 2] for i in range(len(data_series))]
    data_series.plot(kind='bar', ax=ax, color=bar_colors)

    # Rotate labels
    ax.set_xticklabels(data_series.index, rotation=45, ha="right")

    # Set background color
    fig.patch.set_facecolor('#fdf8f5')
    ax.set_facecolor('#fdf8f5')

    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    label_mapping = {
        "wine_type": "Wine Type",
        "brand": "Wine Producer",
        "region": "Wine Region"
    }

    ax.set_title(f"{y_label} by {label_mapping[group_by]}", fontsize=12)
    ax.set_xlabel(label_mapping[group_by], fontsize=11, labelpad=15)
    ax.set_ylabel(y_label, fontsize=11, labelpad=10)
    ax.grid(axis='y', linestyle='--', alpha=0.6)

    # Save plot to BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)

    return send_file(img, mimetype='image/png')



