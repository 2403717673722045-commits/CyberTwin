# CyberTwin Dataset Information

## 1. SMS Spam Collection Dataset
- **Dataset Name**: SMS Spam Collection
- **Official Source**: UCI Machine Learning Repository
- **URL**: https://archive.ics.uci.edu/ml/datasets/sms+spam+collection
- **License**: Public Domain / Research use
- **Number of samples**: 5,574
- **Features**: Raw text messages
- **Labels**: `ham` (benign) and `spam` (malicious/suspicious)
- **Class Distribution**: 
  - Ham: 4,825 (86.6%)
  - Spam: 747 (13.4%)
- **Missing Values**: None
- **Duplicates**: Contains some duplicate messages. (Handled during data cleaning).
- **Limitations**: Short message lengths, English only, slightly dated (2012) but highly representative of short-form social engineering patterns.
- **Why it is suitable**: It perfectly matches the task of distinguishing benign messages from scams, phishing, and spam in short-text formats (SMS, WhatsApp), aligning with CyberTwin's core text analysis capabilities.
- **How it is mapped to CyberTwin**: The `ham` label maps to 'Benign', and the `spam` label maps to 'Phishing/Scam'.

## 2. Phishing URL Dataset
- **Dataset Name**: Phishing Website Detection (Extracted URLs)
- **Official Source**: Public benchmark dataset compilation (curated URl dataset)
- **URL**: https://github.com/shreyagopal/Phishing-Website-Detection-by-Machine-Learning-Techniques
- **License**: Open Source / MIT
- **Number of samples**: ~10,000 to ~400,000 depending on exact file (The downloaded one is ~450k URLs, subset will be used).
- **Features**: Raw URL strings
- **Labels**: `benign` (0) and `phishing` (1)
- **Class Distribution**: Balanced (approx. 50/50 in most benchmark subsets).
- **Missing Values**: Handled during cleaning.
- **Duplicates**: Handled during cleaning.
- **Limitations**: The landscape of phishing URLs changes rapidly. Some domains may no longer be active, but the structural patterns (length, hyphens, TLD usage) remain relevant.
- **Why it is suitable**: It provides raw URL strings rather than pre-extracted numerical features, allowing us to build and test our own URL feature extraction pipeline natively within CyberTwin.
- **How it is mapped to CyberTwin**: 0 maps to 'Benign' and 1 maps to 'Phishing/Malicious'.
