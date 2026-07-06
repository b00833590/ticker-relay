import asyncio
import json
import websockets
import os
from http import HTTPStatus

clients_navigateurs = set()

async def gerer_connexion(websocket):
    try:
        premier_message = await websocket.recv()
        data = json.loads(premier_message)

        if data.get("role") == "emetteur":
            print("Émetteur connecté (ton PC / Refinitiv)")
            async for message in websocket:
                clients_a_retirer = set()
                for client in clients_navigateurs:
                    try:
                        await client.send(message)
                    except websockets.exceptions.ConnectionClosed:
                        clients_a_retirer.add(client)
                clients_navigateurs.difference_update(clients_a_retirer)

        elif data.get("role") == "navigateur":
            print("Navigateur connecté")
            clients_navigateurs.add(websocket)
            try:
                await websocket.wait_closed()
            finally:
                clients_navigateurs.discard(websocket)

    except Exception as e:
        print(f"Erreur de connexion : {e}")


async def healthcheck(connection, request):
    """
    Intercepte les requetes HTTP classiques (comme celles d'UptimeRobot)
    avant la tentative de handshake WebSocket, et repond 200 OK directement.
    Si la requete est une vraie demande d'upgrade WebSocket, on renvoie None
    pour laisser la librairie websockets traiter la connexion normalement.
    """
    if request.headers.get("Upgrade", "").lower() != "websocket":
        return connection.respond(HTTPStatus.OK, "OK - Serveur relais actif\n")
    return None


async def main():
    port = int(os.environ.get("PORT", 8765))
    async with websockets.serve(
        gerer_connexion,
        "0.0.0.0",
        port,
        process_request=healthcheck
    ):
        print(f"Serveur relais démarré sur le port {port}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())