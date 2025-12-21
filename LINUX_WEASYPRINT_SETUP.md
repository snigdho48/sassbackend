# WeasyPrint Linux Installation Guide

Based on official WeasyPrint documentation: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#linux

## Quick Installation (Using Package Manager)

WeasyPrint is available in most Linux distributions' package managers. This is the easiest method:

### Debian ≥ 11 / Ubuntu ≥ 20.04
```bash
sudo apt install weasyprint
```

### Fedora ≥ 39
```bash
sudo dnf install weasyprint
```

### Archlinux
```bash
sudo pacman -S python-weasyprint
```

### Alpine ≥ 3.17
```bash
sudo apk add weasyprint
```

## Installation in Virtual Environment (Recommended for Development)

If you want to install WeasyPrint in a Python virtual environment (recommended for Django projects), follow these steps:

### Step 1: Verify Python and Pango Versions

WeasyPrint requires:
- Python ≥ 3.10.0
- Pango ≥ 1.44.0

Check versions:
```bash
python3 --version
pango-view --version
```

If Pango version is too old, you may need to update your system or use WeasyPrint version 52.5 which doesn't require recent Pango features.

### Step 2: Install System Dependencies

#### Debian ≥ 11 / Ubuntu ≥ 20.04

**For virtualenv with wheels (recommended):**
```bash
sudo apt install python3-pip libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 libharfbuzz-subset0
```

**For virtualenv without wheels (if wheels don't work):**
```bash
sudo apt install python3-pip libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 libharfbuzz-subset0 libffi-dev libjpeg-dev libopenjp2-7-dev
```

#### Fedora ≥ 39

**For virtualenv with wheels (recommended):**
```bash
sudo dnf install python-pip pango
```

**For virtualenv without wheels:**
```bash
sudo dnf install python3-pip pango gcc python3-devel gcc-c++ zlib-devel libjpeg-devel openjpeg2-devel libffi-devel
```

#### Archlinux

**For virtualenv with wheels (recommended):**
```bash
sudo pacman -S python-pip pango
```

**For virtualenv without wheels:**
```bash
sudo pacman -S python-pip pango gcc libjpeg-turbo openjpeg2
```

#### Alpine ≥ 3.17

**For virtualenv with wheels (recommended):**
```bash
sudo apk add py3-pip so:libgobject-2.0.so.0 so:libpango-1.0.so.0 so:libharfbuzz.so.0 so:libharfbuzz-subset.so.0 so:libfontconfig.so.1 so:libpangoft2-1.0.so.0
```

**For virtualenv without wheels:**
```bash
sudo apk add py3-pip so:libgobject-2.0.so.0 so:libpango-1.0.so.0 so:libharfbuzz.so.0 so:libharfbuzz-subset.so.0 so:libfontconfig.so.1 so:libpangoft2-1.0.so.0
sudo apk add gcc musl-dev python3-dev zlib-dev jpeg-dev openjpeg-dev libwebp-dev g++ libffi-dev
```

### Step 3: Create and Activate Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # For bash/zsh
# OR
source venv/bin/activate.fish  # For fish shell
```

### Step 4: Install WeasyPrint

```bash
# Install WeasyPrint
pip install weasyprint

# Verify installation
weasyprint --info
```

## Installation for Django Project

If you're installing for this Django project:

1. **Navigate to your project directory:**
   ```bash
   cd sassbackend
   ```

2. **Activate your virtual environment** (if using one):
   ```bash
   source venv/bin/activate  # Adjust path if different
   ```

3. **Install from requirements.txt:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation:**
   ```bash
   python manage.py shell
   >>> from weasyprint import HTML
   >>> print("WeasyPrint installed successfully!")
   ```

## Verify Installation

Test WeasyPrint installation:

```bash
# Check WeasyPrint version and dependencies
weasyprint --info

# Or test in Python
python3 -c "from weasyprint import HTML; print('WeasyPrint installed successfully!')"
```

## Troubleshooting

### Missing Libraries

If you get errors about missing libraries:

1. **Check which libraries are missing:**
   ```bash
   weasyprint --info
   ```

2. **Install missing system packages** based on your distribution (see Step 2 above)

3. **Common missing libraries:**
   - `libpango-1.0-0` - Pango text layout library
   - `libharfbuzz0b` - HarfBuzz text shaping engine
   - `libpangoft2-1.0-0` - Pango FreeType font backend

### Old Pango Version

If your distribution has an old Pango version (< 1.44.0):

- **Option 1**: Update your system packages
- **Option 2**: Use WeasyPrint version 52.5 which works with older Pango:
  ```bash
  pip install weasyprint==52.5
  ```

### Font Issues

If no characters appear in PDFs or you see squares instead of letters:

1. **Install system fonts:**
   ```bash
   # Debian/Ubuntu
   sudo apt install fonts-dejavu fonts-liberation
   
   # Fedora
   sudo dnf install dejavu-fonts liberation-fonts
   
   # Archlinux
   sudo pacman -S ttf-dejavu ttf-liberation
   ```

2. **Or use @font-face in CSS** to explicitly reference fonts

### Permission Issues

If you get permission errors:

- Make sure you're using `sudo` for system package installation
- For virtual environments, you don't need sudo for pip installs
- Check file permissions on your project directory

## Production Deployment

For production servers:

1. **Install system dependencies** on the server
2. **Use virtual environment** to isolate dependencies
3. **Consider using Docker** for consistent environments
4. **Test PDF generation** before deploying

## Additional Resources

- Official WeasyPrint Documentation: https://doc.courtbouillon.org/weasyprint/stable/
- WeasyPrint GitHub: https://github.com/Kozea/WeasyPrint
- Issue Tracker: https://github.com/Kozea/WeasyPrint/issues

