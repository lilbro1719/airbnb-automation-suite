# Airbnb Automation Suite

**Automated Airbnb reservation tracking and cleaner notification system for property management.**

## 🏠 Overview

This project automates the extraction of Airbnb check-in/check-out data and generates WhatsApp messages for cleaning staff. It focuses on tomorrow's bookings and uses property nicknames for efficient communication.

## ✨ Features

- **Tomorrow's Reservations**: Automatically extracts check-ins and check-outs for the next day
- **Property Nickname Mapping**: Converts long property names to short nicknames (e.g., "2 Bed, 2 Bath Serene Dream" → "2bed")
- **WhatsApp Message Generation**: Creates formatted messages for cleaning staff
- **Smart Filtering**: Processes only "Listed" Bali properties (excludes Seoul locations)
- **Session Persistence**: Uses saved browser profile for seamless login

## 🚀 Quick Start

### Prerequisites

- Windows 11
- Python 3.x
- Selenium WebDriver
- Brave Browser (with saved Airbnb login session)

### Installation

```bash
git clone https://github.com/[username]/airbnb-automation-suite.git
cd airbnb-automation-suite
pip install selenium
```

### Usage

1. **Extract Property Nicknames** (run once to build mapping):
```bash
python extract_nicknames_fixed.py
```

2. **Get Tomorrow's Reservations**:
```bash
python airbnb_tomorrow.py
```

3. **Use Nickname Helper** (for integration):
```python
from property_nickname_helper import PropertyNicknameHelper
helper = PropertyNicknameHelper()
nickname = helper.get_nickname("Long Property Name")
```

## 📁 Project Structure

```
airbnb-automation-suite/
├── airbnb_tomorrow.py              # Main reservation extractor
├── extract_nicknames_fixed.py     # Property nickname extractor  
├── property_nickname_helper.py    # Nickname utility class
├── test_manual_parsing.py         # Testing utilities
├── output/                        # Generated files
│   ├── property_nicknames_*.json  # Nickname mappings
│   ├── property_nicknames_*.txt   # Human-readable tables
│   ├── property_nicknames_*.py    # Python dictionaries
│   └── cleaner_message_*.txt      # WhatsApp messages
├── airbnb_brave_profile/          # Browser session data
└── README.md
```

## 🛠 How It Works

### 1. Property Nickname Extraction
- Navigates to Airbnb hosting listings page
- Parses table rows to extract property names and internal nicknames
- Filters for "Listed" status and Bali locations only
- Saves mappings in multiple formats (JSON, TXT, Python)

### 2. Reservation Processing
- Accesses Airbnb reservations page
- Extracts tomorrow's check-ins and check-outs using advanced parsing
- Maps property names to nicknames for cleaner communication
- Generates formatted WhatsApp messages

### 3. Smart Parsing Logic
- **Position-based guest detection**: Identifies guest names from specific line positions
- **Date filtering**: Focuses on tomorrow's bookings only
- **Status validation**: Processes only active, listed properties
- **Location filtering**: Excludes Seoul properties, focuses on Bali

## 📊 Sample Output

### Property Nickname Mapping
```
Airbnb Name                                      | Internal Name
------------------------------------------------------------
2 Bed, 2 Bath Serene Dream                      | 2bed
Japanese Villa with Rice Terrace                | Japanese
Secret Bali Getaway – Peace, Pool & Free Coconuts | v23
Tranquil Jungle Villa w/ Rice                   | V20
```

### WhatsApp Message
```
🏠 Cleaning Schedule - August 06, 2025

📤 TOMORROW'S CHECKOUTS:
• 2bed
  Guest: John Smith
  People: 2
  Stay: Aug 05 to Aug 06 (1 nights)

📥 TOMORROW'S CHECK-INS:
• v23
  Guest: Mary Johnson
  People: 4
  Stay: Aug 06 to Aug 09 (3 nights)

Generated: 2025-08-05 14:30:25
```

## 🔧 Configuration

- **Browser Profile**: Uses `airbnb_brave_profile/` directory for session persistence
- **Date Scope**: Configurable in `airbnb_tomorrow.py` (currently tomorrow only)
- **Location Filter**: Seoul properties excluded by default
- **Status Filter**: Only "Listed" properties processed

## 🚨 Important Notes

- Requires active Airbnb hosting account login in Brave browser
- Designed for Bali property portfolio (Seoul properties filtered out)
- Manual execution required (no automatic scheduling yet)
- WhatsApp messages require manual sending

## 🔮 Future Enhancements

- [ ] Automatic daily scheduling (cron jobs)
- [ ] WhatsApp API integration for direct sending
- [ ] Multi-day forecasting beyond tomorrow
- [ ] Property location optimization for cleaning routes
- [ ] Integration with calendar systems
- [ ] Real-time notifications

## 📝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

For support, questions, or feature requests, please open an issue in the GitHub repository.

---

**Status**: ✅ Active Development | **Last Updated**: August 2025 | **Version**: 1.0.0
