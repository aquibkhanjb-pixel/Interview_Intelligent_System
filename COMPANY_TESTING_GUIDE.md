# Company Testing Guide

## 🎯 How to Test New Companies

### Quick Test (Recommended)
```bash
python simple_company_test.py "CompanyName"
```

### Examples:
```bash
python simple_company_test.py "Razorpay"    # Test existing company
python simple_company_test.py "Tesla"       # Test new company
python simple_company_test.py "Postman"     # Test another company
```

### Full Test (Advanced)
```bash
python test_new_company.py "CompanyName"
```

### List All Companies
```bash
python list_supported_companies.py                 # Full report
python list_supported_companies.py --patterns      # Show all patterns
python list_supported_companies.py --active        # Show companies with data
python list_supported_companies.py --ready         # Show ready to scrape
```

---

## 📋 Complete List of Supported Companies

### 🏆 High Priority Companies (4)
- **PhonePe** → ['phonepe', 'phone pe']
- **Myntra** → ['myntra', 'myntra.com']
- **PayPal** → ['paypal', 'paypal.com']
- **PayTM** → ['paytm', 'paytm.com', 'one97']

### 🌟 Tech Giants (6)
- **Google** → ['google', 'alphabet', 'goog', 'google.com', 'alphabet inc']
- **Amazon** → ['amazon', 'amzn', 'aws', 'amazon.com', 'amazon inc']
- **Microsoft** → ['microsoft', 'msft', 'ms', 'microsoft.com', 'microsoft corporation']
- **Apple** → ['apple', 'aapl', 'apple inc', 'apple.com']
- **Meta** → ['meta', 'facebook', 'fb', 'instagram', 'whatsapp', 'meta platforms']
- **Netflix** → ['netflix', 'nflx', 'netflix.com', 'netflix inc']

### 🇮🇳 Indian Tech Companies (25)
- **Flipkart** → ['flipkart', 'flipkart.com', 'flipkart india']
- **Zomato** → ['zomato', 'zomato.com']
- **Swiggy** → ['swiggy', 'swiggy.com']
- **Ola** → ['ola', 'ola cabs', 'ola.com']
- **Uber** → ['uber', 'uber.com']
- **Razorpay** → ['razorpay', 'razorpay.com']
- **Dream11** → ['dream11', 'dream 11']
- **Carwale** → ['carwale', 'carwale.com', 'car wale']
- **BigBasket** → ['bigbasket', 'big basket']
- **Grofers** → ['grofers', 'blinkit']
- **Dunzo** → ['dunzo', 'dunzo.com']
- **Freshworks** → ['freshworks', 'freshdesk', 'freshservice']
- **Zoho** → ['zoho', 'zoho.com']
- **InMobi** → ['inmobi', 'inmobi.com']
- **ShareChat** → ['sharechat', 'share chat']
- **Nykaa** → ['nykaa', 'nykaa.com']
- **PolicyBazaar** → ['policybazaar', 'policy bazaar']
- **MakeMyTrip** → ['makemytrip', 'make my trip', 'mmt']
- **BookMyShow** → ['bookmyshow', 'book my show', 'bms']
- **Lenskart** → ['lenskart', 'lenskart.com']
- **UrbanCompany** → ['urbancompany', 'urban company', 'urbanclap', 'urban clap']
- **Cred** → ['cred', 'cred.com']
- **Unacademy** → ['unacademy', 'unacademy.com']
- **Vedantu** → ['vedantu', 'vedantu.com']
- **Byju** → ['byju', 'byjus', "byju's"]

**Total: 35 companies supported**

---

## ➕ How to Add New Companies

### Method 1: Edit the Central File
1. Open `utils/company_extractor.py`
2. Add your company to the `company_patterns` dictionary:

```python
# Add under appropriate category
'Tesla': ['tesla', 'tesla inc', 'tesla motors'],
'Spotify': ['spotify', 'spotify.com'],
'Airbnb': ['airbnb', 'airbnb.com', 'air bnb'],
```

3. Test with: `python simple_company_test.py "Tesla"`

### Method 2: Dynamic Addition (Runtime)
```python
from utils.company_extractor import add_company_patterns

# Add new company at runtime
add_company_patterns('Tesla', ['tesla', 'tesla inc', 'tesla motors'])
```

---

## 🔄 Testing Workflow

### For Existing Companies:
1. **Quick Test**: `python simple_company_test.py "Razorpay"`
2. **If patterns work**: Ready to scrape!
3. **Run Pipeline**: Use main scraping system

### For New Companies:
1. **Quick Test**: `python simple_company_test.py "Tesla"`
2. **If not supported**: Add patterns to `utils/company_extractor.py`
3. **Test Again**: Verify patterns work
4. **Run Pipeline**: Use main scraping system

### For Debugging:
1. **Pattern Issues**: Check `utils/company_extractor.py`
2. **Database Issues**: Use `fix_company_misclassification.py`
3. **Frontend Issues**: Check if company has experiences > 0

---

## 🎯 Success Criteria

A company is **ready for scraping** when:
- ✅ Pattern recognition works (all tests pass)
- ✅ Company appears in supported list
- ✅ No conflicts with other companies

A company will **appear in frontend** when:
- ✅ Pattern recognition works
- ✅ Scraping finds experiences (count > 0)
- ✅ Data is properly stored in database

---

## 🚀 Quick Examples

```bash
# Test if BigBasket is ready
python simple_company_test.py "BigBasket"

# Test if a new company works
python simple_company_test.py "Stripe"

# See all companies that have data
python list_supported_companies.py --active

# See all companies ready to scrape
python list_supported_companies.py --ready

# Full company report
python list_supported_companies.py
```

---

## 📈 Current Status

- **35 companies** supported with patterns
- **9 companies** currently have interview data
- **26 companies** ready to scrape (patterns configured)
- **Root cause fixed** - new companies will work correctly

---

*Last Updated: 2025-09-13*
*System: Interview Intelligence v2.0*