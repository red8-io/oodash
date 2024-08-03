import os
import logging
from contextlib import asynccontextmanager

from dotenv import find_dotenv, load_dotenv

import plotly.graph_objs as go
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from llm_integration import check_ollama_status, extract_model_names
from data_management import DataManager
from layout import safe_unique_values
from auth import authenticate, TokenData

from callbacks.portfolio import portfolio

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
    
    yield
    
    # Shutdown: Clean up resources if needed

# Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

def get_data_manager():
    return data_manager

app.dependency_overrides[get_data_manager] = get_data_manager

app.include_router(portfolio)

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, token: str = Query(...)):
    try:
        # Verify the token
        token_data = authenticate(token)
        
        # If token is valid, serve the main page
        return templates.TemplateResponse("index.html", {
            "request": request,
            "token": token,
            "projects": safe_unique_values(data_manager.df_portfolio, 'name'),
            "employees": safe_unique_values(data_manager.df_employees, 'name'),
            "model_options": model_options
        })
    except HTTPException as e:
        logger.error(e)
        return templates.TemplateResponse("login.html", {"request": request})

@app.get("/api/refresh_data")
async def refresh_data(token_data: TokenData = Depends(authenticate)):
    data_manager.load_all_data(force=True)
    return {"message": "Data refreshed successfully"}

@app.get("/api/chart/global_kpi")
async def get_global_kpi_chart(token_data: TokenData = Depends(authenticate)):
    # Example: Create a simple bar chart
    fig = go.Figure(data=[go.Bar(x=['A', 'B', 'C'], y=[1, 2, 3])])
    return JSONResponse(content=fig.to_dict())

@app.get("/api/chart/financials")
async def get_financials_chart(token_data: TokenData = Depends(authenticate)):
    # Implement your financials chart logic here
    pass

# Add more API endpoints for other charts and data as needed

def main():
    import uvicorn
    logger.info("Starting the Oodash FastAPI+Plotly application")
    uvicorn.run(app, host=os.getenv('SERVICE_URL'), port=int(os.getenv('SERVICE_PORT')))

if __name__ == "__main__":
    main()
