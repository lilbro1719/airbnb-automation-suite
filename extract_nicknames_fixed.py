#!/usr/bin/env python3
"""
Airbnb Property Nickname Extractor - FIXED PARSING VERSION
Extracts nicknames directly from the listings table
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import time
import os
import json
import re
from datetime import datetime

class PropertyNicknameExtractor:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.properties = []
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Brave browser driver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Find Brave browser
            brave_paths = [
                r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
                r"C:\Users\{}\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe".format(os.getenv('USERNAME'))
            ]
            
            brave_path = None
            for path in brave_paths:
                if os.path.exists(path):
                    brave_path = path
                    break
            
            if brave_path:
                chrome_options.binary_location = brave_path
            
            # Use same profile as main script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            profile_dir = os.path.join(script_dir, "airbnb_brave_profile")
            chrome_options.add_argument(f"--user-data-dir={profile_dir}")
            chrome_options.add_argument("--profile-directory=Default")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 20)
            print("✅ Browser setup successful")
            
        except Exception as e:
            print(f"❌ Failed to setup browser: {e}")
            raise
    
    def navigate_to_listings(self):
        """Navigate to listings page"""
        print("Navigating to listings page...")
        self.driver.get("https://www.airbnb.com/hosting/listings")
        time.sleep(5)
        
        # Check if we're logged in
        current_url = self.driver.current_url
        if "login" in current_url or "listings" not in current_url:
            print("❌ Not logged in or can't access listings")
            return False
        
        print("✅ Successfully accessed listings page")
        return True
    
    def extract_properties_from_table(self):
        """Extract properties directly from the listings table"""
        print("Extracting properties from table...")
        
        # Wait for table to load
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tr")))
            time.sleep(5)
        except TimeoutException:
            print("❌ Timeout waiting for table to load")
            return []
        
        properties = []
        
        try:
            # Get all table rows
            rows = self.driver.find_elements(By.CSS_SELECTOR, "tr")
            print(f"Found {len(rows)} table rows")
            
            for i, row in enumerate(rows[1:], 1):  # Skip header row
                try:
                    row_text = row.text.strip()
                    if not row_text or len(row_text) < 20:
                        continue
                    
                    print(f"\n--- Processing row {i} ---")
                    print(f"Row text: {row_text[:150]}...")
                    
                    # Parse the row text to extract title and nickname
                    title, nickname, status = self.parse_row_text(row_text)
                    
                    print(f"  Parsed - Title: '{title}', Nickname: '{nickname}', Status: '{status}'")
                    
                    # Check if location contains Seoul - skip if it does
                    is_seoul = self.is_seoul_location(row_text)
                    
                    if is_seoul:
                        print(f"❌ Skipped (Seoul location): {title or 'Unknown'}")
                    elif title and nickname and status == "Listed":
                        properties.append({
                            'airbnb_name': title,
                            'internal_name': nickname,
                            'status': status
                        })
                        print(f"✅ Added: '{title}' → '{nickname}'")
                    elif status != "Listed":
                        print(f"❌ Skipped (Status: {status}): {title or 'Unknown'}")
                    else:
                        print(f"❌ Could not parse properly: Title={title}, Nickname={nickname}")
                        
                except Exception as e:
                    print(f"Error processing row {i}: {e}")
                    continue
        
        except Exception as e:
            print(f"Error extracting from table: {e}")
        
        print(f"\n✅ Successfully extracted {len(properties)} LISTED properties")
        return properties
    
    def parse_row_text(self, row_text):
        """Parse row text to extract title, nickname, and status"""
        # Fix line splitting - use proper newline character
        lines = [line.strip() for line in row_text.split('\n') if line.strip()]
        
        print(f"    Debug - Found {len(lines)} lines:")
        for j, line in enumerate(lines[:6]):  # Show first 6 lines
            print(f"      Line {j}: '{line}'")
        
        title = None
        nickname = None
        status = "Unknown"
        
        # Typical row structure based on your output:
        # Line 0: Property Title
        # Line 1: Nickname 
        # Line 2: "Home" (type)
        # Line 3: Location
        # Line 4+: Status and other info
        
        if len(lines) >= 2:
            # First line should be the property title
            potential_title = lines[0]
            if self.looks_like_property_title(potential_title):
                title = potential_title
                
                # Second line should be the nickname
                potential_nickname = lines[1]
                if self.looks_like_nickname(potential_nickname):
                    nickname = potential_nickname
                else:
                    print(f"    Warning: Line 1 doesn't look like nickname: '{potential_nickname}'")
            else:
                print(f"    Warning: Line 0 doesn't look like property title: '{potential_title}'")
        
        # Find status in the full row text
        row_lower = row_text.lower()
        if 'listed' in row_lower and 'unlisted' not in row_lower:
            status = "Listed"
        elif 'unlisted' in row_lower:
            status = "Unlisted"  
        elif 'action required' in row_lower:
            status = "Action Required"
        elif 'draft' in row_lower:
            status = "Draft"
        else:
            # Default to Listed if no clear status found
            status = "Listed"
        
        return title, nickname, status
    
    def is_seoul_location(self, row_text):
        """Check if the property location is Seoul"""
        row_lower = row_text.lower()
        seoul_indicators = ['seoul', 'hongdae']
        
        for indicator in seoul_indicators:
            if indicator in row_lower:
                return True
        
        return False
    
    def looks_like_property_title(self, text):
        """Check if text looks like a property title"""
        if not text or len(text) < 10 or len(text) > 100:
            return False
        
        # Should contain property-related words
        property_indicators = [
            'bed', 'bedroom', 'apartment', 'house', 'villa', 'room', 'studio', 
            'penthouse', 'loft', 'pad', 'home', 'place', 'dream', 'view',
            'pool', 'bamboo', 'zen', 'yoga', 'beach', 'jungle', 'rice',
            'castle', 'tower', 'getaway', 'haven', 'barn', 'central'
        ]
        
        text_lower = text.lower()
        has_indicator = any(indicator in text_lower for indicator in property_indicators)
        
        # Also check if it's in title case or has multiple words (typical for property titles)
        has_multiple_words = len(text.split()) > 2
        
        return has_indicator or has_multiple_words
    
    def looks_like_nickname(self, text):
        """Check if text looks like a nickname/internal name"""
        if not text or len(text) < 1 or len(text) > 40:
            return False
        
        # Skip obvious non-nicknames
        skip_words = ['home', 'apartment', 'house', 'villa', 'room', 'studio', 'entire']
        text_lower = text.lower().strip()
        
        if text_lower in skip_words:
            return False
        
        # Good nicknames from your examples:
        # "2bed", "Japanese", "710", "1914 Penthouse", "V20", "V23", "joglo", 
        # "7.5 home Wayan coconuts", "7:5 w a y a n", "Tower Wayan", etc.
        
        # Accept almost anything that's not obviously a location or type
        location_indicators = ['tegallalang', 'seoul', 'bali', 'ubud', 'payangan', 'hongdae', 'kecamatan']
        for loc in location_indicators:
            if loc in text_lower:
                return False
        
        return True
    
    def save_property_mapping(self):
        """Save property mappings to files"""
        if not self.properties:
            print("❌ No properties to save")
            return
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save as JSON
        json_file = os.path.join(script_dir, f"property_nicknames_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.properties, f, indent=2, ensure_ascii=False)
        
        # Save as TXT table
        txt_file = os.path.join(script_dir, f"property_nicknames_{timestamp}.txt")
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("AIRBNB PROPERTY NICKNAMES\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"{'Airbnb Name':<50} | {'Internal Name':<25}\n")
            f.write("-" * 80 + "\n")
            
            for prop in self.properties:
                airbnb_name = prop['airbnb_name'][:49]  # Truncate if too long
                internal_name = prop['internal_name'][:24]  # Truncate if too long
                f.write(f"{airbnb_name:<50} | {internal_name:<25}\n")
        
        # Save as Python dict for easy importing
        py_file = os.path.join(script_dir, f"property_nicknames_{timestamp}.py")
        with open(py_file, 'w', encoding='utf-8') as f:
            f.write("# Airbnb Property Nicknames Mapping\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("PROPERTY_NICKNAMES = {\n")
            for prop in self.properties:
                f.write(f"    '{prop['airbnb_name']}': '{prop['internal_name']}',\n")
            f.write("}\n\n")
            f.write("def get_nickname(airbnb_name):\n")
            f.write("    \"\"\"Get nickname for Airbnb property name\"\"\"\n")
            f.write("    return PROPERTY_NICKNAMES.get(airbnb_name, airbnb_name[:15])\n")
        
        print(f"\n✅ Property mappings saved:")
        print(f"  📄 TXT table: {txt_file}")
        print(f"  📋 JSON data: {json_file}")
        print(f"  🐍 Python dict: {py_file}")
        
        # Display results
        print(f"\n📊 EXTRACTED {len(self.properties)} PROPERTY NICKNAMES:")
        print("-" * 80)
        for prop in self.properties:
            print(f"  {prop['airbnb_name'][:45]:<45} → {prop['internal_name']}")
    
    def run(self):
        """Main execution"""
        try:
            print("=== AIRBNB PROPERTY NICKNAME EXTRACTOR - FIXED PARSING ===")
            
            if not self.navigate_to_listings():
                return
            
            # Extract properties from table
            self.properties = self.extract_properties_from_table()
            
            if self.properties:
                self.save_property_mapping()
            else:
                print("❌ No properties extracted")
                
        except Exception as e:
            print(f"❌ Error during execution: {e}")
            import traceback
            traceback.print_exc()
        finally:
            input("\nPress Enter to close browser...")
            if self.driver:
                self.driver.quit()

def main():
    extractor = PropertyNicknameExtractor()
    extractor.run()

if __name__ == "__main__":
    main()
