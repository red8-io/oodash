import logging

import dash
from dotenv import find_dotenv, load_dotenv

from callbacks.callbacks import register_callbacks
from data_management import DataManager
from layout import create_layout

load_dotenv(find_dotenv(filename='cfg/.env', raise_error_if_not_found=True))

# Configure logging
logging.basicConfig(level=logging.WARNING,
                    format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

def create_app():
    # Initialize DataManager
    data_manager = DataManager()

    if data_manager.df_portfolio is None or data_manager.df_portfolio.empty:
        logging.error("Unable to fetch data from Odoo. Please check your connection and try again.")
        return None

    # Initialize Dash app
    app = dash.Dash(__name__)

    app.layout = create_layout(data_manager)

    # Register callbacks after all data is loaded
    register_callbacks(app, data_manager)
    logging.debug("Callbacks registered")

    return app

def main():
    app = create_app()

    if app:
        logging.info("Starting Dash server")
        app.run_server(debug=True, host='0.0.0.0', port=8003)
    else:
        logging.error("Failed to create app")

if __name__ == '__main__':
    main()
