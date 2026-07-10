from aiohttp import web, ClientSession
import asyncio
import os

dernieres_donnees = {
    "derniere_maj": None,
    "indices": []
}

TICKERS = {
    "DOW JONES": "^DJI",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "CAC 40": "^FCHI",
    "DAX": "^GDAXI",
    "FTSE 100": "^FTSE",
    "EURO STOXX 50": "^STOXX50E",
    "HANG SENG": "^HSI",
    "OR (Gold)": "GC=F",
    "PÉTROLE BRENT": "BZ=F",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "BITCOIN": "BTC-USD",
}

INTERVALLE_SECONDES = 3


async def recuperer_prix_yahoo(session, nom, symbole):
    """Interroge l'API non-officielle Yahoo Finance pour un symbole donne."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbole}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        async with session.get(url, headers=headers, timeout=8) as resp:
            if resp.status != 200:
                return {"nom": nom, "valeur": None, "variation": None}
            data = await resp.json()

        result = data["chart"]["result"][0]
        meta = result["meta"]

        prix_actuel = meta.get("regularMarketPrice")
        prix_precedent = meta.get("previousClose") or meta.get("chartPreviousClose")

        if prix_actuel is None or prix_precedent is None:
            return {"nom": nom, "valeur": None, "variation": None}

        variation = ((prix_actuel - prix_precedent) / prix_precedent) * 100

        return {
            "nom": nom,
            "valeur": round(prix_actuel, 2),
            "variation": round(variation, 2)
        }
    except Exception as e:
        print(f"Erreur recuperation {nom} ({symbole}) : {e}")
        return {"nom": nom, "valeur": None, "variation": None}


async def boucle_mise_a_jour(app):
    """Tache de fond : va chercher les prix Yahoo Finance en continu."""
    global dernieres_donnees
    async with ClientSession() as session:
        while True:
            try:
                resultats = await asyncio.gather(*[
                    recuperer_prix_yahoo(session, nom, symbole)
                    for nom, symbole in TICKERS.items()
                ])

                from datetime import datetime
                dernieres_donnees = {
                    "derniere_maj": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "indices": resultats
                }
                print(f"Prix mis a jour : {dernieres_donnees['derniere_maj']}")

            except Exception as e:
                print(f"Erreur dans la boucle de mise a jour : {e}")

            await asyncio.sleep(INTERVALLE_SECONDES)


async def demarrer_tache_fond(app):
    app["tache_prix"] = asyncio.create_task(boucle_mise_a_jour(app))


async def arreter_tache_fond(app):
    app["tache_prix"].cancel()


async def envoyer_dernieres_donnees(request):
    """GET /latest : renvoie les derniers prix connus au site web"""
    reponse = web.json_response(dernieres_donnees)
    reponse.headers["Access-Control-Allow-Origin"] = "*"
    return reponse


async def healthcheck(request):
    return web.Response(text="OK - Serveur relais actif\n")


app = web.Application()
app.router.add_get("/latest", envoyer_dernieres_donnees)
app.router.add_get("/", healthcheck)
app.on_startup.append(demarrer_tache_fond)
app.on_cleanup.append(arreter_tache_fond)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8765))
    web.run_app(app, host="0.0.0.0", port=port)