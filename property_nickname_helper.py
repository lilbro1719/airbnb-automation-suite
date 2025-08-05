#!/usr/bin/env python3
"""
Property Nickname Helper
Load and use property nicknames in main automation
"""
import json
import os
from datetime import datetime

class PropertyNicknameHelper:
    def __init__(self):
        self.nicknames = {}
        self.load_latest_nicknames()
    
    def load_latest_nicknames(self):
        """Load the most recent nickname mapping"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Find the latest JSON file
        nickname_files = []
        for file in os.listdir(script_dir):
            if file.startswith("property_nicknames_") and file.endswith(".json"):
                nickname_files.append(file)
        
        if not nickname_files:
            print("⚠️ No property nickname files found. Run extract_property_nicknames.py first.")
            return
        
        # Get the latest file
        latest_file = sorted(nickname_files)[-1]
        json_path = os.path.join(script_dir, latest_file)
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                properties = json.load(f)
            
            # Convert to simple dict
            for prop in properties:
                self.nicknames[prop['airbnb_name']] = prop['internal_name']
            
            print(f"✅ Loaded {len(self.nicknames)} property nicknames from {latest_file}")
            
        except Exception as e:
            print(f"❌ Error loading nicknames: {e}")
    
    def get_nickname(self, airbnb_name):
        """Get nickname for Airbnb property name"""
        # Try exact match first
        if airbnb_name in self.nicknames:
            return self.nicknames[airbnb_name]
        
        # Try partial matches (in case of slight differences)
        airbnb_lower = airbnb_name.lower()
        for full_name, nickname in self.nicknames.items():
            if airbnb_lower in full_name.lower() or full_name.lower() in airbnb_lower:
                return nickname
        
        # Fallback: return first 15 chars of original name
        return airbnb_name[:15]
    
    def get_all_nicknames(self):
        """Get all nickname mappings"""
        return self.nicknames.copy()
    
    def print_mappings(self):
        """Print all current mappings"""
        if not self.nicknames:
            print("No nicknames loaded")
            return
        
        print("\n📋 CURRENT PROPERTY NICKNAMES:")
        print("-" * 60)
        for airbnb_name, nickname in self.nicknames.items():
            print(f"  {airbnb_name[:35]:<35} → {nickname}")

# Example usage functions
def test_nickname_helper():
    """Test the nickname helper"""
    helper = PropertyNicknameHelper()
    helper.print_mappings()
    
    # Test some lookups
    test_names = [
        "2 Bed, 2 Bath Serene Dream",
        "Modern Downtown Apartment",
        "Cozy Studio Near Beach"
    ]
    
    print("\n🧪 TESTING NICKNAME LOOKUPS:")
    for name in test_names:
        nickname = helper.get_nickname(name)
        print(f"  '{name}' → '{nickname}'")

if __name__ == "__main__":
    test_nickname_helper()
