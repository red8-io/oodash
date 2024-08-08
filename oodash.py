import os

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from dotenv import find_dotenv, load_dotenv
from urllib.parse import urlparse, parse_qs

from callbacks.callbacks import register_callbacks
from data_management import DataManager
from layout import create_layout, create_login_layout
from auth import authenticate
from logging_config import setup_logging

logger = setup_logging()

load_dotenv(find_dotenv(filename='cfg/.env', raise_error_if_not_found=True))

def create_app():
    # Initialize Dash app
    app = dash.Dash(__name__, suppress_callback_exceptions=True)

    # Initialize DataManager
    data_manager = DataManager()

    login_layout = create_login_layout()
    logged_in_layout = create_layout(data_manager)

    register_callbacks(app, data_manager)
    logger.info("Callbacks registered")

    # Add a new function to retrieve token from URL
    def serve_layout():
        return html.Div([
            dcc.Location(id='url', refresh=False),
            html.Div(id='page-content')
        ])

    app.layout = serve_layout

    # Callback to update the page content based on authentication
    @app.callback(Output('page-content', 'children'),
                  Input('url', 'href'))
    def display_page(href):
        print(f"DEBUG: {href}")

        if href:
            parsed_url = urlparse(href)
            query_params = parse_qs(parsed_url.query)
            token = query_params.get('token', [None])[0]
            
            if token:
                try:
                    token_data = authenticate(token)

                    if token_data:
                        data_manager.load_all_data()

                        return logged_in_layout

                except ValueError as e:
                    logger.info(f"Authentication error: {e}")

        return login_layout

    return app

def main():
    app = create_app()

    if app:
        logger.info("Dash server starting...")
        app.run_server(debug=True, host=os.getenv('SERVICE_URL'), port=int(os.getenv('SERVICE_PORT')))
    else:
        logger.info("Failed to start dash server")

if __name__ == '__main__':
    main()
