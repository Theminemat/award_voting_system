# Awards Voting System

A modern **Django-based voting system** designed for award-style votings (e.g., *Who's the funniest?*).  
It features **sequential mandatory voting** across multiple categories, a full **admin panel**,  
**code-based access**, and **real-time result evaluation**.  
The system also supports **automatic email distribution of voting codes** to participants.

## Features

- ✅ **Adjustable Names**: Name list can be visually managed in the admin area  
- ✅ **Adjustable Categories**: Categories can be visually managed in the admin area  
- ✅ **Sequential Voting**: Users must go through **all** categories one after another  
- ✅ **Dropdown Selection**: Person selection via dropdown menu (sorted alphabetically by first name)  
- ✅ **Mandatory Voting**: A vote is only valid if **all** categories have been completed  
- ✅ **Admin-Generated Codes**: Voting codes with configurable number of uses per code  
- ✅ **URL Parameter Support**: Codes can be passed via URL parameters  
- ✅ **Responsive Design**: Works on both desktop and mobile devices  
- ✅ **Admin Results**: Top 5 per category with vote counts and percentages  
- ✅ **Live Submission Counter**: Real-time submission count for display on a big screen  
- ✅ **Progress Indicator**: Visual progress through all categories  
- ✅ **Security**: CSRF protection and validation


## Voting Process

### Sequential Mandatory Voting
- **All categories must be completed** – skipping is not allowed  
- **Step-by-step navigation** through all available categories  
- **Progress bar** shows current step (e.g., "Step 3 of 7")  
- **Votes are only saved at the end** – no partial submissions

### Dropdown Person Selection
- **Alphabetical sorting by first name** (Anna, David, Emma, Felix...)  
- **Dropdown menu** for a simple and intuitive selection (instead of checkboxes)  
- **Selection required** – button is only active after a person is selected  
- **User-friendly interface** with auto-focus and input validation

## Technical Details

- **Framework**: Django 5.2.3  
- **Database**: SQLite (default), PostgreSQL/MySQL supported  
- **Frontend**: Bootstrap 5.1.3, Font Awesome 6.0  
- **Python**: 3.11+
- **Mailservice** : Mailgun (you can create a free account there.)

## Installation

### 1. Voraussetzungen

```bash
# Python 3.11+ installieren
# pip installieren
```

### 2. Projekt klonen/herunterladen

```bash
# Projekt-Dateien in gewünschtes Verzeichnis kopieren
cd voting_system
```

### 3. Abhängigkeiten installieren

```bash
pip install django pillow
```

### 4. Datenbank einrichten

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Admin-Benutzer erstellen

```bash
python manage.py createsuperuser
```

### 6. Server starten

```bash
python manage.py runserver
```

Die Anwendung ist dann unter `http://localhost:8000` erreichbar.

## Erste Schritte

### 1. Admin-Panel aufrufen

- Gehe zu `http://localhost:8000/admin/`
- Melde dich mit dem erstellten Admin-Account an

### 2. Personen hinzufügen

- Im Admin-Panel: **Voting** → **Persons** → **Hinzufügen**
- Füge die Namen der Klassenmitglieder hinzu

### 3. Kategorien erstellen

- Im Admin-Panel: **Voting** → **Categories** → **Hinzufügen**
- Erstelle Abstimmungskategorien (z.B. "Klassensprecher/in", "Lustigste Person")
- Optional: Füge Bilder zu den Kategorien hinzu

### 4. Voting-Codes generieren

**Best method to generate voting codes:**

Go to /send-codes (you need to login at /admin first), enter the Emails of the participants and click on "Send Codes". To send them via Mailgun an one time code to the Vote.

**Manual Code Generation:**
- Im Admin-Panel: **Voting** → **Voting codes** → **Ändern**
- Wähle die Aktion "10 neue Codes generieren" und klicke "Ausführen"
- Die generierten Codes werden angezeigt

### 5. Abstimmung durchführen

- Hauptseite: `http://localhost:8000/`
- Voting-Seite: `http://localhost:8000/vote/`
- Mit Code-Parameter: `http://localhost:8000/vote/DEIN-CODE/`

### 6. Ergebnisse anzeigen

- Ergebnisse (nur für Admins): `http://localhost:8000/results/`
- Ergebnisse (live Counter Angabenanzahl): `http://localhost:8000/live-results/`

## URL-Struktur

| URL              | Beschreibung                         |
|------------------|--------------------------------------|
| `/`              | Startseite mit Anleitung             |
| `/vote/`         | Voting-Interface (Code-Eingabe)      |
| `/vote/<code>/`  | Direkter Zugang mit Code             |
| `/results/`      | Admin-Ergebnisse (Login erforderlich) |
| `/live-results/` | Live Abgabencounter |
| `/admin/`        | Django Admin-Panel (Login erforderlich)                  |



# Deployment

## Production Settings

1.  **Disable DEBUG** in `settings.py`:
    ```python
    DEBUG = False
    ALLOWED_HOSTS = ['your-domain.com']
    ```

2.  **Generate a secure SECRET_KEY**:
    ```python
    SECRET_KEY = 'your-secure-secret-key-here'
    ```

3.  **Collect static files**:
    ```bash
    python manage.py collectstatic
    ```

4.  **Configure a production database** (PostgreSQL recommended):
    ```python
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'klassenabstimmung',
            'USER': 'your_user',
            'PASSWORD': 'your_password',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
    
4.  **(Optional) If you want to use the Email feature set you Mailgun credentials in settings.py:**
    ```python
    MAILGUN_API_KEY = '1234' # Your Mailgun API key, replace with your actual key
    MAILGUN_DOMAIN = 'example.com' # set your domain here, e.g. 'example.com' or 'example.eu'
    MAILGUN_API_URL = f'https://api.eu.mailgun.net/v3/{MAILGUN_DOMAIN}/messages' # the Api endpoint (no need to edit this unless you use a different region)
    MAILGUN_SENDER_EMAIL = f'Example <no-reply@{MAILGUN_DOMAIN}>' # The Name and email address that will appear as the sender in the emails
    MAILGUN_TEMPLATE_NAME = 'Example' # Name of your Mailgun template
    ```
    Make sure to create a Mailgun template that includes the variables `{{ vote_url }}` and `{{ voting_code }}` to display the voting code and the voting URL in the email.
    
    You can find an example Mailgun template to use here: 


It's recommended to set all credentials in an .env file and load them in settings.py using `os.environ.get('VARIABLE_NAME')`
## Web Server Setup

**With Gunicorn and Nginx:**

1.  Install Gunicorn:
    ```bash
    pip install gunicorn
    ```

2.  Start Gunicorn:
    ```bash
    gunicorn voting_system.wsgi:application --bind 0.0.0.0:8000
    ```

3.  Configure Nginx as a reverse proxy

# Customization

## Customizing the Design
-   Edit CSS in `voting/templates/voting/base.html`
-   Adjust Bootstrap classes in templates

## New Categories
-   Add via the Admin Panel
-   Optionally upload images

## Code Settings
-   Change `max_uses` in the `VotingCode` model
-   Adjust the code length in `generate_code()`

# Troubleshooting

## Common Issues

**Migration errors:**
```bash
python manage.py makemigrations voting
python manage.py migrate
```

**Static files not loading:**
```bash
python manage.py collectstatic --clear
```

**Forgot admin user:**
```bash
python manage.py createsuperuser
```

**Codes not working:**
-   Check if the code is active
-   Check the usage count
-   Check if a vote has already been cast



## Lizenz

This project is licensed under the MIT License