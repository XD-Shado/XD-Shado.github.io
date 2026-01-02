# app.py - Complete Service Growth Prediction Web App
from flask import Flask , render_template , request , redirect , url_for
import os
import pandas as pd
import re
from sklearn.linear_model import LinearRegression
import plotly.express as px
import json
from io import StringIO

app = Flask (__name__)
app.config[ 'UPLOAD_FOLDER' ] = 'uploads'
app.config[ 'ALLOWED_EXTENSIONS' ] = {'xlsx' , 'csv'}


# ========================
# Utility Classes
# ========================

class DataProcessor:
    def __init__(self):
        self.currency_rates = {
            '$': 83.5 ,  # USD to INR
            '€': 89.2 ,  # EUR to INR
            '£': 105.3 ,  # GBP to INR
            '₹': 1  # INR
        }

    def _extract_year(self , text):
        """Extracts year from various formats"""
        year_match = re.search (r'(?:19|20)\d{2}' , str (text))
        return int (year_match.group ()) if year_match else None

    def _convert_to_inr(self , value):
        """Converts any currency to INR"""
        if pd.isna (value):
            return None

        # Check for currency symbols
        match = re.search (r'([₹$€£])\s*(\d[\d,.]*)' , str (value))
        if match:
            currency = match.group (1)
            amount = float (match.group (2).replace (',' , ''))
            return amount * self.currency_rates[ currency ]

        # Handle plain numbers
        try:
            return float (str (value).replace (',' , ''))
        except:
            return None

    def process(self , file):
        """Process uploaded file"""
        try:
            if file.filename.endswith ('.xlsx'):
                df = pd.read_excel (file)
            else:
                df = pd.read_csv (file)

            # Clean and transform data
            if 'Year' not in df.columns:
                return None , "Missing 'Year' column"
            if 'Total' not in df.columns:
                return None , "Missing 'Total' column"
            if 'Service ID' not in df.columns:
                return None , "Missing 'Service ID' column"

            df[ 'Year' ] = df[ 'Year' ].apply (self._extract_year)
            df[ 'Total_INR' ] = df[ 'Total' ].apply (self._convert_to_inr)

            # Remove rows with missing critical data
            df = df.dropna (subset=[ 'Year' , 'Total_INR' , 'Service ID' ])

            # Ensure Category column exists
            if 'Category' not in df.columns:
                df[ 'Category' ] = 'General'

            return df[ [ 'Year' , 'Service ID' , 'Category' , 'Total_INR' ] ] , None
        except Exception as e:
            return None , f"Error processing file: {str (e)}"


class ServicePredictor:
    def __init__(self):
        self.models = {}
        self.service_info = {}

    def train(self , clean_data):
        """Train models for each service"""
        self.models = {}
        self.service_info = {}

        for service , group in clean_data.groupby ('Service ID'):
            if len (group) >= 2:  # Need at least 2 data points
                X = group[ [ 'Year' ] ]
                y = group[ 'Total_INR' ]

                model = LinearRegression ()
                model.fit (X , y)

                self.models[ service ] = model
                self.service_info[ service ] = {
                    'category': group[ 'Category' ].iloc[ 0 ] ,
                    'latest_revenue': group[ 'Total_INR' ].iloc[ -1 ]
                }

    def predict(self , future_years):
        """Generate predictions for given years"""
        predictions = [ ]

        for service , model in self.models.items ():
            for year in future_years:
                pred_inr = model.predict ([ [ year ] ])[ 0 ]
                predictions.append ({
                    'Service ID': service ,
                    'Category': self.service_info[ service ][ 'category' ] ,
                    'Year': year ,
                    'Predicted_INR': round (pred_inr , 2) ,
                    'Growth_Percent': round (
                        ((pred_inr - self.service_info[ service ][ 'latest_revenue' ]) /
                         self.service_info[ service ][ 'latest_revenue' ] * 100) , 1)
                })

        return pd.DataFrame (predictions)


# ========================
# Flask Routes
# ========================

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit ('.' , 1)[ 1 ].lower () in app.config[ 'ALLOWED_EXTENSIONS' ]


