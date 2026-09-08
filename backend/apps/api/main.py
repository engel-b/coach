import logging

from fastapi import FastAPI

from apps.api.routers.check_ins import router as check_ins_router
from apps.api.routers.devices import router as devices_router
from apps.api.routers.health import router as health_router
from apps.api.routers.persons import router as persons_router
from apps.api.routers.telemetry import router as telemetry_router
from apps.api.routers.training import router as training_router
from apps.api.routers.workout_videos import (
    router as workout_videos_router,
)
from apps.api.routers.workouts import router as workouts_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


app = FastAPI(
    title="Health Coach API",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(devices_router)
app.include_router(telemetry_router)
app.include_router(persons_router)
app.include_router(check_ins_router)
app.include_router(training_router)
app.include_router(workouts_router)
app.include_router(workout_videos_router)
