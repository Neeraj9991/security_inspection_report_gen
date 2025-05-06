import pandas as pd 
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

class EmailProcessor:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader('templates'))
        self.template = self.env.get_template('email_template.html')

    def validate_excel(self, df):
        """Validate the uploaded Excel file structure only"""
        required_columns = [
            'Date', 'Time', 'Shift', 'Zone', 'Client Name', 'Contact Person', 'Client Email', 'CC Email',
            'Site Name', 'Attendance Register', 'Handling/Taking Over Register', 'Material In / Out Register',
            'Shortage', 'Grooming', 'Alertness', 'Post Discipline', 'Site Safety',
            'Mobiles (Shift Cell)', 'HHMD', 'Torch', 'Batten', 'Other Security Equipments',
            'Overall Rating', 'Observation', 'Inspected By'
        ]

        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

    def group_by_client(self, df):
        """Group and process the data by client email"""
        df['Formatted_Date'] = df['Date'].apply(
            lambda x: x.strftime('%B %d, %Y') if pd.notna(x) else 'Date not specified'
        )
        df['Formatted_Time'] = pd.to_datetime(df['Time'], errors='coerce').dt.strftime('%B %d, %Y at %I:%M %p')

        grouped = df.groupby('Client Email')

        client_data = []
        for client_email, group in grouped:
            client_name = group['Client Name'].dropna().iloc[0] if not group['Client Name'].dropna().empty else 'Unknown Client'
            cc_email = group['CC Email'].dropna().iloc[0] if 'CC Email' in group.columns else ''
            inspected_by = group['Inspected By'].dropna().iloc[0] if 'Inspected By' in group.columns else ''

            sites = []
            for _, row in group.iterrows():
                site_data = {
                    'site_name': row['Site Name'],
                    'date': row['Formatted_Date'],
                    'time': row['Formatted_Time'],
                    'shift': row['Shift'],
                    'zone': row['Zone'],
                    'contact_person': row['Contact Person'],
                    'attendance_register': row['Attendance Register'],
                    'handling_register': row['Handling/Taking Over Register'],
                    'material_register': row['Material In / Out Register'],
                    'shortage': row['Shortage'],
                    'grooming': row['Grooming'],
                    'alertness': row['Alertness'],
                    'post_discipline': row['Post Discipline'],
                    'site_safety': row['Site Safety'],
                    'mobiles_shift_cell': row['Mobiles (Shift Cell)'],
                    'hhmd': row['HHMD'],
                    'torch': row['Torch'],
                    'batten': row['Batten'],
                    'other_security_equipments': row['Other Security Equipments'],
                    'overall_rating': row['Overall Rating'],
                    'observation': row['Observation'],
                    'inspected_by': row['Inspected By'],
                    'images': []  # to be populated later
                }
                sites.append(site_data)

            valid_dates = [d for d in group['Date'] if pd.notna(d)]
            report_date = (
                max(valid_dates).strftime('%B %d, %Y') 
                if valid_dates 
                else 'Date not available'
            )

            client_data.append({
                'client_email': client_email,
                'client_name': client_name,
                'cc_email': cc_email if pd.notna(cc_email) else '',
                'inspected_by': inspected_by,
                'report_date': report_date,
                'sites': sites,
                'sites_count': len(sites)
            })

        return client_data

    def generate_email_html(self, client_data):
        """Generate email HTML"""
        context = {
            'client_name': client_data['client_name'],
            'report_date': client_data['report_date'],
            'sites': client_data['sites'],
            'inspected_by': client_data['inspected_by'],
            'sites_count': client_data['sites_count']
        }
        return self.template.render(**context)

    def process_excel_file(self, file_path):
        """Main processing"""
        try:
            df = pd.read_excel(
                file_path,
                parse_dates=['Date', 'Time'],
                dtype={'Shift': str, 'Zone': str}
            )
            self.validate_excel(df)
            return self.group_by_client(df)
        except Exception as e:
            raise Exception(f"Failed to process file: {str(e)}")
