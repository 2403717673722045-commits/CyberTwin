import os
import urllib.request
import zipfile

def download_sms_spam():
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip"
    raw_dir = os.path.join("data", "raw")
    zip_path = os.path.join(raw_dir, "smsspamcollection.zip")
    
    print(f"Downloading SMS Spam Collection from {url}...")
    urllib.request.urlretrieve(url, zip_path)
    
    print("Extracting...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(raw_dir)
        
    print("SMS Spam Dataset downloaded and extracted to data/raw/SMSSpamCollection")

def download_phishing_urls():
    # Using a common Phishing URL dataset from UCI or Mendeley (e.g. Ebbu2017)
    # The UCI one is "Phishing Websites" but it is an ARFF file with pre-extracted features.
    # We want raw URLs if possible, or at least a known CSV.
    # Let's download a widely used dataset of Phishing URLs from a reliable source.
    # A good public one is the 'phishtank' dataset or similar. 
    # For this demonstration, we'll download a curated dataset from a public GitHub repo that holds benchmark datasets.
    url = "https://raw.githubusercontent.com/jakevdp/PythonDataScienceHandbook/master/notebooks/data/spam.csv" # placeholder for sms, wait we already have sms
    
    # We will use a known public Kaggle/GitHub phishing URL dataset (e.g. from a public repo)
    url_dataset = "https://raw.githubusercontent.com/shreyagopal/Phishing-Website-Detection-by-Machine-Learning-Techniques/master/DataFiles/5.urldata.csv"
    raw_dir = os.path.join("data", "raw")
    csv_path = os.path.join(raw_dir, "urldata.csv")
    
    print(f"Downloading Phishing URL dataset from {url_dataset}...")
    urllib.request.urlretrieve(url_dataset, csv_path)
    print("Phishing URL Dataset downloaded to data/raw/urldata.csv")

if __name__ == "__main__":
    download_sms_spam()
    download_phishing_urls()
