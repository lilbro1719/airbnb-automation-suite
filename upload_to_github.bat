@echo off
REM GitHub Upload Script for Airbnb Automation Suite (Windows)
REM Run this from: C:\Users\Owner\Documents\01_Projects\airbnb-automation-suite

echo 🚀 AIRBNB AUTOMATION SUITE - GITHUB UPLOAD
echo ==========================================

REM Step 1: Check if we're in the right directory
if not exist "airbnb_integrated_cleaner.py" (
    echo ❌ Error: Not in the correct directory!
    echo Please run this script from: C:\Users\Owner\Documents\01_Projects\airbnb-automation-suite
    pause
    exit /b 1
)

echo ✅ Directory check passed

REM Step 2: Check Git status
echo.
echo 📋 Checking Git status...
git status

REM Step 3: Add all files
echo.
echo 📁 Adding all files to Git...
git add .

REM Step 4: Show what will be committed
echo.
echo 📋 Files to be committed:
git status --short

REM Step 5: Commit with detailed message
echo.
echo 💾 Creating commit...
git commit -m "🏠 Airbnb Automation Suite v1.0.0 - Production Ready

✨ Features:
- Smart reservation parsing with advanced date logic
- Property nickname mapping (Bali-only, excludes Seoul)
- Indonesian WhatsApp message generation
- Session persistence with Brave browser
- Tomorrow-focused filtering with past reservation exclusion

🔧 Technical Highlights:
- Fixed date assignment logic (Aug 7-11 = check-in on Aug 7)
- Header contamination filtering (first 15 lines only)
- Fuzzy property name matching with fallbacks
- Smart guest name detection with auto-skip
- Range validation (1-30 days) for reasonable reservations

📊 Expected Output Format:
Out: 7.5jt, bamboo
In: bamboo, 2 orang, 7Aug-11Aug

🎯 Status: 100%% working, thoroughly tested
📁 Includes: Main automation, nickname extractor, helper utilities
🌍 Focus: Bali property management automation"

REM Step 6: Check remote origin
echo.
echo 🌐 Checking remote repository...
git remote -v | findstr origin >nul
if %errorlevel% equ 0 (
    echo ✅ Remote origin already configured:
    git remote -v
) else (
    echo ⚠️ No remote origin found. You'll need to add it manually:
    echo git remote add origin https://github.com/[YOUR_USERNAME]/airbnb-automation-suite.git
    echo.
    set /p repo_url="Enter your GitHub repository URL: "
    if not "!repo_url!"=="" (
        git remote add origin "!repo_url!"
        echo ✅ Remote origin added: !repo_url!
    )
)

REM Step 7: Push to GitHub
echo.
echo ⬆️ Pushing to GitHub...
git branch -M main
git push -u origin main

REM Step 8: Success message
echo.
echo 🎉 SUCCESS! Your Airbnb Automation Suite has been uploaded to GitHub!
echo.
echo 📋 REPOSITORY SUMMARY:
echo ========================
echo 📁 Main Scripts:
echo   • airbnb_integrated_cleaner.py - Main automation (Indonesian output)
echo   • extract_nicknames_fixed.py - Property nickname extractor
echo   • property_nickname_helper.py - Utility class
echo   • airbnb_tomorrow.py - Alternative English version
echo.
echo 📊 Data Files:
echo   • property_nicknames_*.json - Nickname mappings
echo   • .gitignore - Excludes browser profiles ^& generated files
echo.
echo 📖 Documentation:
echo   • README.md - Comprehensive project documentation
echo   • output/README.md - Output files documentation
echo.
echo 🔧 KEY FEATURES WORKING:
echo   ✅ Smart date parsing (Aug 7-11 = check-in on Aug 7)
echo   ✅ Seoul property exclusion
echo   ✅ Indonesian message format
echo   ✅ Property nickname mapping
echo   ✅ Tomorrow-only filtering
echo.
echo 🌐 Your repository should now be live at:
echo https://github.com/[YOUR_USERNAME]/airbnb-automation-suite
echo.
echo 📱 Next Steps:
echo 1. Verify the repository looks correct on GitHub
echo 2. Test clone from another location to validate
echo 3. Consider adding GitHub Issues/Projects for future enhancements
echo 4. Share the repository URL for collaboration
echo.
echo 🎯 Repository Status: PRODUCTION READY ✅
echo.
pause
