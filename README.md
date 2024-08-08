# Oodash

Oodash is a dashboard application for visualizing and analyzing Odoo data. It provides various charts and analytics tools to help you gain insights from your Odoo instance.

**Note: This project is currently in beta and has not been extensively tested. Use with caution in production environments.**

## Requirements

- Python 3.12.4 (tested version)
- Odoo instance with API access

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/oodash.git
   cd oodash
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your Odoo credentials:
   ```
   ODOO_URL=https://your-odoo-instance.com
   ODOO_DB=your_database_name
   ODOO_USERNAME=your_username
   ODOO_API_KEY=your_api_key
   JWT_SECRET_KEY=encryption_key
   JWT_ALGORITHM=algorithm choice
   TIMEZONE=your_timezone

   LOGIN_URL=login_url

   # url and port
   SERVICE_URL=url_to_start_the_service
   SERVICE_PORT=port_to_start_the_service
   ```

5. Run the application:
   ```
   python oodash.py
   ```

6. Open a web browser and navigate to `http://SERVICE_PORT:SERVICE_URL` to access the dashboard.

## Important Notes

### Personally Identifiable Information (PII)
This application interacts with Odoo data, which may include personally identifiable information. Users are responsible for ensuring compliance with relevant data protection regulations when using this application. Implement appropriate access controls and data handling procedures to protect sensitive information.

### Debug Mode
By default, the application runs with debug mode set to `True`. This can potentially expose sensitive information through detailed error messages. For production use, make sure to set `debug=False` in the `oodash.py` file.

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3). See the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is provided "as is", without warranty of any kind. Use at your own risk.