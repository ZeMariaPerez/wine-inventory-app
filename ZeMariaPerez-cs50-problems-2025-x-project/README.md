# Wine Manager
#### Video Demo: https://youtu.be/FjIlIYdfCWE
#### Description:

### Project Background

Wine Manager is a Flask web application initially developed as part of the CS50x course, designed with real-world applicability in mind—particularly for restaurant owners and wine professionals. The platform offers a clean, user-friendly, and offline-first interface to help users manage their wine catalog, track inventory levels, record sales, and gain insights through visual analytics. It operates on a single set of credentials for all users, rather than individual user accounts, simplifying access while maintaining security.
The inspiration to develop this application stems from my background — being Portuguese and living in Portugal, a country renowned for its exceptional wines, which play an important role in our culture and daily life. More personally, my parents own a restaurant and are passionate wine enthusiasts. They’ve built an extensive and diverse wine cellar, striving to offer a premium selection of wines, including rare and unique ones. This project was born out of a desire to simplify their wine management process. For my CS50x final project, I chose to develop a tool that could genuinely make their day-to-day operations easier and more efficient.

### Key Features

- Register new wines with their detailed characteristics and description in order to build a wine catalog/database.
- From this catalog the user can update their inventory in real time.
- Log and view wine sales.
- Analytics dashboard with sales and stock visualizations grouped by wine type, producer, or region.

### Project Files Overview

