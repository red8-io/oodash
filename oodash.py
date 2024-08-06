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
    # Initialize DataManager
    data_manager = DataManager()

    if data_manager.df_portfolio is None or data_manager.df_portfolio.empty:
        logger.error("Unable to fetch data from Odoo. Please check your connection and try again.")
        return None

    # Initialize Dash app
    app = dash.Dash(__name__)

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
            logger.debug(f"Parsed url {parsed_url}")
            query_params = parse_qs(parsed_url.query)
            logger.debug(f"Query params {query_params}")
            token = query_params.get('token', [None])[0]
            logger.debug(f"Token: {token}")
            
            if token:
                try:
                    token_data = authenticate(token)

                    register_callbacks(app, data_manager)
                    logger.info("Callbacks registered")

                    return create_layout(data_manager, token)
                except ValueError as e:
                    logger.info(f"Authentication error: {e}")
                    return create_login_layout()
            else:
                return html.Div("No token provided")
        else:
            logger.debug(f"Could not retrieve href")
            return create_login_layout()

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
