# Document Viewer (PDF, EPUB, MOBI) - DoVI

## Overview
A lightweight Python/Tkinter app for reading your docs in style.
Open PDFs, EPUBs, or MOBIs → zoom in, search text, flip pages, or go fullscreen. Clean, minimal, distraction-free.

![Screenshot](img/SS1.png)

## ✨ Features
- 📄 **Supports PDF, EPUB, and MOBI formats**
- 🔍 **Text search** with navigation through matches (PDF)
- 🔄 **Zoom in/out** for better readability
- ⏭️ **Navigation controls** (Next/Previous page, Go to page)
- 🖥️ **Fullscreen mode** for a distraction-free experience
- 🎨 **HTML rendering** for EPUB/MOBI for better formatting

## 🚀 Quickstart
### Clone the repository:
```bash
  git clone https://github.com/draprar/tkinter-document-viewer_dovi.git
  cd tkinter-document-viewer_dovi
```

### Create and activate virtual environment (recommended):
```bash
  python -m venv venv
  # On Windows:
  venv\Scripts\activate
  # On macOS/Linux:
  source venv/bin/activate
```

### Install Dependencies
```bash
  pip install -r requirements.txt
```

## Usage
Run the application:
```bash
  python main.py
```

## 🧪 Testy (headless)
W środowiskach bez GUI (CI lub serwery) testy można uruchomić w trybie headless.
Ustaw zmienną środowiskową `HEADLESS` przed uruchomieniem pytest:

PowerShell:
```powershell
$env:HEADLESS='1'
python -m pytest -q
```

Albo uruchom z coverage:
```powershell
$env:HEADLESS='1'
python -m pytest --cov=./ -q
```

Testy jednostkowe zostały dostosowane do pracy bez rzeczywistego widgetu Tk.

## ⚠️ Wymagania opcjonalne
Niektóre funkcje wymagają dodatkowych bibliotek, które nie są konieczne do
uruchomienia testów:

- PyMuPDF (`fitz`) — wymagane do otwierania i renderowania plików PDF
- `mobi` — opcjonalne wsparcie dla MOBI
- `tkhtmlview` — renderowanie HTML w niektórych trybach EPUB/MOBI

Zainstaluj je tylko gdy chcesz używać tych funkcji:
```powershell
pip install PyMuPDF mobi tkhtmlview
```

### Keyboard Shortcuts
- **Ctrl + Mouse Wheel**: Zoom in/out
- **Mouse Wheel**: Navigate pages
- **Escape**: Exit fullscreen

## ⚙️ CI/CD
Automated testing with GitHub Actions (runs on every push & PR).

## 📜 License
This project is licensed under the MIT License.

## 👤 Credits
- **Built by**: Walery ([@draprar](https://github.com/draprar/))
