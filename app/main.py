from __future__ import annotations

from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "restaurants.db"
STATIC_DIR = BASE_DIR / "app" / "static"

app = FastAPI(
    title="Madrid Restaurant Picker API",
    description="API y mini interfaz web para elegir restaurantes en Madrid por precio, cocina, zona y visitado.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


PRICE_BUCKETS = [
    {"code": "economico", "label": "€ · Económico", "min_avg_ticket": 0, "max_avg_ticket": 20},
    {"code": "medio", "label": "€€ · Medio", "min_avg_ticket": 21, "max_avg_ticket": 40},
    {"code": "alto", "label": "€€€ · Alto", "min_avg_ticket": 41, "max_avg_ticket": 70},
    {"code": "muy_alto", "label": "€€€€ · Muy alto", "min_avg_ticket": 71, "max_avg_ticket": 999},
]

MADRID_CITY_ZONES = [
    "Centro",
    "Salamanca",
    "Chamberí",
    "Chamartín",
    "Retiro",
    "Tetuán",
    "Arganzuela",
    "Moncloa-Aravaca",
    "Latina",
    "Usera",
    "Carabanchel",
    "Fuencarral-El Pardo",
    "Hortaleza",
    "Ciudad Lineal",
    "San Blas-Canillejas",
    "Puente de Vallecas",
    "Villa de Vallecas",
    "Moratalaz",
    "Vicálvaro",
    "Villaverde",
    "Barajas",
]

COMMUNITY_ZONES = [
    "Madrid capital",
    "Norte metropolitano",
    "Oeste metropolitano",
    "Este metropolitano",
    "Sur metropolitano",
    "Sierra Norte",
    "Sierra Oeste",
    "Cuenca del Henares",
    "Las Vegas / Sureste",
]

CUISINE_GROUPS = [
    "Española",
    "Italiana",
    "Mexicana",
    "Japonesa",
    "China",
    "Asiática",
    "Mediterránea",
    "Peruana",
    "India",
    "Coreana",
    "Americana / Hamburguesas",
    "Brasa / Carnes",
    "Marisquería / Pescado",
    "Tapas / Taberna",
    "Fusión",
    "Vegetariana / Vegana",
    "Internacional",
    "Árabe / Oriente Medio",
]

OCCASIONS = [
    "Diario",
    "Cita",
    "Con amigos",
    "Negocios",
    "Celebración",
    "Turistas",
]


class RestaurantCreate(BaseModel):
    name: str = Field(min_length=2)
    neighborhood: str
    madrid_zone: str
    community_zone: str
    cuisine_group: str
    price_bucket: str
    avg_ticket_eur: int = Field(ge=0)
    visited: bool = False
    notes: Optional[str] = None
    vibe: Optional[str] = None
    critic_score: Optional[float] = Field(default=None, ge=0, le=10)
    occasion: Optional[str] = None


class RestaurantUpdateVisited(BaseModel):
    visited: bool


class RestaurantOut(BaseModel):
    id: int
    name: str
    neighborhood: str
    madrid_zone: str
    community_zone: str
    cuisine_group: str
    price_bucket: str
    avg_ticket_eur: int
    visited: bool
    notes: Optional[str] = None
    vibe: Optional[str] = None
    critic_score: Optional[float] = None
    occasion: Optional[str] = None


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS restaurants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                neighborhood TEXT NOT NULL,
                madrid_zone TEXT NOT NULL,
                community_zone TEXT NOT NULL,
                cuisine_group TEXT NOT NULL,
                price_bucket TEXT NOT NULL,
                avg_ticket_eur INTEGER NOT NULL,
                visited INTEGER NOT NULL DEFAULT 0,
                notes TEXT,
                vibe TEXT,
                critic_score REAL,
                occasion TEXT
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) AS n FROM restaurants").fetchone()["n"]
        if count == 0:
            seed_rows = [
                ("Casa Gran Vía", "Sol", "Centro", "Madrid capital", "Española", "medio", 32, 0, "Buena opción castiza de inicio.", "clásico", 7.8, "Turistas"),
                ("Bistró Retiro 28", "Ibiza", "Retiro", "Madrid capital", "Mediterránea", "alto", 48, 1, "Más fino que pretencioso.", "elegante", 8.4, "Cita"),
                ("Pasta Chamberí", "Trafalgar", "Chamberí", "Madrid capital", "Italiana", "medio", 29, 0, "Funciona muy bien para comida informal.", "animado", 7.6, "Con amigos"),
                ("Fuego Salamanca", "Recoletos", "Salamanca", "Madrid capital", "Brasa / Carnes", "muy_alto", 95, 0, "Ticket alto, experiencia potente.", "lujo", 8.8, "Celebración"),
                ("Mercado Usera", "Moscardó", "Usera", "Madrid capital", "Asiática", "economico", 17, 1, "Mucho sabor, poca tontería.", "casual", 8.1, "Diario"),
                ("Taquería Río", "Legazpi", "Arganzuela", "Madrid capital", "Mexicana", "medio", 24, 0, "Perfil fresco y compartible.", "informal", 7.9, "Con amigos"),
                ("Umami Tetuán", "Cuatro Caminos", "Tetuán", "Madrid capital", "Japonesa", "alto", 52, 0, "Pensado para producto y barra.", "moderno", 8.5, "Cita"),
                ("Huerta Verde", "Prosperidad", "Chamartín", "Madrid capital", "Vegetariana / Vegana", "medio", 27, 0, "Cocina vegetal seria, no de relleno.", "luminoso", 8.0, "Diario")
            ]
            conn.executemany(
                """
                INSERT INTO restaurants (
                    name, neighborhood, madrid_zone, community_zone, cuisine_group,
                    price_bucket, avg_ticket_eur, visited, notes, vibe, critic_score, occasion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                seed_rows,
            )
        conn.commit()


@app.on_event("startup")
def startup_event() -> None:
    init_db()


@app.get("/")
def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/meta")
def meta() -> dict:
    return {
        "price_buckets": PRICE_BUCKETS,
        "madrid_city_zones": MADRID_CITY_ZONES,
        "community_zones": COMMUNITY_ZONES,
        "cuisine_groups": CUISINE_GROUPS,
        "occasions": OCCASIONS,
        "principles": {
            "price": "Agrupar por ticket medio real y no por lujo percibido.",
            "zone": "Separar Madrid capital por distritos y Comunidad por macrozonas útiles para decidir desplazamientos.",
            "cuisine": "Evitar etiquetas hiperespecíficas y mantener familias de cocina comparables.",
        },
    }


@app.get("/restaurants", response_model=List[RestaurantOut])
def list_restaurants(
    price_bucket: Optional[str] = None,
    cuisine_group: Optional[str] = None,
    madrid_zone: Optional[str] = None,
    community_zone: Optional[str] = None,
    neighborhood: Optional[str] = None,
    visited: Optional[bool] = Query(default=None),
    min_score: Optional[float] = Query(default=None, ge=0, le=10),
    occasion: Optional[str] = None,
    q: Optional[str] = None,
    sort_by: str = Query(default="critic_score"),
    sort_dir: str = Query(default="desc"),
):
    allowed_sort_fields = {"critic_score", "avg_ticket_eur", "name"}
    if sort_by not in allowed_sort_fields:
        raise HTTPException(status_code=400, detail=f"sort_by debe ser uno de {sorted(allowed_sort_fields)}")
    if sort_dir not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="sort_dir debe ser asc o desc")

    sql = "SELECT * FROM restaurants WHERE 1=1"
    params: list = []

    filters = {
        "price_bucket": price_bucket,
        "cuisine_group": cuisine_group,
        "madrid_zone": madrid_zone,
        "community_zone": community_zone,
        "neighborhood": neighborhood,
        "occasion": occasion,
    }
    for field, value in filters.items():
        if value is not None:
            sql += f" AND {field} = ?"
            params.append(value)

    if visited is not None:
        sql += " AND visited = ?"
        params.append(1 if visited else 0)

    if min_score is not None:
        sql += " AND critic_score >= ?"
        params.append(min_score)

    if q:
        sql += " AND (name LIKE ? OR notes LIKE ? OR neighborhood LIKE ?)"
        like_q = f"%{q}%"
        params.extend([like_q, like_q, like_q])

    sql += f" ORDER BY {sort_by} {sort_dir.upper()}, name ASC"

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [RestaurantOut(**dict(row), visited=bool(row["visited"])) for row in rows]


@app.post("/restaurants", response_model=RestaurantOut, status_code=201)
def create_restaurant(payload: RestaurantCreate):
    if payload.madrid_zone not in MADRID_CITY_ZONES:
        raise HTTPException(status_code=400, detail="madrid_zone no válida")
    if payload.community_zone not in COMMUNITY_ZONES:
        raise HTTPException(status_code=400, detail="community_zone no válida")
    if payload.cuisine_group not in CUISINE_GROUPS:
        raise HTTPException(status_code=400, detail="cuisine_group no válida")
    if payload.price_bucket not in {p['code'] for p in PRICE_BUCKETS}:
        raise HTTPException(status_code=400, detail="price_bucket no válida")
    if payload.occasion and payload.occasion not in OCCASIONS:
        raise HTTPException(status_code=400, detail="occasion no válida")

    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO restaurants (
                name, neighborhood, madrid_zone, community_zone, cuisine_group,
                price_bucket, avg_ticket_eur, visited, notes, vibe, critic_score, occasion
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.name, payload.neighborhood, payload.madrid_zone, payload.community_zone,
                payload.cuisine_group, payload.price_bucket, payload.avg_ticket_eur,
                1 if payload.visited else 0, payload.notes, payload.vibe,
                payload.critic_score, payload.occasion,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM restaurants WHERE id = ?", (cur.lastrowid,)).fetchone()
        return RestaurantOut(**dict(row), visited=bool(row["visited"]))


@app.patch("/restaurants/{restaurant_id}/visited", response_model=RestaurantOut)
def update_visited(restaurant_id: int, payload: RestaurantUpdateVisited):
    with get_conn() as conn:
        exists = conn.execute("SELECT * FROM restaurants WHERE id = ?", (restaurant_id,)).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Restaurante no encontrado")
        conn.execute("UPDATE restaurants SET visited = ? WHERE id = ?", (1 if payload.visited else 0, restaurant_id))
        conn.commit()
        row = conn.execute("SELECT * FROM restaurants WHERE id = ?", (restaurant_id,)).fetchone()
        return RestaurantOut(**dict(row), visited=bool(row["visited"]))


@app.get("/recommendation", response_model=Optional[RestaurantOut])
def recommendation(
    price_bucket: Optional[str] = None,
    cuisine_group: Optional[str] = None,
    madrid_zone: Optional[str] = None,
    visited: Optional[bool] = False,
    occasion: Optional[str] = None,
):
    sql = "SELECT * FROM restaurants WHERE 1=1"
    params: list = []
    if price_bucket:
        sql += " AND price_bucket = ?"
        params.append(price_bucket)
    if cuisine_group:
        sql += " AND cuisine_group = ?"
        params.append(cuisine_group)
    if madrid_zone:
        sql += " AND madrid_zone = ?"
        params.append(madrid_zone)
    if visited is not None:
        sql += " AND visited = ?"
        params.append(1 if visited else 0)
    if occasion:
        sql += " AND occasion = ?"
        params.append(occasion)
    sql += " ORDER BY critic_score DESC, avg_ticket_eur ASC LIMIT 1"

    with get_conn() as conn:
        row = conn.execute(sql, params).fetchone()
        if row is None:
            return None
        return RestaurantOut(**dict(row), visited=bool(row["visited"]))
