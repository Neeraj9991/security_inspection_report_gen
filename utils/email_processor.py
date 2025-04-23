import pandas as pd 
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import win32com.client as win32
import pythoncom

class EmailProcessor:
    def __init__(self):
        # Set up Jinja environment
        self.env = Environment(loader=FileSystemLoader('templates'))
        self.template = self.env.get_template('email_template.html')
        
        # Configuration (should be moved to config file in production)
        self.config = {
            'signature': {
                'name': "",
                'position': "",
                'company': "",
                'contact': ""
            },
            'valid_ratings': ['impressive', 'outstanding', 'satisfactory']
        }

    def validate_excel(self, df):
        """Validate the uploaded Excel file structure and content"""
        required_columns = [
            'Date', 'Time', 'Shift', 'Zone', 'Client Name', 'Client Email', 
            'CC Email', 'Site Name', 'Grooming', 'Alertness', 'Post Discipline', 
            'Site Safety', 'Documentation & Equipment', 'Overall Rating', 
            'Suggestion', 'Inspected By'
        ]
        
        # Check for missing columns
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")
        
        # Validate rating values
        rating_columns = ['Grooming', 'Alertness', 'Post Discipline', 
                         'Site Safety', 'Documentation & Equipment', 'Overall Rating']
        
        for col in rating_columns:
            if not df[col].str.lower().isin(self.config['valid_ratings']).all():
                invalid_values = df[~df[col].str.lower().isin(self.config['valid_ratings'])][col].unique()
                raise ValueError(
                    f"Invalid values in {col}: {', '.join(invalid_values)}. "
                    f"Only {', '.join([x.capitalize() for x in self.config['valid_ratings']])} are allowed."
                )

    def group_by_client(self, df):
        """Group and process the data by client email only"""
        df['Formatted_Date'] = df['Date'].apply(
            lambda x: x.strftime('%B %d, %Y') if pd.notna(x) else 'Date not specified'
        )
        df['Formatted_Time'] = df['Time'].apply(
            lambda x: x.strftime('%I:%M %p') if isinstance(x, pd.Timestamp) else str(x)
        )
        
        # Group only by Client Email
        grouped = df.groupby('Client Email')
        
        client_data = []
        for client_email, group in grouped:
            # Get the first non-NA values for these fields (assuming they're consistent per client)
            client_name = group['Client Name'].dropna().iloc[0] if 'Client Name' in group.columns else ''
            cc_email = group['CC Email'].dropna().iloc[0] if 'CC Email' in group.columns else ''
            inspected_by = group['Inspected By'].dropna().iloc[0] if 'Inspected By' in group.columns else ''
            
            sites = []
            for _, row in group.iterrows():
                site_data = {
                    'site_name': row['Site Name'] if pd.notna(row['Site Name']) else 'Unnamed Site',
                    'date': row['Formatted_Date'],
                    'time': row['Formatted_Time'],
                    'shift': row['Shift'] if pd.notna(row['Shift']) else 'Not specified',
                    'zone': row['Zone'] if pd.notna(row['Zone']) else 'Not specified',
                    'grooming': row['Grooming'].capitalize(),
                    'alertness': row['Alertness'].capitalize(),
                    'post_discipline': row['Post Discipline'].capitalize(),
                    'site_safety': row['Site Safety'].capitalize(),
                    'documentation': row['Documentation & Equipment'].capitalize(),
                    'overall_rating': row['Overall Rating'].capitalize(),
                    'suggestions': row['Suggestion'] if pd.notna(row['Suggestion']) else 'No specific recommendations',
                    'inspected_by': row['Inspected By'],
                    'images': []  
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
        """Generate HTML email content with proper context"""
        context = {
            'client_name': client_data['client_name'],
            'report_date': client_data['report_date'],
            'sites': client_data['sites'],
            'inspected_by': client_data['inspected_by'],
            'signature': self.config['signature'],
            'sites_count': client_data['sites_count']
        }
        return self.template.render(**context)
    
    def create_outlook_draft(self, client_data):
        """Create Outlook email draft with error handling and COM management"""
        try:
            pythoncom.CoInitialize()
            outlook = win32.Dispatch('Outlook.Application')
            mail = outlook.CreateItem(0)
            
            html_body = self.generate_email_html(client_data)
            
            # Create informative subject line
            site_names = [site['site_name'] for site in client_data['sites']]
            subject_sites = (
                ', '.join(site_names[:3]) + 
                (f" and {len(site_names)-3} more" if len(site_names) > 3 else '')
            )
            
            mail.Subject = (
                f"Security Inspection Report: {subject_sites} | "
                f"{client_data['report_date']}"
            )
            mail.To = client_data['client_email']
            
            if client_data['cc_email']:
                mail.CC = client_data['cc_email']
            
            mail.HTMLBody = html_body
            mail.Display(True)
            return True
            
        except Exception as e:
            raise Exception(f"Email creation failed: {str(e)}")
        finally:
            pythoncom.CoUninitialize()
    
    def process_excel_file(self, file_path):
        """Main processing method with enhanced error handling"""
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
