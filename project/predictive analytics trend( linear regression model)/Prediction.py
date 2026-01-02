from flask import Flask , render_template_string , request , redirect
import os
import pandas as pd
import re
from sklearn.linear_model import LinearRegression
import plotly.express as px
import json
import plotly
from werkzeug.utils import secure_filename
import warnings
import numpy as np
import requests

app = Flask (__name__)
app.config[ 'UPLOAD_FOLDER' ] = 'uploads'
app.config[ 'ALLOWED_EXTENSIONS' ] = {'xlsx' , 'csv'}
app.config[ 'YEAR_API_ENDPOINT' ] = None  # Set your API endpoint if available

# Suppress sklearn warnings
warnings.filterwarnings ("ignore" , category=UserWarning , message="X does not have valid feature names")


class DataProcessor:
    def __init__(self):
        self.currency_rates = {
            '$': 83.5 ,  # USD to INR
            '€': 89.2 ,  # EUR to INR
            '£': 105.3 ,  # GBP to INR
            '₹': 1  # INR
        }

    def _convert_to_inr(self , value):
        if pd.isna (value):
            return None

        match = re.search (r'([₹$€£])\s*(\d[\d,.]*)' , str (value))
        if match:
            currency = match.group (1)
            amount = float (match.group (2).replace (',' , ''))
            return amount * self.currency_rates[ currency ]

        try:
            return float (str (value).replace (',' , ''))
        except:
            return None

    def _fetch_year_from_api(self , filename):
        """Fetch year from API if available"""
        if not app.config[ 'YEAR_API_ENDPOINT' ]:
            return None

        try:
            response = requests.get (
                app.config[ 'YEAR_API_ENDPOINT' ] ,
                params={'filename': secure_filename (filename)} ,
                timeout=3
            )
            if response.status_code == 200:
                data = response.json ()
                return data.get ('year')
        except Exception as e:
            print (f"API Error: {str (e)}")
        return None

    def process(self , file , year_info=None):
        try:
            # Read file
            if file.filename.endswith ('.xlsx'):
                df = pd.read_excel (file)
            else:
                df = pd.read_csv (file)

            # Debug: Print raw data
            print (f"\n=== Raw Data from {file.filename} ===")
            print (df.head ())

            # Check required columns
            if 'Total' not in df.columns:
                return None , "Missing 'Total' column"
            if 'Service ID' not in df.columns:
                return None , "Missing 'Service ID' column"

            # Handle Year column
            year_source = "file"
            if 'Year' in df.columns:
                df[ 'Year' ] = pd.to_numeric (df[ 'Year' ] , errors='coerce')
                if df[ 'Year' ].isna ().all ():
                    year_source = None
            else:
                year_source = None

            # If no valid years in file, try other sources
            if year_source is None:
                if year_info:  # From form input
                    if '-' in year_info:  # Year range
                        try:
                            start_year , end_year = map (int , year_info.split ('-'))
                            df[ 'Year' ] = [ start_year + (i % (end_year - start_year + 1))
                                             for i in range (len (df)) ]
                            year_source = "form (range)"
                        except:
                            return None , "Invalid year range format (use YYYY-YYYY)"
                    else:  # Single year
                        try:
                            df[ 'Year' ] = int (year_info)
                            year_source = "form (single)"
                        except:
                            return None , "Invalid year format (use YYYY)"
                else:  # Try API
                    api_year = self._fetch_year_from_api (file.filename)
                    if api_year:
                        try:
                            df[ 'Year' ] = int (api_year)
                            year_source = "API"
                        except:
                            return None , "Invalid year from API"

            # Final fallback if no year source
            if year_source is None:
                return None , "Could not determine year(s). Please specify in form."

            print (f"Year source for {file.filename}: {year_source}")

            # Process currency and clean data
            df[ 'Total_INR' ] = df[ 'Total' ].apply (self._convert_to_inr)
            df = df.dropna (subset=[ 'Year' , 'Total_INR' , 'Service ID' ])

            # Debug: Print cleaned data
            print ("\n=== Cleaned Data ===")
            print (df.head ())

            # Ensure Category exists
            if 'Category' not in df.columns:
                df[ 'Category' ] = 'General'

            return df[ [ 'Year' , 'Service ID' , 'Category' , 'Total_INR' ] ] , None

        except Exception as e:
            print (f"Processing error: {str (e)}")
            return None , f"Error processing {file.filename}: {str (e)}"


