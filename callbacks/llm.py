from dash import html
from dash.dependencies import Input, Output, State
from llm_integration import generate_llm_report
from data_management import DataManager
from logging_config import setup_logging

logger = setup_logging()

def register_llm_callback(app, data_manager: DataManager):
    logger.info("Registering callback...")

    @app.callback(
        Output('llm-report-output', 'children'),
        [Input('generate-llm-report', 'n_clicks')],
        [State('model-selection', 'value')],
        prevent_initial_call=True
    )
    def update_llm_report(n_clicks, selected_model):
        if n_clicks > 0 and selected_model and data_manager.data:
            df_projects, df_employees, df_sales, df_financials, df_timesheet, df_tasks = data_manager.data
            report = generate_llm_report(df_projects, df_employees, df_sales, df_financials, df_timesheet, df_tasks, selected_model)
            if report.startswith("Error:"):
                return html.Div([
                    html.H4("Error Generating LLM Report"),
                    html.P(report, style={'color': 'red'})
                ])
            else:
                return html.Div([
                    html.H4(f"LLM Generated Report (Model: {selected_model})"),
                    html.Pre(report, style={'white-space': 'pre-wrap', 'word-break': 'break-word'})
                ])
        return ""