- `app.py`: This is the main Flask application responsible for routing, data processing, and rendering HTML templates. While it contains various components, its core functionality revolves around handling user authentication (`login`), and managing the main features of the app: `register_wine`, `catalog`, `inventory`, `sales`, and `analytics`. Each of these routes interacts with a SQL database to retrieve, manipulate, and pass data to the client side, ensuring that users can seamlessly access and manage their information. Additionally, each route renders a dedicated HTML template, which will be described in more detail below;
- `templates/`: Contains HTML templates rendered by Flask. It includes:

    - `login.html`: This template provides a simple login form where users input their username and password. Flash messages appear if the login fails. The corresponding Flask function clears existing sessions, checks the submitted username and password against stored credentials, and either logs in the user or redirects them back with an error message. It's worth mentioning that every route after this point is protected by login authentication and there's a logout function that clears the session and redirects the user to the login page.
    - `layout.html`: The layout.html file is the base template for all pages in the Wine Manager app. It defines the overall structure, including a sidebar menu with links to each page (home, register, catalog, etc.) and a top strip for branding. The template uses Bootstrap for styling and responsiveness. Flash messages appear dynamically within the header section. The {% block main %} placeholder is where page-specific content is inserted, making this a reusable foundation for all views rendered through Flask.
    - `homepage.html`: This is the landing page after a successful login. It welcomes the user and provides a quick overview of the application's main features—registering wines, browsing the catalog, managing inventory, logging sales, and viewing analytics. The route simply renders the homepage template.
    - `register_wine.html`: This page allows users to register new wines into their catalog via a form. Fields include name, brand, region, type, year, alcohol %, bottle size, and optional fields like color (subtype) and description. The form uses datalists filled dynamically with existing values from the database to assist and streamline user input.
    When the form is submitted by POST, the Flask function first ensures all required fields are filled. Then it checks if the wine already exists—if not, it adds the new entry to the database. On GET, the function fetches distinct values from existing wines to populate the form’s suggestions, and renders the registration page.
    - `catalog.html`: The catalog.html template and its corresponding Flask route define the page where users can browse and manage the complete list of wines that have been registered in the system. When a user accesses the page, the Flask route fetches all wines from the wines table in the database and passes them to the template to be displayed in a structured table format. Each row in the table represents a wine and displays its key attributes, such as brand, producer, region, type, color, year, alcohol content, and bottle size.
    Users can filter the table by choosing a specific attribute from a dropdown menu and typing a value to match. Once filtered, only the relevant rows remain visible. Users may also click on a row to select a wine. When a wine is selected, a hidden section on the page becomes visible, showing its description. This same selection allows the user to perform two actions: add the wine to inventory or delete it from the catalog.
    When adding a wine to inventory, the user must input the quantity, purchase price, and selling price. If the wine already exists in the inventory, the system updates the record and recalculates the average buying price based on the new and existing quantities. If the wine is not yet in the inventory, it is inserted as a new entry. If the delete button is used instead, the route checks whether the wine has ever been sold. If it hasn’t, it is removed from both the wines and inventory tables. Otherwise, deletion is blocked and a warning message is shown.
    - `inventory.html`: The inventory.html template and its Flask route together handle the display and real-time management of the restaurant's wine inventory. When the user accesses the page via a GET request, the route queries the database to retrieve all wines currently in inventory, joining data from both the wines and inventory tables. This information is rendered in a dynamic, interactive table that shows key inventory details such as quantity, bottle size, average purchase price, and retail price.
    Users can filter the table using a dropdown menu and text input to narrow down wines by attributes like brand or year. From this interface, they can also select a wine row and choose to either add stock, register a sale, or delete a specific quantity. Depending on the action submitted via the form, the Flask route processes the request: adding bottles increases the inventory count, selling bottles decreases it and logs the transaction in the sales table, and deleting removes bottles directly without registering a sale.
    The route includes validation for quantity input and checks for constraints like preventing sales when there isn’t enough stock. It also updates or deletes records accordingly, ensuring the inventory remains accurate.
    - `sales.html`: The Sales page displays a table of all past wine sales. Users can click a row to select a sale, which highlights the row and stores its wine and sale ID. Clicking the "Undo Sale" button submits a POST request to the /sales route. The route checks if a sale was selected and updates the database accordingly: if the wine still exists in inventory, it adds the sold quantity back and deletes the sale record; if not, it restores the wine from the backup table. The table on the page is dynamically populated using data retrieved from the sales and wines tables. JavaScript handles row selection and form input updates. Flash messages inform the user of the result. The two_decimals() function ensures proper formatting of numeric values. The route supports both GET (to load sales data) and POST (to undo a sale).
    - `analytics.html`: The analytics.html template is used to display sales and inventory charts. It includes dropdown menus to allow users to select how to group the data (by wine type, producer, or region). The charts are initially loaded using the URLs /sales_plot.png and /inventory_plot.png. When a user selects an option from the dropdown, the JavaScript updates the chart's src attribute, triggering the Flask routes to generate new charts based on the selected grouping.
    The Flask route /analytics simply renders the analytics.html page. The /sales_plot.png and /inventory_plot.png routes are responsible for generating the respective charts. They call the generate_chart function, passing the chart type (sales or inventory) to determine which data to process. In generate_chart, the data is retrieved from the database, grouped by the selected property (defaulting to wine_type), and then a bar chart is generated using matplotlib. The chart is saved to a BytesIO object and returned as a PNG image, which is then displayed in the template.
    The charts are dynamically updated on the page without reloading because the src of the images is updated with the selected group_by parameter. The backend function generates and returns the image, which is displayed directly in the HTML.
- `static/`: Includes `styles.css`, which contains all custom CSS used for styling in the project;
- `helpers.py`: Contains helper functions such as number formatting and the `login_required` function;
- `wine.sql`: Defines the database schema which includes the `wines`, `sales`, `inventory`, and `inventory_backup` tables;
- `wine.db`: SQLite database file storing all data locally;
- `flask_session/`: Stores session data on the server;
- `requirements.txt`: Lists the Python packages that the project needs. It makes it easy to install all the necessary packages using pip;
- `README.md`: This file.

### Technologies Used

- Python (Flask framework and Matplotlib and Pandas for data processing and visualization);
- SQLite;
- HTML;
- JavaScript;
- CSS;
- Jinja2;
- Bootstrap (for responsive UI and styling);

### Future Enhancements for the Wine Manager App

- Edit wines in the catalog.
- Filter inventory by price (e.g., wines costing more/less than X).
- Search across all categories when no filter is applied.
- Show a confirmation before deleting a wine.
- Make more graphs for the analytics page, such as one displaying wines by price range.
