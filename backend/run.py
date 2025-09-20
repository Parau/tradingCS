import uvicorn
import os

if __name__ == "__main__":
    # Obtém a porta da variável de ambiente ou usa 8000 como padrão
    port = int(os.getenv("PORT", 8000))

    # Inicia o servidor Uvicorn
    # reload=True é ótimo para desenvolvimento, pois reinicia o servidor a cada alteração de código.
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
