# Madrid Restaurant Picker API

API web en FastAPI para filtrar restaurantes por:
- precio
- tipo de cocina
- zona de Madrid
- visitado / no visitado
- ocasión

Incluye una mini interfaz web y una base SQLite inicial.

## Filosofía de clasificación

### 1) Precio
- `economico`: 0–20 €
- `medio`: 21–40 €
- `alto`: 41–70 €
- `muy_alto`: 71 €+

### 2) Zonas de Madrid capital
Se usan los 21 distritos oficiales del Ayuntamiento de Madrid.

### 3) Comunidad de Madrid
Se simplifica en macrozonas útiles para decisión gastronómica:
- Madrid capital
- Norte metropolitano
- Oeste metropolitano
- Este metropolitano
- Sur metropolitano
- Sierra Norte
- Sierra Oeste
- Cuenca del Henares
- Las Vegas / Sureste

### 4) Cocina
Agrupaciones deliberadamente no hiperespecíficas:
- Española
- Italiana
- Mexicana
- Japonesa
- China
- Asiática
- Mediterránea
- Peruana
- India
- Coreana
- Americana / Hamburguesas
- Brasa / Carnes
- Marisquería / Pescado
- Tapas / Taberna
- Fusión
- Vegetariana / Vegana
- Internacional
- Árabe / Oriente Medio

## Ejecutar en local

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abre:
- API docs: `http://127.0.0.1:8000/docs`
- Web: `http://127.0.0.1:8000/`

## Endpoints principales

- `GET /meta`
- `GET /restaurants`
- `POST /restaurants`
- `PATCH /restaurants/{id}/visited`
- `GET /recommendation`

## Despliegue

### Render
1. Sube este proyecto a GitHub.
2. Crea un nuevo Web Service en Render.
3. Usa Docker.
4. Deploy.

### Railway
1. Sube a GitHub.
2. New Project -> Deploy from GitHub.
3. Railway detectará Dockerfile.

## Siguiente paso recomendado

Conectar esta API a un CSV o Google Sheet propio con tus restaurantes reales, para que la app deje de ser demo y pase a ser tu guía personal de Madrid.
