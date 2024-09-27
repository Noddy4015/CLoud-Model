from flask import Flask, request, render_template
import pandas as pd
from numpy import array
from numpy.linalg import eig
from numpy import linalg as LA
from pymongo import MongoClient

app = Flask(__name__)
client = MongoClient('localhost', 27017)
db = client['cloud_compute_db']

def load_data_from_mongodb(collection_name):
    data = list(db[collection_name].find())
    df = pd.DataFrame(data)
    required_columns = ['Instance Type', 'vCPUs', 'Memory (GB)', 'Price (USD/hour)', 'Performance Details', 'Security Features', 'Region']
    for column in required_columns:
        if column not in df.columns:
            df[column] = None
    print(f"Loaded data from {collection_name} with columns: {df.columns.tolist()}")
    return df


gcp_df = load_data_from_mongodb('gcp_instances')
aws_df = load_data_from_mongodb('aws_instances')
azure_df = load_data_from_mongodb('azure_instances')
oracle_df = load_data_from_mongodb('oracle_instances')
alibaba_df = load_data_from_mongodb('alibaba_instances')
ibm_df = load_data_from_mongodb('ibm_instances')

def normalize_data(df):
    if 'vCPUs' not in df.columns or df['vCPUs'].isnull().all():
        df['Normalized_vCPUs'] = 0
    else:
        df['Normalized_vCPUs'] = df['vCPUs'] / df['vCPUs'].max()

    if 'Memory (GB)' not in df.columns or df['Memory (GB)'].isnull().all():
        df['Normalized_Memory'] = 0
    else:
        df['Normalized_Memory'] = df['Memory (GB)'] / df['Memory (GB)'].max()

    if 'Price (USD/hour)' not in df.columns or df['Price (USD/hour)'].isnull().all():
        df['Normalized_Price'] = 0
    else:
        df['Normalized_Price'] = 1 / df['Price (USD/hour)']

    df['Normalized_Performance'] = df['Performance Details'].map({
        'Low performance': 1,
        'Moderate performance': 2,
        'High performance': 3,
        'Very high performance': 4
    }).fillna(0)

    df['Normalized_Security'] = df['Security Features'].map({
        'Basic security features': 1,
        'Advanced security features': 2,
        'High security': 3
    }).fillna(0)
    
    return df


def get_matching_instances(cpu_required, memory_required, region):
    if region == 'all':
        filtered_gcp = gcp_df[(gcp_df['vCPUs'] == cpu_required) & (gcp_df['Memory (GB)'] == memory_required)]
        filtered_aws = aws_df[(aws_df['vCPUs'] == cpu_required) & (aws_df['Memory (GB)'] == memory_required)]
        filtered_azure = azure_df[(azure_df['vCPUs'] == cpu_required) & (azure_df['Memory (GB)'] == memory_required)]
        filtered_oracle = oracle_df[(oracle_df['vCPUs'] == cpu_required) & (oracle_df['Memory (GB)'] == memory_required)]
        filtered_alibaba = alibaba_df[(alibaba_df['vCPUs'] == cpu_required) & (alibaba_df['Memory (GB)'] == memory_required)]
        filtered_ibm = ibm_df[(ibm_df['vCPUs'] == cpu_required) & (ibm_df['Memory (GB)'] == memory_required)]
    else:
        filtered_gcp = gcp_df[(gcp_df['vCPUs'] == cpu_required) & (gcp_df['Memory (GB)'] == memory_required) & (gcp_df['Region'] == region)]
        filtered_aws = aws_df[(aws_df['vCPUs'] == cpu_required) & (aws_df['Memory (GB)'] == memory_required) & (aws_df['Region'] == region)]
        filtered_azure = azure_df[(azure_df['vCPUs'] == cpu_required) & (azure_df['Memory (GB)'] == memory_required) & (azure_df['Region'] == region)]
        filtered_oracle = oracle_df[(oracle_df['vCPUs'] == cpu_required) & (oracle_df['Memory (GB)'] == memory_required) & (oracle_df['Region'] == region)]
        filtered_alibaba = alibaba_df[(alibaba_df['vCPUs'] == cpu_required) & (alibaba_df['Memory (GB)'] == memory_required) & (alibaba_df['Region'] == region)]
        filtered_ibm = ibm_df[(ibm_df['vCPUs'] == cpu_required) & (ibm_df['Memory (GB)'] == memory_required) & (ibm_df['Region'] == region)]
    
    filtered_gcp = filtered_gcp.assign(Provider='GCP')
    filtered_aws = filtered_aws.assign(Provider='AWS')
    filtered_azure = filtered_azure.assign(Provider='Azure')
    filtered_oracle = filtered_oracle.assign(Provider='Oracle')
    filtered_alibaba = filtered_alibaba.assign(Provider='Alibaba')
    filtered_ibm = filtered_ibm.assign(Provider='IBM')

    all_filtered = pd.concat([filtered_gcp, filtered_aws, filtered_azure, filtered_oracle, filtered_alibaba, filtered_ibm])
    
    if all_filtered.empty:
        return pd.DataFrame()
    
    all_filtered = all_filtered.fillna({'Instance Type': 'Unknown', 'vCPUs': 0, 'Memory (GB)': 0, 'Price (USD/hour)': 0})
    return all_filtered[['Provider', 'Instance Type', 'Region', 'vCPUs', 'Memory (GB)', 'Price (USD/hour)', 'Performance Details', 'Security Features']]

