#!/usr/bin/env python3
"""
Integrated Airbnb Automation - Indonesian Cleaner Messages with Nicknames
FINAL FIXED VERSION - Corrects date parsing and classification logic
BALI ONLY - Excludes Seoul properties
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
from property_nickname_helper import PropertyNicknameHelper

class AirbnbIndonesianAutomation:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.today = datetime.now().date()
        self.tomorrow = self.today + timedelta(days=1)
        self.nickname_helper = PropertyNicknameHelper()
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
    
    def is_seoul_property(self, property_name):
        """Check if property is in Seoul (to be excluded)"""
        if not property_name:
            return False
        
        property_lower = property_name.lower()
        seoul_indicators = [
            'seoul', 'korea', 'korean', 'gangnam', 'hongdae', 'myeongdong', 
            'itaewon', 'dongdaemun', 'insadong', 'jung-gu', 'yongsan',
            'south korea', 'kr', 'seoul station'
        ]
        
        for indicator in seoul_indicators:
            if indicator in property_lower:
                print(f"🚫 Excluding Seoul property: {property_name}")
                return True
        
        return False
    
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
        """Parse reservation and check if relevant for tomorrow - FINAL FIXED VERSION"""
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
            
            # STEP 1: Find guest name - improved detection
            for i, line in enumerate(lines[:8]):
                if self._is_guest_name(line, i):
                    data['guest_name'] = line
                    print(f"  → Found guest name: '{line}' at position {i}")
                    break
            
            # STEP 2: Find dates - FIXED to only extract from this reservation's specific text
            all_dates = []
            date_context_lines = []
            
            # Only look at first 10-15 lines to avoid page header contamination
            relevant_lines = lines[:15] if len(lines) > 15 else lines
            
            for line in relevant_lines:
                # Skip header/navigation lines that contain many dates
                line_lower = line.lower()
                if any(word in line_lower for word in ['status', 'guests', 'check-in', 'checkout', 'booked', 'listing', 'confirmation', 'total', 'actions', 'review']):
                    continue
                    
                dates = self._extract_dates_robust(line)
                if dates:
                    all_dates.extend(dates)
                    date_context_lines.append(line[:100])  # Keep context
            
            # Remove duplicates while preserving order
            unique_dates = []
            for date in all_dates:
                if date not in unique_dates:
                    unique_dates.append(date)
            unique_dates.sort()
            
            print(f"  → Guest: {data.get('guest_name', 'Unknown')}")
            print(f"  → Found dates: {unique_dates}")
            if date_context_lines:
                print(f"  → Date context: {date_context_lines[0]}")
            
            # CRITICAL FIX: Improved date assignment logic for correct check-in/checkout identification
            if len(unique_dates) >= 2:
                # Priority 1: Check if tomorrow is exactly one of the dates
                if self.tomorrow in unique_dates:
                    idx = unique_dates.index(self.tomorrow)
                    
                    # Smart logic: Find the most relevant date pair that includes tomorrow
                    # Look for consecutive dates that form a valid reservation period
                    found_pair = False
                    
                    # Check if tomorrow can be paired with the next date (check-in scenario)
                    if idx < len(unique_dates) - 1:
                        next_date = unique_dates[idx + 1]
                        # If next date is within reasonable range (1-30 days), it's likely checkout
                        days_diff = (next_date - self.tomorrow).days
                        if 1 <= days_diff <= 30:
                            data['checkin_date'] = self.tomorrow
                            data['checkout_date'] = next_date
                            found_pair = True
                            print(f"  → Tomorrow is check-in date: {self.tomorrow} to {next_date} ({days_diff} days)")
                    
                    # If not found above, check if tomorrow can be paired with previous date (checkout scenario)
                    if not found_pair and idx > 0:
                        prev_date = unique_dates[idx - 1]
                        # If previous date is within reasonable range, it's likely check-in
                        days_diff = (self.tomorrow - prev_date).days
                        if 1 <= days_diff <= 30:
                            data['checkin_date'] = prev_date
                            data['checkout_date'] = self.tomorrow
                            found_pair = True
                            print(f"  → Tomorrow is checkout date: {prev_date} to {self.tomorrow} ({days_diff} days)")
                    
                    # Fallback: if no reasonable pair found, treat as single date
                    if not found_pair:
                        text_lower = text.lower()
                        if 'checkout' in text_lower or 'check-out' in text_lower:
                            data['checkout_date'] = self.tomorrow
                            print(f"  → Tomorrow is checkout (no valid pair): {self.tomorrow}")
                        else:
                            data['checkin_date'] = self.tomorrow
                            print(f"  → Tomorrow is check-in (no valid pair): {self.tomorrow}")
                
                # Priority 2: Check if tomorrow falls within a reasonable date range
                else:
                    for i in range(len(unique_dates) - 1):
                        start_date = unique_dates[i]
                        end_date = unique_dates[i + 1]
                        
                        # Check if tomorrow falls within this date range and range is reasonable
                        range_days = (end_date - start_date).days
                        if (start_date <= self.tomorrow < end_date and 1 <= range_days <= 30):
                            data['checkin_date'] = start_date
                            data['checkout_date'] = end_date
                            print(f"  → Tomorrow falls within range: {start_date} to {end_date} ({range_days} days)")
                            break
                    
                    # If no valid range includes tomorrow, it's not relevant
                    if not data['checkin_date'] and not data['checkout_date']:
                        print(f"  → No valid date range includes tomorrow, skipping reservation")
                        return None
            
            # Single date case
            elif len(unique_dates) == 1:
                single_date = unique_dates[0]
                if single_date == self.tomorrow:
                    # Determine check-in vs checkout from context
                    text_lower = text.lower()
                    if 'checkout' in text_lower or 'check-out' in text_lower:
                        data['checkout_date'] = single_date
                        print(f"  → Single date checkout: {single_date}")
                    else:
                        data['checkin_date'] = single_date
                        print(f"  → Single date check-in: {single_date}")
                else:
                    print(f"  → Single date {single_date} doesn't involve tomorrow")
                    return None
            
            # No dates found
            else:
                print(f"  → No dates found, skipping reservation")
                return None
            
            # STEP 3: Find guest count
            for line in lines:
                count = self._extract_guest_count_robust(line)
                if count:
                    data['guest_count'] = count
                    break
            
            # STEP 4: Find property name
            for line in lines:
                if self._is_property_name(line):
                    data['property_name'] = self._clean_property_name(line)
                    break
            
            # STEP 5: Fallbacks
            if not data['guest_name']:
                data['guest_name'] = self._extract_fallback_name(lines)
                if data['guest_name']:
                    print(f"  → Using fallback guest name: '{data['guest_name']}'")
                else:
                    print(f"  → No guest name found, skipping reservation")
                    return None
            
            if not data['property_name']:
                for line in lines[5:15]:
                    if self._is_property_name(line):
                        data['property_name'] = self._clean_property_name(line)
                        break
                if not data['property_name']:
                    data['property_name'] = "Property"
            
            # Check if Seoul property (exclude)
            if self.is_seoul_property(data['property_name']):
                print(f"  → EXCLUDED: Seoul property")
                return None
            
            # FINAL CHECK: Determine relevance for tomorrow
            is_relevant = False
            relevance_reason = ""
            
            print(f"  → Dates: Check-in={data['checkin_date']}, Checkout={data['checkout_date']}")
            print(f"  → Tomorrow: {self.tomorrow}")
            
            # Check if reservation has already ended (both dates in the past)
            if (data['checkout_date'] and data['checkout_date'] < self.tomorrow and 
                data['checkin_date'] and data['checkin_date'] < self.tomorrow):
                print(f"  → EXCLUDED: Reservation already ended ({data['checkout_date']})")
                return None
            
            if data['checkout_date'] == self.tomorrow:
                is_relevant = True
                relevance_reason = "Checkout tomorrow"
                data['type'] = 'checkout'
            elif data['checkin_date'] == self.tomorrow:
                is_relevant = True
                relevance_reason = "Check-in tomorrow"
                data['type'] = 'checkin'
            
            print(f"  → RELEVANT: {is_relevant} - {relevance_reason}")
            
            if is_relevant and data['guest_name']:
                # Get property nickname
                data['property_nickname'] = self.nickname_helper.get_nickname(data['property_name'])
                print(f"  → Property: '{data['property_name']}' → Nickname: '{data['property_nickname']}'")
                
                # Fallback for nickname
                if not data['property_nickname']:
                    # Try alternative property detection
                    for line in lines:
                        if len(line) > 10 and any(word in line.lower() for word in ['bed', 'bath', 'villa', 'dream', 'bamboo', 'buddha', 'rice', 'paddy']):
                            alt_nickname = self.nickname_helper.get_nickname(line)
                            if alt_nickname:
                                data['property_name'] = line
                                data['property_nickname'] = alt_nickname
                                print(f"  → Found alternative: '{line}' → '{alt_nickname}'")
                                break
                
                # Final fallback
                if not data['property_nickname']:
                    data['property_nickname'] = data['property_name'][:20] + "..." if len(data['property_name']) > 20 else data['property_name']
                    print(f"  → Using fallback nickname: '{data['property_nickname']}'")
                
                return data
                
        except Exception as e:
            print(f"Error parsing reservation: {e}")
        
        return None
    
    def _is_guest_name(self, line, position):
        """Check if line is a guest name"""
        if position > 3 or len(line) < 2 or len(line) > 50:
            return False
        
        excludes = [
            'confirmed', 'pending', 'cancelled', 'status', 'check', 'guest', 'adult', 
            'night', 'total', 'booking', 'reservation', 'review', 'listing', 'property',
            'apartment', 'house', 'room', 'actions', 'details', 'contact', 'message',
            'upcoming', 'current', 'past', 'today', 'tomorrow', 'currently', 'hosting',
            'trip', 'change', 'requested', 'booked', 'checkout', 'payout', 'confirmation',
            'code', 'guests', 'checkin'
        ]
        
        line_lower = line.lower()
        for exclude in excludes:
            if exclude in line_lower:
                return False
        
        if re.search(r'\d{1,2}[/\-]\d{1,2}|\w+ \d{1,2}', line):
            return False
        
        if re.match(r'^[\d\$\€\£\@\#\%]', line):
            return False
        
        if re.match(r'^[A-Za-z\s\'\-\.À-ÿ\u4e00-\u9fff\u0100-\u017f]+$', line):
            return True
        
        return False
    
    def _is_property_name(self, line):
        """Check if line looks like a property name"""
        if len(line) < 3 or len(line) > 100:
            return False
        
        property_words = [
            'apartment', 'house', 'room', 'studio', 'villa', 'condo', 'place', 'home',
            'loft', 'suite', 'flat', 'unit', 'bedroom', 'bed', 'bath', 'penthouse',
            'cottage', 'cabin', 'bungalow', 'townhouse', 'duplex', 'newly', 'built',
            'private', 'rice', 'paddy', 'pool', 'view', 'dream', 'serene', 'bamboo',
            'buddha', 'jungle', 'getaway', 'peace', 'coconuts', 'secret', 'bali',
            'tranquil', 'japanese', 'terrace'
        ]
        
        line_lower = line.lower()
        has_property_word = any(word in line_lower for word in property_words)
        
        if has_property_word:
            excludes = ['confirmed', 'pending', 'cancelled', 'guest', 'adult', 'total', 'actions', 'review', 'details']
            if not any(exclude in line_lower for exclude in excludes):
                return True
        
        return False
    
    def _clean_property_name(self, property_name):
        """Clean property name by removing trailing dots and extra info"""
        if not property_name:
            return property_name
            
        # Remove trailing ... and extra content after codes
        cleaned = property_name.rstrip('.')
        
        # Remove confirmation codes (pattern: space + 2+ uppercase letters/numbers)
        cleaned = re.sub(r'\s+[A-Z0-9]{6,}\s*\$?[\d,\.]*', '', cleaned)
        
        # Remove price info
        cleaned = re.sub(r'\s*\$[\d,\.]+.*$', '', cleaned)
        
        return cleaned.strip()
    
    def _extract_dates_robust(self, line):
        """Extract dates from line"""
        dates = []
        
        # Pattern: Month Day, Year
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
        
        return dates
    
    def _extract_guest_count_robust(self, line):
        """Extract guest count"""
        patterns = [
            r'(\d+)\s*adults?',
            r'(\d+)\s*guests?',
            r'(\d+)\s*people'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line.lower())
            if match:
                count = int(match.group(1))
                if 1 <= count <= 20:
                    return str(count)
        
        return None
    
    def _extract_fallback_name(self, lines):
        """Extract fallback guest name"""
        for line in lines[:5]:
            if (3 <= len(line) <= 40 and
                re.match(r'^[A-Za-z\s\'\-\.À-ÿ\u4e00-\u9fff]+$', line) and
                not any(word in line.lower() for word in [
                    'status', 'confirmed', 'pending', 'cancelled', 'guest', 'adult', 
                    'booking', 'reservation', 'check', 'night', 'total', 'actions'
                ])):
                return line
        
        return "Unknown Guest"
    
    def format_date_indonesian(self, date_obj):
        """Format date as '7Aug' style (no leading zero)"""
        if not date_obj:
            return None
        
        day = str(date_obj.day)  # No leading zero
        month = date_obj.strftime('%b')
        return f"{day}{month}"
    
    def get_tomorrows_reservations(self):
        """Get tomorrow's reservations (BALI ONLY)"""
        print(f"\n=== GETTING TOMORROW'S RESERVATIONS - BALI ONLY ({self.tomorrow}) ===")
        
        reservations = {'checkouts': [], 'checkins': []}
        
        try:
            if not self.navigate_to_reservations():
                return reservations
            
            reservation_texts = self.extract_all_reservations_raw()
            
            print(f"\nProcessing {len(reservation_texts)} reservations...")
            
            for i, text in enumerate(reservation_texts):
                print(f"\n{'='*20} RESERVATION {i+1} {'='*20}")
                print(f"Raw text preview: {text[:200]}...")
                
                reservation = self.parse_reservation_fixed(text)
                
                if reservation:
                    if reservation.get('type') == 'checkout':
                        reservations['checkouts'].append(reservation)
                        print(f"✅ CHECKOUT: {reservation['property_nickname']}")
                    
                    if reservation.get('type') == 'checkin':
                        reservations['checkins'].append(reservation)  
                        print(f"✅ CHECK-IN: {reservation['property_nickname']}")
            
            print(f"\n📊 BALI RESULTS: {len(reservations['checkouts'])} checkouts, {len(reservations['checkins'])} check-ins")
            
        except Exception as e:
            print(f"Error getting reservations: {e}")
            import traceback
            traceback.print_exc()
        
        return reservations
    
    def create_indonesian_cleaner_message(self, reservations):
        """Create Indonesian cleaner message"""
        messages = []
        
        # Process checkouts - use property nicknames only
        if reservations['checkouts']:
            out_properties = [res['property_nickname'] for res in reservations['checkouts']]
            if out_properties:
                out_msg = "Out: " + ", ".join(out_properties)
                messages.append(out_msg)
        
        # Process check-ins - use property nicknames and correct date format
        if reservations['checkins']:
            for res in reservations['checkins']:
                property_nickname = res['property_nickname']
                guest_count = res['guest_count']
                
                checkin_str = self.format_date_indonesian(res.get('checkin_date', self.tomorrow))
                checkout_str = self.format_date_indonesian(res.get('checkout_date'))
                
                # Only show date range if we have both dates
                if checkin_str and checkout_str:
                    date_range = f"{checkin_str}-{checkout_str}"
                elif checkin_str:
                    date_range = checkin_str
                else:
                    date_range = "TBC"
                
                in_msg = f"In: {property_nickname}, {guest_count} orang, {date_range}"
                messages.append(in_msg)
        
        if messages:
            return "\n".join(messages)
        else:
            return f"Besok tidak ada checkout atau checkin di Bali ({self.format_date_indonesian(self.tomorrow)})"
    
    def run(self):
        """Main execution"""
        try:
            print("=== AIRBNB INDONESIAN CLEANER AUTOMATION - BALI ONLY (FIXED) ===")
            print(f"Today: {self.today}")
            print(f"Tomorrow: {self.tomorrow}")
            
            if self.check_existing_session():
                print("✅ Already logged in!")
            else:
                print("❌ Not logged in. Please login first.")
                return
            
            print(f"✅ Loaded {len(self.nickname_helper.get_all_nicknames())} property nicknames")
            
            reservations = self.get_tomorrows_reservations()
            indonesian_message = self.create_indonesian_cleaner_message(reservations)
            
            print("\n" + "="*60)
            print("PESAN UNTUK CLEANER BALI (INDONESIAN):")
            print("="*60)
            print(indonesian_message)
            print("="*60)
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            filename = os.path.join(script_dir, f"indonesian_cleaner_message_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Pesan Cleaner Bali - {self.tomorrow.strftime('%d %B %Y')}\n")
                f.write("="*50 + "\n\n")
                f.write(indonesian_message)
                f.write(f"\n\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
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
    automation = AirbnbIndonesianAutomation()
    automation.run()

if __name__ == "__main__":
    main()
