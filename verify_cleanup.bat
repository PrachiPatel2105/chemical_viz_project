@echo off
echo ========================================
echo Project Cleanup Verification
echo ========================================
echo.

echo Checking for cleaned files...
echo.

echo [1/5] Checking if duplicate CSVs are removed...
if exist "large_sample_equipment_data.csv" (
    echo ❌ FAIL: large_sample_equipment_data.csv still exists
) else (
    echo ✓ PASS: Duplicate CSV removed
)

if exist "media\4_sample_equipment_data.csv" (
    echo ❌ FAIL: media\4_sample_equipment_data.csv still exists
) else (
    echo ✓ PASS: Media CSV files cleaned
)

echo.
echo [2/5] Checking if sample data exists...
if exist "sample_equipment_data.csv" (
    echo ✓ PASS: Main sample data present
) else (
    echo ❌ FAIL: sample_equipment_data.csv missing
)

echo.
echo [3/5] Checking if .gitignore exists...
if exist ".gitignore" (
    echo ✓ PASS: .gitignore file created
) else (
    echo ❌ FAIL: .gitignore missing
)

echo.
echo [4/5] Checking if upload script exists...
if exist "upload_to_github.bat" (
    echo ✓ PASS: Upload script ready
) else (
    echo ❌ FAIL: Upload script missing
)

echo.
echo [5/5] Checking if documentation exists...
if exist "README.md" (
    echo ✓ PASS: README.md present
) else (
    echo ❌ FAIL: README.md missing
)

echo.
echo ========================================
echo Verification Complete!
echo ========================================
echo.
echo If all checks passed, you're ready to upload!
echo Run: upload_to_github.bat
echo.
pause
