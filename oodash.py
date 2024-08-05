import logging
import os

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dotenv import find_dotenv, load_dotenv
from flask import request, redirect

from callbacks.callbacks import register_callbacks
from data_management import DataManager
from layout import create_layout, create_login_layout
from auth import authenticate

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

    # Define the layout with a div for the content
    app.layout = html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content')
    ])

    # Callback to update the page content based on authentication
    @app.callback(Output('page-content', 'children'),
                  Input('url', 'pathname'))
    def display_page(pathname):
        # Get the JWT from the cookie
        jwt_cookie = request.cookies.get('access_token')
        if jwt_cookie and jwt_cookie.startswith('Bearer '):
            token = jwt_cookie.split(' ')[1]
            try:
                token_data = authenticate(token)

                register_callbacks(app, data_manager)
                logging.debug("Callbacks registered")

                return create_layout(data_manager)
            except Exception as e:
                logging.error(f"Authentication error: {str(e)}")
                return create_login_layout()
        else:
            return create_login_layout()

    return app

def main():
    app = create_app()

    if app:
        logging.info("Starting Dash server")
        app.run_server(debug=True, host=os.getenv('SERVICE_URL'), port=int(os.getenv('SERVICE_PORT')))
    else:
        logging.error("Failed to create app")

if __name__ == '__main__':
    main()
