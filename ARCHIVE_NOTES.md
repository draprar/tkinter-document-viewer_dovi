ARCHIVE NOTES — tkinter-document-viewer_dovi
=========================================

Data archiwizacji: 2026-05-04

Krótki opis
----------
Lekki czytnik dokumentów (PDF/EPUB/MOBI) napisany w Python/Tkinter. Projekt
został przygotowany do archiwizacji: testy jednostkowe uruchamiają się w trybie
headless i istnieje wydzielony backend dokumentów (`document_backend.py`).

Jak odtworzyć środowisko (Windows - PowerShell)
------------------------------------------------
1) Utwórz i aktywuj wirtualne środowisko:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Zainstaluj zależności:

```powershell
pip install -r requirements.txt
```

3) (opcjonalnie) zainstaluj zależności rozszerzające funkcjonalność PDF/MOBI:

```powershell
pip install PyMuPDF mobi tkhtmlview
```

4) Uruchom aplikację:

```powershell
python main.py
```

5) Uruchom testy (headless):

```powershell
$env:HEADLESS='1'
python -m pytest -q
```

Znane ograniczenia / notatki
----------------------------
- Testy działają w trybie headless; pełne testy renderowania (obrazów) wymagają
  rzeczywistego środowiska z Tcl/Tk i PyMuPDF.
- Nie wszystkie dev narzędzia są spięte w jednym lockfile. Jeśli chcesz w pełni
  odtworzyć środowisko developerskie, rozważ wygenerowanie `requirements-dev.txt` lub
  lockfile (`poetry.lock` / `pip-tools`).
- Jeśli `pip-audit` zgłosi krytyczne podatności, rozważ aktualizację zależności
  lub dodanie ich do `ARCHIVE_NOTES.md` z instrukcją mitigacji.

Kontakt i prawa
---------------
Projekt licencjonowany na podstawie pliku `LICENSE` (MIT). Autor: Walery
([@draprar](https://github.com/draprar/)).

