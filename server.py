from aiohttp import web
import json
import os

# Dernier etat connu des indices, garde en memoire
dernieres_donnees = {
    "derniere_maj": None,
    "indices": []
}


async def recevoir_maj(request):
    """POST /update : recoit les derniers prix depuis refinitiv_stream.py"""
    global dernieres_donnees
    try:
        data = await request.json()
        dernieres_donnees = data
        return web.json_response({"status": "ok"})
    except Exception as e:
        return web.json_response({"status": "erreur", "detail": str(e)}, status=400)


async def envoyer_dernieres_donnees(request):
    """GET /latest : renvoie les derniers prix connus au site web"""
    reponse = web.json_response(dernieres_donnees)
    reponse.headers["Access-Control-Allow-Origin"] = "*"  # autorise l'appel depuis GitHub Pages
    return reponse


async def healthcheck(request):
    """GET / : simple verification que le serveur est vivant"""
    return web.Response(text="OK - Serveur relais actif\n")


app = web.Application()
app.router.add_post("/update", recevoir_maj)
app.router.add_get("/latest", envoyer_dernieres_donnees)
app.router.add_get("/", healthcheck)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    web.run_app(app, host="0.0.0.0", port=port)