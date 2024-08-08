async function updatePortfolio() {
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    const selectedProjects = Array.from(document.getElementById('project-filter').selectedOptions).map(option => option.value);
    const selectedEmployees = Array.from(document.getElementById('employee-filter').selectedOptions).map(option => option.value);
    const chartHeight = document.getElementById('portfolio-hours-height').value || 400;

    const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
        chart_height: chartHeight
    });

    selectedProjects.forEach(project => params.append('selected_projects', project));
    selectedEmployees.forEach(employee => params.append('selected_employees', employee));

    try {
        const response = await fetch(`/api/portfolio?${params.toString()}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch portfolio data');
        }

        const data = await response.json();

        Plotly.newPlot('portfolio-hours-chart', data.hours_chart.data, data.hours_chart.layout);
        Plotly.newPlot('portfolio-tasks-chart', data.tasks_chart.data, data.tasks_chart.layout);
    } catch (error) {
        console.error('Error updating portfolio:', error);
        // Display an error message to the user
    }
}

// Call updatePortfolio when the page loads and when filters change
document.addEventListener('DOMContentLoaded', () => {
    updatePortfolio();
    document.getElementById('start-date').addEventListener('change', updatePortfolio);
    document.getElementById('end-date').addEventListener('change', updatePortfolio);
    document.getElementById('project-filter').addEventListener('change', updatePortfolio);
    document.getElementById('employee-filter').addEventListener('change', updatePortfolio);
    document.getElementById('portfolio-hours-height').addEventListener('change', updatePortfolio);
});