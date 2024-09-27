import requests
from bs4 import BeautifulSoup
import pymongo
from pymongo import MongoClient
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client['cloud_compute_db']

def fetch_aws_instance_data():
    url = 'https://aws.amazon.com/ec2/instance-types/'
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to retrieve AWS data")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    instance_data = []
    table = soup.find('class', {'id': 'lb-tbl lb-tbl-p'})
    rows = table.find_all('tr')[1:]

    for row in rows:
        cols = row.find_all('tr')
        instance_data.append({
            "Instance Type": cols[0].text.strip(),
            "vCPUs": int(cols[1].text.strip()),
            "Memory (GB)": int(cols[2].text.strip()),
            "Price (USD/hour)": float(cols[3].text.strip().replace('$', '').replace(',', '')),
            "Region": cols[4].text.strip(),
            "Provider": "AWS"
        })

    return instance_data

def fetch_azure_instance_data():
    url = 'https://azure.microsoft.com/en-us/pricing/details/virtual-machines/windows/#pricing'
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to retrieve Azure data")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    instance_data = []
    table = soup.find('class', {'id': 'data-table__table data-table__table--pricing'})
    rows = table.find_all('tr')[1:]

    for row in rows:
        cols = row.find_all('tr')
        instance_data.append({
            "Instance Type": cols[0].text.strip(),
            "vCPUs": int(cols[1].text.strip()),
            "Memory (GB)": int(cols[2].text.strip()),
            "Price (USD/hour)": float(cols[3].text.strip().replace('$', '').replace(',', '')),
            "Region": cols[4].text.strip(),
            "Provider": "Azure"
        })

    return instance_data

def fetch_gcp_instance_data():
    url = 'https://cloud.google.com/compute/all-pricing'
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to retrieve GCP data")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    instance_data = []
    table = soup.find('table', {'id': 'table-content'})
    rows = table.find_all('tr')[1:]

    for row in rows:
        cols = row.find_all('td')
        instance_data.append({
            "Instance Type": cols[0].text.strip(),
            "vCPUs": int(cols[1].text.strip()),
            "Memory (GB)": int(cols[2].text.strip()),
            "Price (USD/hour)": float(cols[3].text.strip().replace('$', '').replace(',', '')),
            "Region": cols[4].text.strip(),
            "Provider": "GCP",
        })

    return instance_data

def fetch_oracle_instance_data():
    url = 'https://www.oracle.com/in/cloud/price-list/'
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to retrieve Oracle data")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    instance_data = []
    table = soup.find('table', {'id': 'rc34w5 rw-neutral-00bg'})
    rows = table.find_all('tr')[1:]

    for row in rows:
        cols = row.find_all('td')
        instance_data.append({
            "Instance Type": cols[0].text.strip(),
            "vCPUs": int(cols[1].text.strip()),
            "Memory (GB)": int(cols[2].text.strip()),
            "Price (USD/hour)": float(cols[3].text.strip().replace('$', '').replace(',', '')),
            "Region": cols[4].text.strip(),
            "Provider": "Oracle"
        })

    return instance_data

def fetch_alibaba_instance_data():
    url = 'https://www.alibabacloud.com/en/product/ecs?_p_lc=1&spm=a3c0i.7938564.8215766810.1.184e441eD8JpjB'
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to retrieve Alibaba data")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    instance_data = []
    table = soup.find('table', {'id': 'table___1YneY'})
    rows = table.find_all('tr')[1:]

    for row in rows:
        cols = row.find_all('td')
        instance_data.append({
            "Instance Type": cols[0].text.strip(),
            "vCPUs": int(cols[1].text.strip()),
            "Memory (GB)": int(cols[2].text.strip()),
            "Price (USD/hour)": float(cols[3].text.strip().replace('$', '').replace(',', '')),
            "Region": cols[4].text.strip(),
            "Provider": "Alibaba"
        })

    return instance_data

def fetch_ibm_instance_data():
    url = 'https://cloud.ibm.com/infrastructure/provision/vs?catalog_query=aHR0cHM6Ly9jbG91ZC5pYm0uY29tL2NhdGFsb2c%2FY2F0ZWdvcnk9Y29tcHV0ZQ%3D%3D'
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to retrieve IBM data")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    instance_data = []
    table = soup.find('table', {'id': 'cds--data-table-content'})
    rows = table.find_all('tr')[1:]

    for row in rows:
        cols = row.find_all('td')
        instance_data.append({
            "Instance Type": cols[0].text.strip(),
            "vCPUs": int(cols[1].text.strip()),
            "Memory (GB)": int(cols[2].text.strip()),
            "Price (USD/hour)": float(cols[3].text.strip().replace('$', '').replace(',', '')),
            "Region": cols[4].text.strip(),
            "Provider": "IBM",
            "Scraped At": datetime.now()
        })

    return instance_data

def store_instance_data(data, collection_name):
    collection = db[collection_name]
    collection.insert_many(data)

if __name__ == '__main__':
    all_instance_data = []
    all_instance_data.extend(fetch_aws_instance_data())
    all_instance_data.extend(fetch_azure_instance_data())
    all_instance_data.extend(fetch_gcp_instance_data())
    all_instance_data.extend(fetch_oracle_instance_data())
    all_instance_data.extend(fetch_alibaba_instance_data())
    all_instance_data.extend(fetch_ibm_instance_data())

    if all_instance_data:
        store_instance_data(all_instance_data, 'all_instances')
        print("Data successfully scraped and stored in MongoDB.")
    else:
        print("No data to store.")
