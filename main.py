import logging
from contextlib import asynccontextmanager

import dash
from dotenv import find_dotenv, load_dotenv

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from callbacks.callbacks import register_callbacks
from llm_integration import check_ollama_status, extract_model_names
from data_management import DataManager
from layout import create_dash_layout
from auth import verify_token, TokenData

load_dotenv(find_dotenv(filename='cfg/.env', raise_error_if_not_found=True))

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(level=logging.WARNING,
                    format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Initialize DataManager
data_manager = DataManager()

if data_manager.df_portfolio is None or data_manager.df_portfolio.empty:
    logging.error("Unable to fetch data from Odoo. Please check your connection and try again.")
    raise SystemExit("Failed to initialize DataManager")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

model_options = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Ollama models
    global model_options
    ollama_running, available_models = check_ollama_status()
    if ollama_running:
        model_options = [{'label': model, 'value': model} for model in extract_model_names(available_models)]
    else:
        model_options = []
    
    # Update Dash layout with model options
    dash_app.layout = create_dash_layout(data_manager, model_options)
    
    yield
    
    # Shutdown: Clean up resources if needed

# Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# Create Dash app
dash_app = dash.Dash(__name__, server=app, url_base_pathname='/dash/')
dash_app.config.suppress_callback_exceptions = True

# Set up initial Dash layout
dash_app.layout = create_dash_layout(data_manager, [])  # Empty list for model_options, will be updated in lifespan

# Register Dash callbacks
register_callbacks(dash_app, data_manager)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, token: str = Query(...)):
    try:
        # Verify the token
        token_data = verify_token(token)
        
        # If token is valid, serve the Dash app
        return templates.TemplateResponse("root_page.html", {"request": request, "token": token})
    except HTTPException:
        return RedirectResponse(url="/login")

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login_page.html", {"request": request})

@app.get("/api/refresh_data")
async def refresh_data(token_data: TokenData = Depends(verify_token)):
    data_manager.load_all_data(force=True)
    return {"message": "Data refreshed successfully"}

def main():
    # Mount Dash app
    app.mount("/dash", WSGIMiddleware(dash_app.server))

    import uvicorn
    logger.info("Starting the Oodash FastAPI+Dash application")
    uvicorn.run(app, host="0.0.0.0", port=8003)

if __name__ == "__main__":
    main()