@app.route ('/' , methods=[ 'GET' ])
def home():
    return render_template_string ('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Service Growth Predictor</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                .container { max-width: 800px; margin: 0 auto; }
                h1 { color: #2c3e50; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input[type="file"], input[type="text"] { width: 100%; padding: 8px; }
                button { background: #3498db; color: white; border: none; padding: 10px 15px; cursor: pointer; }
                button:hover { background: #2980b9; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Service Growth Predictor</h1>
                <form method="POST" action="/analyze" enctype="multipart/form-data">
                    <div class="form-group">
                        <label for="file">Upload Business Data (Excel/CSV):</label>
                        <input type="file" id="file" name="file" required>
                    </div>
                    <div class="form-group">
                        <label for="years">Years to Predict (comma-separated, e.g., 2024,2025,2026):</label>
                        <input type="text" id="years" name="years" value="2024,2025,2026" required>
                    </div>
                    <button type="submit">Analyze</button>
                </form>
            </div>
        </body>
        </html>
    ''')


@app.route ('/analyze' , methods=[ 'POST' ])
def analyze():
    if 'file' not in request.files:
        return redirect (request.url)

    file = request.files[ 'file' ]
    if file.filename == '':
        return redirect (request.url)

    if not allowed_file (file.filename):
        return render_template_string ('''
            <p>Invalid file type. Please upload Excel (.xlsx) or CSV file.</p>
            <a href="/">Try again</a>
        ''')

    try:
        future_years = [ int (y.strip ()) for y in request.form[ 'years' ].split (',') ]
    except:
        return render_template_string ('''
            <p>Invalid years format. Please use comma-separated numbers (e.g., 2024,2025,2026).</p>
            <a href="/">Try again</a>
        ''')

    # Process data
    processor = DataProcessor ()
    clean_data , error = processor.process (file)

    if error:
        return render_template_string (f'''
            <p>{error}</p>
            <a href="/">Try again</a>
        ''')

    # Make predictions
    predictor = ServicePredictor ()
    predictor.train (clean_data)
    results = predictor.predict (future_years)

    # Generate visualization
    fig = px.line (
        results ,
        x="Year" ,
        y="Predicted_INR" ,
        color="Service ID" ,
        title="Service Revenue Projections (INR)" ,
        labels={"Predicted_INR": "Revenue (₹)" , "Year": "Year"}
    )

    # Format results for display
    formatted_results = [ ]
    for service in results[ 'Service ID' ].unique ():
        service_data = results[ results[ 'Service ID' ] == service ]
        formatted_results.append ({
            'Service ID': service ,
            'Category': service_data[ 'Category' ].iloc[ 0 ] ,
            'Projections': {
                year: service_data[ service_data[ 'Year' ] == year ][ 'Predicted_INR' ].iloc[ 0 ]
                for year in future_years
            } ,
            'Growth': service_data[ 'Growth_Percent' ].iloc[ 0 ]
        })

    # Sort by highest growth
    formatted_results.sort (key=lambda x: x[ 'Growth' ] , reverse=True)

    return render_template_string ('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Analysis Results</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                h1 { color: #2c3e50; }
                #graph { height: 500px; margin: 20px 0; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
                tr:hover { background-color: #f5f5f5; }
                .back-link { display: inline-block; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Analysis Results</h1>

                <div id="graph"></div>

                <h2>Top Performing Services</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Service ID</th>
                            <th>Category</th>
                            <th>Growth %</th>
                            {% for year in years %}
                            <th>{{ year }} (₹)</th>
                            {% endfor %}
                        </tr>
                    </thead>
                    <tbody>
                        {% for service in results %}
                        <tr>
                            <td>{{ loop.index }}</td>
                            <td>{{ service['Service ID'] }}</td>
                            <td>{{ service['Category'] }}</td>
                            <td>{{ service['Growth'] }}%</td>
                            {% for year in years %}
                            <td>{{ "{:,.2f}".format(service['Projections'][year]) }}</td>
                            {% endfor %}
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>

                <a href="/" class="back-link">← Analyze Another File</a>
            </div>

            <script>
                var graph = {{ graph_json|safe }};
                Plotly.newPlot('graph', graph.data, graph.layout);
            </script>
        </body>
        </html>
    ''' ,
                                   results=formatted_results ,
                                   years=future_years ,
                                   graph_json=json.dumps (fig , cls=plotly.utils.PlotlyJSONEncoder))


# ========================
# Main Execution
# ========================

if __name__ == '__main__':
    os.makedirs (app.config[ 'UPLOAD_FOLDER' ] , exist_ok=True)
    app.run (debug=True)