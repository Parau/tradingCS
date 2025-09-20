from fastapi import FastAPI
from contextlib import asynccontextmanager
from . import mt5_connector
from .api import history, markers, websockets

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Iniciando a aplicação...")
    await mt5_connector.initialize_mt5()
    yield
    # Shutdown
    print("Encerrando a aplicação...")
    mt5_connector.shutdown_mt5()

app = FastAPI(lifespan=lifespan)

# Inclui os roteadores da API
app.include_router(history.router, prefix="/api", tags=["History"])
app.include_router(markers.router, prefix="/api", tags=["Markers"])
app.include_router(websockets.router, tags=["WebSockets"])


@app.get("/health")
def read_root():
    return {"status": "ok"}

@app.get("/mt5-status")
def get_mt5_status():
    return {"connected": mt5_connector.is_connected()}
