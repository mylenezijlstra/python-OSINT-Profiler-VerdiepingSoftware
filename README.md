# python-OSINT-Profiler-VerdiepingSoftware

A Python-based OSINT profiling tool developed for Verdieping Software, focused on gathering, analyzing, and structuring publicly available intelligence data.

# trello 
https://trello.com/b/5PaWx7qK/verdieping-software

## Hoe runnen

### Vereisten

- Python 3.x geïnstalleerd ([python.org](https://www.python.org/downloads/))
- De volgende Python packages:

```bash
pip install streamlit httpx pandas cryptography
```

### Starten

```bash
C:\Users\mylen\AppData\Local\Python\bin\python.exe -m streamlit run profiler_app.py
```

Of als `python` wel in je PATH staat:

```bash
python -m streamlit run profiler_app.py
```

### Openen

Na het starten opent de app automatisch in je browser, of ga zelf naar:

```
http://localhost:8501
```

## Beveiliging & Privacy (Nieuw)

De applicatie slaat profielen veilig op om de privacy van gezochte personen te garanderen:
1. **Toegangscontrole (Master Password)**: Bij de eerste opstart wordt er gevraagd om een Master Password in te stellen. Dit wachtwoord beveiligt de toegang tot de scanner en historie.
2. **AES-256 Data Encryptie**: Alle opgeslagen profielgegevens en platformkoppelingen worden lokaal versleuteld in de SQLite database (`profiles.db`). De sleutel wordt bij het inloggen in-memory afgeleid van het Master Password via PBKDF2. Offline is de database onleesbaar zonder het juiste wachtwoord.

