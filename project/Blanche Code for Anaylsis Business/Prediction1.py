from flask import Flask, render_template, request, redirect, url_for
import os
from utlis.data_processor import DataProcessor
from utlis.predictor import ServicePredictor
import ploty.express as px
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'csv'}

def allowed_file(filename):
    return '' in filename and \
        filename.rsplit('.',1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET'])
def home():
    return render_template('upload.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    if file.filename = '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        future_years = list(map(int, request.form['years'].split(',')))

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

    processor = DataProcessor()
    clean_data = processor.process(filepath)

    predictor = ServicePredictor()
    predictor.train(clean_data)
    results = predictor.predict(future_years)

    fig = px.line(
        results,
        x = "Year",
        y = "Predicted_INR",
        color = "Service ID",
        title ="Service Revenue"
    )
    graph_json = json.dumps(fig, cls=ploty.utils.PlotyJSONEncoder)

    return render_template(
        'results.html',
        results = results.to_dict('records'),
        graph_json=graph_json,
        years=future_years

        return redirect(request.url)

if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)








from sklearn.linear_model import LinearRegression
import pandas as pd

class ServicePredictor:
    def __init__(self):
        self.models {}
        self.service_info = {}

    def train(self, clean_data):
        for service, group in clean_data.groupby('Service ID'):
            if len(group) >= 2:
                X = group[['Year']]
                Y = group['Total_INR']

                model = LinearRegression
                model.fit(X,Y)

                self.moduels[service] = model
                self.service_info[service] = {
                    'category': group['Category'].iloc[0],
                    'latest_revenue': group['Total_INR'].isloc[-1]

                }

    def predict(self, future_years):

        predictions = []

        for service, model in self.models.items():
            for year in future_years:
                pred_inr = model.predict([[year]])[0]
                predictions.append({
                    'Service ID': service,
                    'Category': self.service_info[service]['category'],
                    'Year':year,
                    'Predicted_INR':round(pred_inr, 2),
                    'Growth_Precent':round(
                        ((pred_inr - self.service_info[service]['latest_revenue']) /
                         self.service_info[service]['latest_revenue'] * 100, 1)

                })

        return pd.DataFrame(predictions)


