import plotly.graph_objs as go
import pandas as pd
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from auth import verify_token, TokenData
from data_management import DataManager

portfolio = APIRouter()

def get_data_manager():
    # This function should return the DataManager instance
    # It will be implemented in main.py
    pass

@portfolio.get("/api/portfolio")
async def get_portfolio_data(
    start_date: str = Query(...),
    end_date: str = Query(...),
    selected_projects: Optional[List[str]] = Query(None),
    selected_employees: Optional[List[str]] = Query(None),
    chart_height: int = Query(400),
    token_data: TokenData = Depends(verify_token),
    data_manager: DataManager = Depends(get_data_manager)
):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    filtered_timesheet = data_manager.df_timesheet[
        (data_manager.df_timesheet['date'] >= start_date) &
        (data_manager.df_timesheet['date'] <= end_date)
    ]

    if selected_projects:
        filtered_timesheet = filtered_timesheet[filtered_timesheet['project_name'].isin(selected_projects)]

    if selected_employees:
        filtered_timesheet = filtered_timesheet[filtered_timesheet['employee_name'].isin(selected_employees)]

    project_hours = filtered_timesheet.groupby('project_name')['unit_amount'].sum().sort_values(ascending=False)

    fig_hours = go.Figure(go.Bar(
        x=project_hours.index,
        y=project_hours.values,
        text=project_hours.values.round(2),
        textposition='auto'
    ))

    fig_hours.update_layout(
        title='Total Hours per Project',
        xaxis_title='Project',
        yaxis_title='Hours',
        height=chart_height
    )

    project_tasks = filtered_timesheet.groupby('project_name')['task_id'].nunique().sort_values(ascending=False)

    fig_tasks = go.Figure(go.Bar(
        x=project_tasks.index,
        y=project_tasks.values,
        text=project_tasks.values,
        textposition='auto'
    ))

    fig_tasks.update_layout(
        title='Number of Tasks per Project',
        xaxis_title='Project',
        yaxis_title='Number of Tasks',
        height=400
    )

    return {
        "hours_chart": fig_hours.to_dict(),
        "tasks_chart": fig_tasks.to_dict()
    }