def wsm_recommend_instance(cpu_required, memory_required, region, weights):
    matching_instances = get_matching_instances(cpu_required, memory_required, region)
    matching_instances = normalize_data(matching_instances)
    matching_instances['Score'] = (weights['Price'] * matching_instances['Normalized_Price'])
    recommended = matching_instances.sort_values(by='Score', ascending=False)
    return recommended[['Provider', 'Instance Type', 'Region', 'vCPUs', 'Memory (GB)', 'Price (USD/hour)', 'Score']]

def ahp_weights(criteria_comparisons):
    matrix = array(criteria_comparisons)
    eigvals, eigvecs = eig(matrix)
    weights = eigvecs[:, eigvals.argmax()]
    weights = weights / weights.sum()
    return weights

def ahp_recommend_instance(cpu_required, memory_required, region):
    matching_instances = get_matching_instances(cpu_required, memory_required, region)
    matching_instances = normalize_data(matching_instances)
    criteria_comparisons = [[1, 2, 1], [0.5, 1, 0.5], [1, 2, 1]]
    weights = ahp_weights(criteria_comparisons)
    matching_instances['Score'] = (weights[0] * matching_instances['Normalized_Performance'] +
                                   weights[1] * matching_instances['Normalized_Memory'] +
                                   weights[2] * matching_instances['Normalized_Price'])
    recommended = matching_instances.sort_values(by='Score', ascending=False)
    return recommended[['Provider', 'Instance Type', 'Region', 'vCPUs', 'Memory (GB)', 'Price (USD/hour)', 'Performance Details', 'Score']]

def topsis_recommend_instance(cpu_required, memory_required, region):
    matching_instances = get_matching_instances(cpu_required, memory_required, region)
    matching_instances = normalize_data(matching_instances)
    decision_matrix = matching_instances[['Normalized_Security', 'Normalized_Memory', 'Normalized_Price']].values
    norm_decision_matrix = decision_matrix / LA.norm(decision_matrix, axis=0)
    weights = [0.4, 0.4, 0.2]
    weighted_matrix = norm_decision_matrix * weights
    ideal_solution = weighted_matrix.max(axis=0)
    negative_ideal_solution = weighted_matrix.min(axis=0)
    distance_to_ideal = LA.norm(weighted_matrix - ideal_solution, axis=1)
    distance_to_negative_ideal = LA.norm(weighted_matrix - negative_ideal_solution, axis=1)
    scores = distance_to_negative_ideal / (distance_to_ideal + distance_to_negative_ideal)
    matching_instances['Score'] = scores
    recommended = matching_instances.sort_values(by='Score', ascending=False)
    return recommended[['Provider', 'Instance Type', 'Region', 'vCPUs', 'Memory (GB)', 'Price (USD/hour)', 'Security Features', 'Score']]

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        try:
            cpu = int(request.form["cpu"])
            memory = float(request.form["memory"])
            region = request.form["region"]
        
            wsm_weights = {"Price": 1}
            wsm_results = wsm_recommend_instance(cpu, memory, region, wsm_weights)
            ahp_results = ahp_recommend_instance(cpu, memory, region)
            topsis_results = topsis_recommend_instance(cpu, memory, region)
        
            if wsm_results.empty and ahp_results.empty and topsis_results.empty:
                return render_template("results.html", message="No data available for the given inputs.")
        
            wsm_results_html = wsm_results.to_html(classes='table table-striped')
            ahp_results_html = ahp_results.to_html(classes='table table-striped')
            topsis_results_html = topsis_results.to_html(classes='table table-striped')

            return render_template("results.html", wsm_results=wsm_results_html, ahp_results=ahp_results_html, topsis_results=topsis_results_html)
        
        except KeyError as e:
            return render_template("results.html", message="Please put relevant vCPU and Memory value")
        except Exception as e:
            return render_template("results.html", message=f"An error occurred: {str(e)}")
    
    return render_template("index.html")



if __name__ == "__main__":
    app.run(debug=True)
