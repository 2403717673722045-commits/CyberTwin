import re
import numpy as np
from urllib.parse import urlparse

def extract_url_features(urls):
    features = []
    for u in urls:
        u = str(u)
        if not re.match(r"^https?://", u, re.IGNORECASE):
            u = "http://" + u
            
        parsed = urlparse(u)
        host = (parsed.hostname or "").lower()
        path = parsed.path or ""
        
        # Features
        # Clean host
        if host.startswith("www."):
            host = host[4:]
            
        # Features based ONLY on host, since the training dataset lacks paths and schemes
        host_len = len(host)
        num_dots = host.count('.')
        num_hyphens = host.count('-')
        num_digits = sum(c.isdigit() for c in host)
        num_special = sum(not c.isalnum() for c in host)
        has_at = 1 if '@' in u else 0
        is_ip = 1 if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host) else 0
        
        # Note: removing has_https, path_len, and full URL length because the training dataset 
        # (urldata.csv) contains ONLY domain names, meaning these features are completely 
        # missing from training and cause catastrophic OOD false positives during inference.
        
        features.append([
            host_len, num_dots, num_hyphens, num_digits, num_special, has_at, is_ip
        ])
    return np.array(features)
