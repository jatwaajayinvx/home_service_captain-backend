from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.auth import router as auth_router
from app.routers.captain import router as captain_router
from app.routers.booking import router as booking_router
from app.routers.address import router as address_router
from app.routers.payment import router as payment_router
from app.routers.review import router as review_router
from app.routers.notification import router as notification_router
from app.routers.service_category import router as service_category_router
from app.routers.service import router as service_router


app = FastAPI(
    title="Home Service Captain API",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4300",
        "http://127.0.0.1:4300",
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(captain_router)
app.include_router(booking_router)
app.include_router(address_router)
app.include_router(payment_router)
app.include_router(review_router)
app.include_router(notification_router)
app.include_router(service_category_router)
app.include_router(service_router)


@app.get("/")
def root():

    return {
        "message": "Home Service Captain API is running"
    }