#!/usr/bin/env python3
"""
Fixed Airbnb automation - Gets TOMORROW's reservations with accurate parsing
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from datetime import datetime, timedelta
import os
import re
import json

class AirbnbAutomationFixed:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.today = datetime.now().date()
        self.tomorrow = self.today + timedelta(days=1)
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Brave browser driver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
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
    
    def check_existing_session(self):
        """Check if already logged in"""
        self.driver.get("https://www.airbnb.com/hosting")
        time.sleep(3)
        current_url = self.driver.current_url
        return "hosting" in current_url and "login" not in current_url
    
    def navigate_to_reservations(self):
        """Navigate to reservations page"""
        print("Navigating to reservations page...")
        self.driver.get("https://www.airbnb.com/hosting/reservations")
        time.sleep(5)
        return True
    
    def extract_all_reservations_raw(self):
        """Extract raw reservation texts for manual parsing"""
        print("Extracting raw reservation data...")
        
        # Find reservation elements
        selectors = [
            "[data-testid*='reservation']",
            "[data-testid*='booking']",
            "[class*='reservation']",
            "[role='listitem']"
        ]
        
        all_elements = []
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                all_elements.extend(elements)
            except:
                continue
        
        # Get unique reservation texts
        reservation_texts = []
        seen_texts = set()
        
        for element in all_elements:
            try:
                text = element.text.strip()
                if text and len(text) > 50 and text not in seen_texts:
                    reservation_texts.append(text)
                    seen_texts.add(text)
            except:
                continue
        
        print(f"Found {len(reservation_texts)} unique reservation texts")
        return reservation_texts
    
    def parse_reservation_fixed(self, text):
        """Fixed reservation parsing with proper field identification"""
        try:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            data = {
                'guest_name': None,
                'property_name': None,
                'guest_count': '1',
                'checkin_date': None,
                'checkout_date': None,
                'raw_text': text[:500]
            }
            
            # Debug: print all lines to understand structure
            print(f"\nParsing reservation with {len(lines)} lines:")
            for i, line in enumerate(lines):
                print(f"  {i}: '{line}'")
            
            # STEP 1: Find guest name (usually first meaningful line)
            for i, line in enumerate(lines[:5]):
                if self._is_guest_name(line, i):
                    data['guest_name'] = line
                    print(f"  → Guest name found: '{line}' at line {i}")
                    break
            
            # STEP 2: Find dates first (they're most reliable)
            all_dates = []
            for line in lines:
                dates = self._extract_dates_robust(line)
                all_dates.extend(dates)
            
            # Remove duplicates and sort
            unique_dates = list(dict.fromkeys(all_dates))  # Preserves order
            unique_dates.sort()
            
            if len(unique_dates) >= 2:
                data['checkin_date'] = unique_dates[0]
                data['checkout_date'] = unique_dates[1]
                print(f"  → Dates found: {unique_dates[0]} to {unique_dates[1]}")
            elif len(unique_dates) == 1:
                # Single date - determine based on tomorrow's context
                single_date = unique_dates[0]
                if single_date == self.tomorrow:
                    # Could be either check-in or check-out
                    data['checkin_date'] = single_date
                    data['checkout_date'] = single_date
                    print(f"  → Single date (tomorrow): {single_date}")
            
            # STEP 3: Find guest count
            for line in lines:
                count = self._extract_guest_count_robust(line)
                if count:
                    data['guest_count'] = count
                    print(f"  → Guest count: {count}")
                    break
            
            # STEP 4: Find property name (look for property-like strings)
            for line in lines:
                if self._is_property_name(line):
                    data['property_name'] = line
                    print(f"  → Property name: '{line}'")
                    break
            
            # STEP 5: Apply fallbacks
            if not data['guest_name']:
                data['guest_name'] = self._extract_fallback_name(lines)
                print(f"  → Fallback guest name: '{data['guest_name']}'")
            
            if not data['property_name']:
                data['property_name'] = "Property"
            
            # Only return if we have minimum data and relevant dates
            is_relevant = False
            if data['checkout_date'] == self.tomorrow:
                is_relevant = True
                print("  → RELEVANT: Checkout tomorrow")
            elif data['checkin_date'] == self.tomorrow:
                is_relevant = True
                print("  → RELEVANT: Check-in tomorrow")
            
            if is_relevant and data['guest_name']:
                return data
            else:
                print("  → NOT RELEVANT or insufficient data")
                
        except Exception as e:
            print(f"Error parsing reservation: {e}")
        
        return None
    
    def _is_guest_name(self, line, position):
        """Check if line is a guest name with stricter rules"""
        # Must be in first 3 lines
        if position > 2:
            return False
        
        # Length check
        if len(line) < 2 or len(line) > 50:
            return False
        
        # Must contain letters
        if not re.search(r'[a-zA-Z]', line):
            return False
        
        # Exclude obvious non-names
        excludes = [
            'confirmed', 'pending', 'cancelled', 'status', 'check', 'guest', 'adult', 
            'night', 'total', 'booking', 'reservation', 'review', 'listing', 'property',
            'apartment', 'house', 'room', 'actions', 'details', 'contact', 'message',
            'upcoming', 'current', 'past', 'today', 'tomorrow'
        ]
        
        line_lower = line.lower()
        for exclude in excludes:
            if exclude in line_lower:
                return False
        
        # Exclude if contains dates
        if re.search(r'\d{1,2}[/\-]\d{1,2}|\w+ \d{1,2}', line):
            return False
        
        # Exclude if starts with numbers or symbols
        if re.match(r'^[\d\$\€\£\@\#\%]', line):
            return False
        
        # Should look like a name (letters, spaces, common name chars)
        if re.match(r'^[A-Za-z\s\'\-\.À-ÿ]+$', line):
            return True
        
        return False
    
    def _is_property_name(self, line):
        """Check if line looks like a property name"""
        if len(line) < 3 or len(line) > 100:
            return False
        
        # Property indicators
        property_words = [
            'apartment', 'house', 'room', 'studio', 'villa', 'condo', 'place', 'home',
            'loft', 'suite', 'flat', 'unit', 'bedroom', 'bed', 'bath', 'penthouse',
            'cottage', 'cabin', 'bungalow', 'townhouse', 'duplex'
        ]
        
        # Location indicators
        location_words = [
            'downtown', 'uptown', 'center', 'central', 'near', 'close', 'beach', 'ocean',
            'mountain', 'city', 'urban', 'suburban', 'quiet', 'cozy', 'modern', 'luxury',
            'beautiful', 'stunning', 'amazing', 'perfect', 'spacious', 'comfortable'
        ]
        
        line_lower = line.lower()
        
        # Must contain at least one property or location word
        has_property_word = any(word in line_lower for word in property_words)
        has_location_word = any(word in line_lower for word in location_words)
        
        if has_property_word or has_location_word:
            # Exclude if it looks like status or booking info
            excludes = ['confirmed', 'pending', 'cancelled', 'guest', 'adult', 'total', 'actions']
            if not any(exclude in line_lower for exclude in excludes):
                return True
        
        return False
    
    def _extract_dates_robust(self, line):
        """Robust date extraction"""
        dates = []
        
        # Pattern 1: Month Day, Year (Jul 28, 2025)
        pattern1 = r'(\w{3,9})\s+(\d{1,2}),?\s*(\d{4})'
        matches = re.finditer(pattern1, line)
        for match in matches:
            try:
                month_str, day_str, year_str = match.groups()
                for fmt in ['%B %d, %Y', '%b %d, %Y', '%B %d %Y', '%b %d %Y']:
                    try:
                        date_str = f"{month_str} {day_str}, {year_str}"
                        date = datetime.strptime(date_str, fmt).date()
                        if date not in dates:
                            dates.append(date)
                        break
                    except:
                        continue
            except:
                continue
        
        # Pattern 2: Month Day (Jul 28) - add current year
        pattern2 = r'(\w{3,9})\s+(\d{1,2})(?![:\d])'
        matches = re.finditer(pattern2, line)
        for match in matches:
            try:
                month_str, day_str = match.groups()
                current_year = datetime.now().year
                for fmt in ['%B %d', '%b %d']:
                    try:
                        date_str = f"{month_str} {day_str}"
                        date = datetime.strptime(date_str, fmt).replace(year=current_year).date()
                        if date not in dates:
                            dates.append(date)
                        break
                    except:
                        continue
            except:
                continue
        
        # Pattern 3: MM/DD/YYYY
        pattern3 = r'(\d{1,2})/(\d{1,2})/(\d{4})'
        matches = re.finditer(pattern3, line)
        for match in matches:
            try:
                month_str, day_str, year_str = match.groups()
                date = datetime(int(year_str), int(month_str), int(day_str)).date()
                if date not in dates:
                    dates.append(date)
            except:
                continue
        
        return dates
    
    def _extract_guest_count_robust(self, line):
        """Extract guest count with better patterns"""
        patterns = [
            r'(\d+)\s*adults?',
            r'(\d+)\s*guests?',
            r'(\d+)\s*people',
            r'(\d+)\s*persons?',
            r'(\d+)\s*pax'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line.lower())
            if match:
                count = int(match.group(1))
                if 1 <= count <= 20:  # Reasonable range
                    return str(count)
        
        return None
    
    def _extract_fallback_name(self, lines):
        """Extract name as fallback - be more conservative"""
        for line in lines[:5]:
            # Very strict name matching
            if (3 <= len(line) <= 40 and
                re.match(r'^[A-Za-z\s\'\-\.À-ÿ]+$', line) and
                not any(word in line.lower() for word in [
                    'status', 'confirmed', 'pending', 'cancelled', 'guest', 'adult', 
                    'booking', 'reservation', 'check', 'night', 'total', 'actions',
                    'review', 'listing', 'property', 'apartment', 'house', 'room'
                ])):
                return line
        
        return "Unknown Guest"
    
    def get_tomorrows_reservations(self):
        """Get tomorrow's reservations"""
        print(f"\n=== GETTING TOMORROW'S RESERVATIONS ({self.tomorrow}) ===")
        
        reservations = {'checkouts': [], 'checkins': []}
        
        try:
            if not self.navigate_to_reservations():
                return reservations
            
            # Extract all reservation texts
            reservation_texts = self.extract_all_reservations_raw()
            
            print(f"\nProcessing {len(reservation_texts)} reservations...")
            
            for i, text in enumerate(reservation_texts):
                print(f"\n{'='*50}")
                print(f"PROCESSING RESERVATION {i+1}")
                print(f"{'='*50}")
                
                reservation = self.parse_reservation_fixed(text)
                
                if reservation:
                    # Categorize by type
                    if reservation.get('checkout_date') == self.tomorrow:
                        reservations['checkouts'].append(reservation)
                        print(f"✅ Added to CHECKOUTS: {reservation['guest_name']}")
                    
                    if reservation.get('checkin_date') == self.tomorrow:
                        reservations['checkins'].append(reservation)
                        print(f"✅ Added to CHECK-INS: {reservation['guest_name']}")
                else:
                    print("❌ Not relevant for tomorrow")
            
            print(f"\n📊 FINAL RESULTS:")
            print(f"  Checkouts tomorrow: {len(reservations['checkouts'])}")
            print(f"  Check-ins tomorrow: {len(reservations['checkins'])}")
            
        except Exception as e:
            print(f"Error getting reservations: {e}")
            import traceback
            traceback.print_exc()
        
        return reservations
    
    def create_cleaner_message(self, reservations):
        """Create WhatsApp message for tomorrow's reservations"""
        tomorrow_str = self.tomorrow.strftime("%B %d, %Y")
        
        message = f"🏠 Cleaning Schedule - {tomorrow_str}\n\n"
        
        # Tomorrow's checkouts
        if reservations['checkouts']:
            message += "📤 TOMORROW'S CHECKOUTS:\n"
            for res in reservations['checkouts']:
                message += f"• {res['property_name']}\n"
                message += f"  Guest: {res['guest_name']}\n"
                message += f"  People: {res['guest_count']}\n"
                
                if res.get('checkin_date') and res.get('checkout_date'):
                    checkin = res['checkin_date'].strftime('%b %d')
                    checkout = res['checkout_date'].strftime('%b %d')
                    nights = (res['checkout_date'] - res['checkin_date']).days
                    message += f"  Stay: {checkin} to {checkout} ({nights} nights)\n\n"
                else:
                    message += f"  Checkout: {self.tomorrow.strftime('%b %d')}\n\n"
        
        # Tomorrow's check-ins
        if reservations['checkins']:
            message += "📥 TOMORROW'S CHECK-INS:\n"
            for res in reservations['checkins']:
                message += f"• {res['property_name']}\n"
                message += f"  Guest: {res['guest_name']}\n"
                message += f"  People: {res['guest_count']}\n"
                
                if res.get('checkin_date') and res.get('checkout_date'):
                    checkin = res['checkin_date'].strftime('%b %d')
                    checkout = res['checkout_date'].strftime('%b %d')
                    nights = (res['checkout_date'] - res['checkin_date']).days
                    message += f"  Stay: {checkin} to {checkout} ({nights} nights)\n\n"
                else:
                    message += f"  Check-in: {self.tomorrow.strftime('%b %d')}\n\n"
        
        if not reservations['checkouts'] and not reservations['checkins']:
            message += "No check-ins or check-outs scheduled for tomorrow.\n\n"
        
        message += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return message
    
    def save_debug_info(self, reservations, raw_texts):
        """Save debug information"""
        debug_data = {
            'timestamp': datetime.now().isoformat(),
            'today': self.today.isoformat(),
            'tomorrow': self.tomorrow.isoformat(),
            'total_raw_reservations': len(raw_texts),
            'total_checkouts': len(reservations['checkouts']),
            'total_checkins': len(reservations['checkins']),
            'raw_reservation_texts': raw_texts[:5],  # First 5 for debugging
            'parsed_reservations': reservations
        }
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        debug_file = os.path.join(script_dir, f"debug_tomorrow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(debug_file, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📊 Debug info saved to: {debug_file}")
    
    def run(self):
        """Main execution"""
        try:
            print("=== AIRBNB AUTOMATION - TOMORROW'S RESERVATIONS ===")
            print(f"Today: {self.today}")
            print(f"Tomorrow: {self.tomorrow}")
            
            if self.check_existing_session():
                print("✅ Already logged in!")
            else:
                print("❌ Not logged in. Please login first.")
                return
            
            # Get tomorrow's reservations
            reservations = self.get_tomorrows_reservations()
            
            # Create message
            message = self.create_cleaner_message(reservations)
            
            # Display message
            print("\n" + "="*60)
            print("WHATSAPP MESSAGE FOR CLEANER:")
            print("="*60)
            print(message)
            print("="*60)
            
            # Save message
            script_dir = os.path.dirname(os.path.abspath(__file__))
            filename = os.path.join(script_dir, f"cleaner_message_tomorrow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(message)
            
            print(f"\n📁 Message saved to: {filename}")
            print("\n📱 Copy this message to send via WhatsApp!")
            
        except Exception as e:
            print(f"❌ Error during execution: {e}")
            import traceback
            traceback.print_exc()
        finally:
            input("\nPress Enter to close browser...")
            if self.driver:
                self.driver.quit()

def main():
    automation = AirbnbAutomationFixed()
    automation.run()

if __name__ == "__main__":
    main()
