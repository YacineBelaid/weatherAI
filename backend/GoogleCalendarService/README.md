# Google Calendar Service

Service d'intégration Google Calendar API pour Weather AI.

## Configuration avec API Key (Recommandé)

### 1. Créer un projet Google Cloud

1. Allez sur [Google Cloud Console](https://console.developers.google.com/)
2. Créez un nouveau projet ou sélectionnez un projet existant
3. Activez l'API Google Calendar

### 2. Créer une API Key

1. Dans la console Google Cloud, allez dans "APIs & Services" > "Credentials"
2. Cliquez sur "Create Credentials" > "API Key"
3. Copiez l'API key générée

### 3. Configurer l'API Key

**Option A - Variable d'environnement :**

```bash
set GOOGLE_API_KEY=your_actual_api_key_here
```

**Option B - Fichier .env :**

```bash
echo GOOGLE_API_KEY=your_actual_api_key_here > .env
```

## Utilisation

### Démarrer le service

```bash
python backend/GoogleCalendarService/app.py
```

Le service sera disponible sur `http://localhost:8005`

## Endpoints Google Calendar API

### GET /health

Vérifie l'état du service et la configuration de l'API key.

### GET /calendars

Liste tous les calendriers publics accessibles.

### GET /calendars/{calendar_id}

Récupère un calendrier spécifique.

### GET /calendars/{calendar_id}/events

Liste les événements d'un calendrier public.

**Paramètres:**

- `time_min`: Date/heure de début (ISO 8601)
- `time_max`: Date/heure de fin (ISO 8601)
- `max_results`: Nombre maximum d'événements (défaut: 10)

### GET /calendars/{calendar_id}/events/{event_id}

Récupère un événement spécifique.

### POST /calendars/{calendar_id}/events

Crée un nouvel événement (nécessite OAuth pour les calendriers privés).

### PUT /calendars/{calendar_id}/events/{event_id}

Met à jour un événement existant (nécessite OAuth pour les calendriers privés).

### DELETE /calendars/{calendar_id}/events/{event_id}

Supprime un événement (nécessite OAuth pour les calendriers privés).

### POST /freebusy

Récupère les informations de disponibilité.

### GET /settings

Récupère les paramètres du calendrier.

## Variables d'environnement

- `GOOGLE_API_KEY`: Votre clé API Google Calendar

## Test

```bash
python test_google_calendar.py
```

## Limitations

- L'API key permet d'accéder aux calendriers publics uniquement
- Pour les calendriers privés, OAuth 2.0 est nécessaire
- Certaines opérations (créer/modifier/supprimer) nécessitent OAuth

## Dépannage

### Erreur "API key not configured"

- Vérifiez que `GOOGLE_API_KEY` est définie
- Vérifiez que l'API key est valide

### Erreur "API key not valid"

- Vérifiez que l'API Google Calendar est activée
- Vérifiez que l'API key a les bonnes permissions
