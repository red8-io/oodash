from datetime import datetime
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from llm_integration import check_ollama_status, extract_model_names
from data_management import DataManager
from auth import verify_token, TokenData
from layout import safe_unique_values
from financial_calculator import FinancialCalculator

# Import the callback modules
from callbacks import global_kpi, financials, employees, llm

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(filename='cfg/.env', raise_error_if_not_found=True))

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(level=logging.WARNING,
                    format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Initialize DataManager
data_manager = DataManager()
financial_calculator = FinancialCalculator(data_manager)

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
    
    yield
    
    # Shutdown: Clean up resources if needed

# Create FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, token: str = Query(...)):
    try:
        # Verify the token
        token_data = verify_token(token)
        
        # If token is valid, serve the main page
        return templates.TemplateResponse("index.html", {
            "request": request,
            "token": token,
            "projects": safe_unique_values(data_manager.df_portfolio, 'name'),
            "employees": safe_unique_values(data_manager.df_employees, 'name'),
            "model_options": model_options
        })
    except HTTPException:
        return templates.TemplateResponse("login.html", {"request": request})

@app.get("/api/refresh_data")
async def refresh_data(token_data: TokenData = Depends(verify_token)):
    data_manager.load_all_data(force=True)
    return {"message": "Data refreshed successfully", "last_update": data_manager.last_update.strftime('%Y-%m-%d %H:%M:%S')}

@app.get("/api/chart/global_kpi")
async def get_global_kpi_chart(start_date: str, end_date: str, selected_projects: str = None, token_data: TokenData = Depends(verify_token)):
    fig_map, fig_kpi = global_kpi.update_global_kpi(start_date, end_date, selected_projects, data_manager)
    return JSONResponse(content={"map": fig_map.to_dict(), "kpi": fig_kpi.to_dict()})

@app.get("/api/chart/financials")
async def get_financials_chart(start_date: str, end_date: str, token_data: TokenData = Depends(verify_token)):
    fig_financials, total_revenue, fig_hours, fig_revenue, calculation_progress, _ = financials.update_financials(
        start_date, end_date, 1, data_manager, financial_calculator
    )
    return JSONResponse(content={
        "financials": fig_financials.to_dict(),
        "hours": fig_hours.to_dict(),
        "revenue": fig_revenue.to_dict(),
        "total_revenue": total_revenue,
        "calculation_progress": calculation_progress
    })

@app.get("/api/chart/employee_hours")
async def get_employee_hours_chart(start_date: str, end_date: str, selected_projects: str = None, selected_employees: str = None, chart_height: int = 600, token_data: TokenData = Depends(verify_token)):
    fig, total_hours = employees.update_employee_hours(
        start_date, end_date, selected_projects, selected_employees, chart_height, data_manager
    )
    return JSONResponse(content={"chart": fig.to_dict(), "total_hours": total_hours})

@app.get("/api/generate_llm_report")
async def generate_llm_report_api(selected_model: str, token_data: TokenData = Depends(verify_token)):
    report = llm.update_llm_report(1, selected_model, data_manager.serialize_dataframes([
        data_manager.df_portfolio,
        data_manager.df_employees,
        data_manager.df_sales,
        data_manager.df_timesheet,
        data_manager.df_tasks
    ]), data_manager)
    return JSONResponse(content={"report": report})

def main():
    import uvicorn
    logger.info("Starting the Oodash FastAPI+Plotly application")
    uvicorn.run(app, host="0.0.0.0", port=8003)

if __name__ == "__main__":
    main()
