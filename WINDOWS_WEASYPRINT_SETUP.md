# WeasyPrint Windows Installation Guide

Based on official WeasyPrint documentation: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows

## Official Installation Steps (Recommended)

1. **Install Python** from the Microsoft Store:
   - https://apps.microsoft.com/store/search/python
   - Install the latest version

2. **Install MSYS2**:
   - Download from: https://www.msys2.org/#installation
   - Keep the default options during installation

3. **Install Pango in MSYS2**:
   - Open MSYS2's shell (not regular Windows terminal)
   - Run: `pacman -S mingw-w64-x86_64-pango`
   - Close MSYS2's shell

4. **Install WeasyPrint**:
   - Open Windows Command Prompt (cmd.exe)
   - Activate your virtual environment (if using one)
   - Run: `python3 -m pip install weasyprint`
   - Test: `python3 -m weasyprint --info`

## Setting DLL Directory (If Libraries Not Found)

If you get "cannot load library" errors, set the `WEASYPRINT_DLL_DIRECTORIES` environment variable:

### In Command Prompt (cmd.exe):
```cmd
set WEASYPRINT_DLL_DIRECTORIES=C:\msys64\mingw64\bin
```

### In PowerShell:
```powershell
$env:WEASYPRINT_DLL_DIRECTORIES="C:\msys64\mingw64\bin"
```

### Permanently (Windows):
1. Open System Properties → Environment Variables
2. Add new System Variable:
   - Name: `WEASYPRINT_DLL_DIRECTORIES`
   - Value: `C:\msys64\mingw64\bin` (adjust path if MSYS2 installed elsewhere)
3. Restart your terminal/IDE

### In Django Settings (Alternative):
You can also set this in your Django settings or before importing WeasyPrint:
```python
import os
os.environ['WEASYPRINT_DLL_DIRECTORIES'] = r'C:\msys64\mingw64\bin'
```

## Verify Installation

Test with:
```bash
python -c "from weasyprint import HTML; print('WeasyPrint installed successfully!')"
```

## Alternative: Using WSL

If MSYS2 installation is problematic, you can use WSL (Windows Subsystem for Linux) and install WeasyPrint the same way as on Linux.

## Troubleshooting

- Make sure MSYS2 is installed to the default location (`C:\msys64`)
- If installed elsewhere, adjust the path in `WEASYPRINT_DLL_DIRECTORIES`
- Verify DLL files exist: Check that `C:\msys64\mingw64\bin\libgobject-2.0-0.dll` exists
- Restart your terminal/IDE after setting environment variables

