from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(title="Movie Ticket Booking System 🎬")

# ✅ CORS FIX (IMPORTANT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Fake Databases
# -----------------------------
movies = []
theaters = []
shows = []
bookings = []

# -----------------------------
# Schemas
# -----------------------------
class Movie(BaseModel):
    title: str = Field(..., min_length=1)
    genre: str
    rating: float = Field(..., ge=0, le=10)

class Theater(BaseModel):
    name: str
    location: str

class Show(BaseModel):
    movie_id: int
    theater_id: int
    time: str

class Booking(BaseModel):
    show_id: int
    user_name: str
    seats: List[int]

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def find_item(data, item_id):
    for item in data:
        if item["id"] == item_id:
            return item
    return None

def is_seat_available(show_id, seats):
    booked = []
    for b in bookings:
        if b["show_id"] == show_id:
            booked.extend(b["seats"])
    return all(seat not in booked for seat in seats)

# -----------------------------
# MOVIE APIs
# -----------------------------
@app.post("/movies")
def add_movie(movie: Movie):
    new = movie.dict()
    new["id"] = len(movies) + 1
    movies.append(new)
    return new

@app.get("/movies")
def get_movies(search: str = "", page: int = 1, limit: int = 5):
    data = [m for m in movies if search.lower() in m["title"].lower()]
    start = (page - 1) * limit
    return data[start:start + limit]

@app.get("/movies/{movie_id}")
def get_movie(movie_id: int):
    movie = find_item(movies, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")
    return movie

@app.put("/movies/{movie_id}")
def update_movie(movie_id: int, updated: Movie):
    movie = find_item(movies, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")
    movie.update(updated.dict())
    return movie

@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int):
    movie = find_item(movies, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")
    movies.remove(movie)
    return {"message": "Deleted"}

# -----------------------------
# THEATER APIs
# -----------------------------
@app.post("/theaters")
def add_theater(theater: Theater):
    new = theater.dict()
    new["id"] = len(theaters) + 1
    theaters.append(new)
    return new

@app.get("/theaters")
def get_theaters():
    return theaters

@app.get("/theaters/{theater_id}")
def get_theater(theater_id: int):
    theater = find_item(theaters, theater_id)
    if not theater:
        raise HTTPException(404, "Theater not found")
    return theater

# -----------------------------
# SHOW APIs
# -----------------------------
@app.post("/shows")
def add_show(show: Show):
    if not find_item(movies, show.movie_id):
        raise HTTPException(404, "Movie not found")
    if not find_item(theaters, show.theater_id):
        raise HTTPException(404, "Theater not found")

    new = show.dict()
    new["id"] = len(shows) + 1
    shows.append(new)
    return new

@app.get("/shows")
def get_shows(movie_id: Optional[int] = None):
    if movie_id:
        return [s for s in shows if s["movie_id"] == movie_id]
    return shows

@app.get("/shows/{show_id}")
def get_show(show_id: int):
    show = find_item(shows, show_id)
    if not show:
        raise HTTPException(404, "Show not found")
    return show

@app.delete("/shows/{show_id}")
def delete_show(show_id: int):
    show = find_item(shows, show_id)
    if not show:
        raise HTTPException(404, "Show not found")
    shows.remove(show)
    return {"message": "Show deleted"}

# -----------------------------
# BOOKING APIs
# -----------------------------
@app.post("/bookings")
def create_booking(booking: Booking):
    if not find_item(shows, booking.show_id):
        raise HTTPException(404, "Show not found")

    if not is_seat_available(booking.show_id, booking.seats):
        raise HTTPException(400, "Seats already booked")

    new = booking.dict()
    new["id"] = len(bookings) + 1
    bookings.append(new)
    return new

@app.get("/bookings")
def get_bookings():
    return bookings

@app.get("/bookings/{booking_id}")
def get_booking(booking_id: int):
    booking = find_item(bookings, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")
    return booking

@app.get("/users/{user_name}/bookings")
def get_user_bookings(user_name: str):
    return [b for b in bookings if b["user_name"].lower() == user_name.lower()]

@app.delete("/bookings/{booking_id}")
def cancel_booking(booking_id: int):
    booking = find_item(bookings, booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")
    bookings.remove(booking)
    return {"message": "Cancelled"}

# -----------------------------
# ADVANCED APIs
# -----------------------------
@app.get("/shows/{show_id}/seats")
def check_seats(show_id: int):
    booked = []
    for b in bookings:
        if b["show_id"] == show_id:
            booked.extend(b["seats"])
    return {"booked_seats": booked}

@app.get("/analytics/revenue")
def revenue():
    return {
        "total_bookings": len(bookings),
        "total_revenue": len(bookings) * 200
    }

@app.get("/search")
def global_search(query: str = Query(...)):
    return {
        "movies": [m for m in movies if query.lower() in m["title"].lower()],
        "theaters": [t for t in theaters if query.lower() in t["name"].lower()]
    }