class ServicePredictor:
    def __init__(self):
        self.models = {}
        self.service_info = {}

    def train(self , clean_data):
        self.models = {}
        self.service_info = {}

        # Debug: Print training data stats
        print ("\n=== Training Data Stats ===")
        print (f"Total services: {clean_data[ 'Service ID' ].nunique ()}")
        print (f"Year range: {clean_data[ 'Year' ].min ()} to {clean_data[ 'Year' ].max ()}")
        print (f"Records per service:\n{clean_data[ 'Service ID' ].value_counts ()}")

        for service , group in clean_data.groupby ('Service ID'):
            if len (group) >= 2:  # Need at least 2 data points for linear regression
                X = group[ [ 'Year' ] ].values.reshape (-1 , 1)
                y = group[ 'Total_INR' ].values
                model = LinearRegression ()
                model.fit (X , y)
                self.models[ service ] = model
                self.service_info[ service ] = {
                    'category': group[ 'Category' ].iloc[ 0 ] ,
                    'latest_revenue': group[ 'Total_INR' ].iloc[ -1 ]
                }

        # Debug: Print training results
        print ("\n=== Training Results ===")
        print (f"Models trained: {len (self.models)}")
        if self.models:
            first_service = next (iter (self.models.keys ()))
            print (f"Example model for {first_service}:")
            print (f"Coefficient: {self.models[ first_service ].coef_[ 0 ]}")
            print (f"Intercept: {self.models[ first_service ].intercept_}")

    def predict(self , future_years):
        predictions = [ ]
        for service , model in self.models.items ():
            for year in future_years:
                pred_inr = max (0 , model.predict ([ [ year ] ])[ 0 ])  # Ensure non-negative
                latest_revenue = self.service_info[ service ][ 'latest_revenue' ]

                if latest_revenue == 0:
                    growth_percent = 0
                else:
                    growth_percent = ((pred_inr - latest_revenue) / latest_revenue) * 100

                predictions.append ({
                    'Service ID': service ,
                    'Category': self.service_info[ service ][ 'category' ] ,
                    'Year': year ,
                    'Predicted_INR': round (pred_inr , 2) ,
                    'Growth_Percent': round (growth_percent , 1)
                })

        # Debug: Print prediction sample
        if predictions:
            print ("\n=== Prediction Sample ===")
            print (predictions[ :2 ])  # Print first two predictions

        return pd.DataFrame (predictions)


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
                input[type="file"], input[type="text"] { 
                    width: 100%; padding: 8px; margin-bottom: 10px; 
                }
                button { background: #3498db; color: white; border: none; padding: 10px 15px; cursor: pointer; }
                button:hover { background: #2980b9; }
                .file-year-group { display: flex; margin-bottom: 10px; }
                .file-input { flex: 2; margin-right: 10px; }
                .year-input { flex: 1; }
                .add-file-btn { margin-bottom: 15px; }
                .predict-years { margin-top: 15px; }
                .year-note { 
                    font-size: 0.9em; 
                    color: #666; 
                    margin-top: 5px;
                }
                .error-message {
                    color: #dc3545;
                    padding: 10px;
                    margin: 10px 0;
                    border: 1px solid #dc3545;
                    border-radius: 4px;
                }
            </style>
            <script>
                let fileCounter = 0;

                function addFileInput() {
                    fileCounter++;
                    const container = document.getElementById('file-inputs');
                    const div = document.createElement('div');
                    div.className = 'file-year-group';
                    div.innerHTML = `
                        <div class="file-input">
                            <input type="file" name="file_${fileCounter}" required>
                        </div>
                        <div class="year-input">
                            <input type="text" name="year_${fileCounter}" 
                                   placeholder="YYYY or YYYY-YYYY">
                            <div class="year-note">Required if file doesn't contain year data</div>
                        </div>
                    `;
                    container.appendChild(div);
                }
            </script>
        </head>
        <body>
            <div class="container">
                <h1>Service Growth Predictor</h1>
                <form method="POST" action="/analyze" enctype="multipart/form-data">
                    <div class="form-group">
                        <label>Upload Business Data Files:</label>
                        <div id="file-inputs">
                            <div class="file-year-group">
                                <div class="file-input">
                                    <input type="file" name="file_0" required>
                                </div>
                                <div class="year-input">
                                    <input type="text" name="year_0" 
                                           placeholder="YYYY or YYYY-YYYY">
                                    <div class="year-note">Required if file doesn't contain year data</div>
                                </div>
                            </div>
                        </div>
                        <button type="button" onclick="addFileInput()" class="add-file-btn">
                            + Add Another File
                        </button>
                    </div>
                    <div class="form-group predict-years">
                        <label for="years">Years to Predict (comma-separated):</label>
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
    # Get all uploaded files with their corresponding year info
    file_data = [ ]
    i = 0
    while f'file_{i}' in request.files:
        file = request.files[ f'file_{i}' ]
        year_info = request.form.get (f'year_{i}' , '').strip ()
        if file.filename != '' and allowed_file (file.filename):
            file_data.append ((file , year_info if year_info else None))
        i += 1

    if not file_data:
        return redirect (request.url)

    try:
        future_years = [ int (y.strip ()) for y in request.form[ 'years' ].split (',') ]
    except:
        return render_template_string ('''
            <p class="error-message">Invalid prediction years format. Please use comma-separated numbers (e.g., 2024,2025,2026).</p>
            <a href="/">Try again</a>
        ''')

    # Process all files
    all_data = [ ]
    processor = DataProcessor ()

    for file , year_info in file_data:
        clean_data , error = processor.process (file , year_info)
        if error:
            return render_template_string (f'''
                <div class="container">
                    <h1>Error</h1>
                    <p class="error-message">{error}</p>
                    <a href="/" class="back-link">← Try again</a>
                </div>
            ''')
        all_data.append (clean_data)

    # Combine all data
    combined_data = pd.concat (all_data , ignore_index=True)

    # Debug: Print combined data stats
    print ("\n=== Combined Data ===")
    print ("Number of services:" , combined_data[ 'Service ID' ].nunique ())
    print ("Years available:" , combined_data[ 'Year' ].unique ())
    print ("Records per service:\n" , combined_data[ 'Service ID' ].value_counts ())

    # Train model and predict
    predictor = ServicePredictor ()
    predictor.train (combined_data)
    results = predictor.predict (future_years)

    if results.empty:
        return render_template_string ('''
            <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
                <h1>Analysis Results</h1>
                <p class="error-message">
                    No predictions could be generated. This usually happens when:
                </p>
                <ul>
                    <li>Your data doesn't have at least 2 years of history per service</li>
                    <li>The 'Total' column contains non-numeric values</li>
                    <li>There are missing values in critical columns</li>
                </ul>
                <p>Please check your input files and try again.</p>
                <a href="/" style="display: inline-block; margin-top: 20px;">← Back to Upload</a>
            </div>
        ''')

    # Create visualization
    try:
        fig = px.line (
            results ,
            x="Year" ,
            y="Predicted_INR" ,
            color="Service ID" ,
            title="Service Revenue Projections (INR)" ,
            labels={"Predicted_INR": "Revenue (₹)" , "Year": "Year"} ,
            template="plotly_white" ,
            markers=True
        )

        fig.update_layout (
            hovermode="x unified" ,
            xaxis=dict (tickmode='linear' , dtick=1) ,
            yaxis=dict (tickprefix="₹" , tickformat=",.0f") ,
            plot_bgcolor='rgba(240,240,240,0.8)'
        )

        # Debug: Print graph data
        print ("\n=== Graph Data ===")
        print ("Number of traces:" , len (fig.data))
        print ("X values sample:" , fig.data[ 0 ].x[ :5 ] if fig.data else "No data")
        print ("Y values sample:" , fig.data[ 0 ].y[ :5 ] if fig.data else "No data")

    except Exception as e:
        print (f"Graph creation error: {str (e)}")
        return render_template_string ('''
            <div class="container">
                <h1>Error</h1>
                <p class="error-message">Failed to create visualization: {str(e)}</p>
                <a href="/" class="back-link">← Try again</a>
            </div>
        ''')

    # Format results for display
    formatted_results = [ ]
    for service in results[ 'Service ID' ].unique ():
        service_data = results[ results[ 'Service ID' ] == service ]
        formatted_results.append ({
            'Service_ID': service ,
            'Category': service_data[ 'Category' ].iloc[ 0 ] ,
            'Projections': {
                year: service_data[ service_data[ 'Year' ] == year ][ 'Predicted_INR' ].iloc[ 0 ]
                for year in future_years
            } ,
            'Growth': service_data[ 'Growth_Percent' ].iloc[ 0 ]
        })

    formatted_results.sort (key=lambda x: x[ 'Growth' ] , reverse=True)

    return render_template_string ('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Analysis Results</title>
            <script src="https://cdn.plot.ly/plotly-2.14.0.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                h1 { color: #2c3e50; }
                #graph { 
                    height: 500px; 
                    margin: 20px 0;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; position: sticky; top: 0; }
                tr:hover { background-color: #f5f5f5; }
                .positive-growth { color: #28a745; font-weight: bold; }
                .negative-growth { color: #dc3545; font-weight: bold; }
                .back-link { 
                    display: inline-block; 
                    margin-top: 20px; 
                    padding: 10px 15px;
                    background: #3498db;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                }
                .back-link:hover { background: #2980b9; }
                .data-warning { 
                    background: #fff3cd; 
                    padding: 15px; 
                    border-radius: 4px;
                    border-left: 4px solid #ffc107;
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Analysis Results</h1>
                <div id="graph">
                    <script>
                        try {
                            var graph = {{ graph_json|safe }};
                            if(graph.data && graph.data.length > 0) {
                                Plotly.newPlot('graph', graph.data, graph.layout)
                                    .catch(err => {
                                        document.getElementById('graph').innerHTML = 
                                            '<div class="data-warning">Graph Error: ' + err.message + '</div>';
                                        console.error('Plotly error:', err);
                                    });
                            } else {
                                document.getElementById('graph').innerHTML = 
                                    '<div class="data-warning">No data available for visualization</div>';
                                console.warn('Empty graph data:', graph);
                            }
                        } catch (e) {
                            document.getElementById('graph').innerHTML = 
                                '<div class="data-warning">Rendering Error: ' + e.message + '</div>';
                            console.error('Rendering error:', e);
                        }
                    </script>
                </div>
                <h2>Service Performance Summary</h2>
                <div style="overflow-x: auto;">
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
                                <td>{{ service.Service_ID }}</td>
                                <td>{{ service.Category }}</td>
                                <td class="{% if service.Growth >= 0 %}positive-growth{% else %}negative-growth{% endif %}">
                                    {{ service.Growth }}%
                                </td>
                                {% for year in years %}
                                <td>{{ "{:,.2f}".format(service.Projections[year]) }}</td>
                                {% endfor %}
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                <a href="/" class="back-link">← Analyze Another File</a>
            </div>
        </body>
        </html>
    ''' ,
                                   results=formatted_results ,
                                   years=future_years ,
                                   graph_json=json.dumps (fig , cls=plotly.utils.PlotlyJSONEncoder)
                                   )


if __name__ == '__main__':
    os.makedirs (app.config[ 'UPLOAD_FOLDER' ] , exist_ok=True)
    app.run (debug=True)