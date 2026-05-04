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

## Audyt zależności (pip-audit)

W środowisku developerskim uruchomiłem `pip-audit` i narzędzie wykryło kilka
znanych podatności w pakietach zainstalowanych w lokalnym venv (część z nich
to narzędzia developerskie). Pełne skanowanie należy wykonać na czystym
środowisku po zainstalowaniu tylko produkcyjnych zależności (`requirements.txt`).

Krótka lista podatnych pakietów znalezionych w moim środowisku (przykładowe
zalecane wersje naprawcze):

- Pillow 10.4.0 -> zaktualizować do >= 12.2.0 (naprawia CVE-2026-25990 / 2026-40192)
- pytest 8.3.4 -> zaktualizować do 9.0.3 (jeśli używasz w środowisku developerskim)
- urllib3 2.3.0 -> zaktualizować do >= 2.6.3 (wiele CVE związanych z dekodowaniem)
- requests 2.32.3 -> zaktualizować do 2.32.4 / 2.33.0
- lxml 5.3.0 -> zaktualizować do >= 6.1.0
- filelock 3.17.0 -> zaktualizować do >= 3.20.3
- brotli 1.1.0 -> zaktualizować do >= 1.2.0
- cairosvg, fonttools i inne transitive -> rozważyć aktualizację do wersji naprawczych

Zalecenia praktyczne:

1. Oddziel zależności produkcyjne od developerskich (zrobione: dodano
   `requirements-dev.txt`). Przy archiwizacji umieść w `requirements.txt` tylko
   runtime deps i sprawdź je w czystym venv:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pip_audit
```

2. Jeśli pip-audit wykryje krytyczne podatności w zależnościach produkcyjnych —
   zaktualizuj je do podanych wersji lub dodaj notatkę do `ARCHIVE_NOTES.md` z
   instrukcją mitigacji.

3. Narzędzia developerskie (black, flake8 itp.) należy instalować z
   `requirements-dev.txt` tylko lokalnie. Dla archiwizacji nie ma potrzeby
   instalowania ich w środowisku produkcyjnym.

Jeśli chcesz, mogę:

- (A) uruchomić pip-audit na *czystym* środowisku zainstalowanym tylko z
  `requirements.txt` i przygotować listę remediacji dla produkcyjnych pakietów, lub
- (B) przygotować sugestie konkretnych wersji (patches) do wpisania w
  `requirements.txt`/`constraints.txt` aby wyeliminować krytyczne CVE.


