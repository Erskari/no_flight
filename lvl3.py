from dotenv import dotenv_values
import requests
import webbrowser
import websocket
import json
from lib.math import normalize_heading
import time
import math

FRONTEND_BASE = "noflight.monad.fi"
BACKEND_BASE = "noflight.monad.fi/backend"

game_id = None

def on_message(ws: websocket.WebSocketApp, message):
    [action, payload] = json.loads(message)

    if action != "game-instance":
        print([action, payload])
        return
     # New game tick arrived!
    game_state = json.loads(payload["gameState"])
    commands = generate_commands(game_state)

    time.sleep(0.1)
    ws.send(json.dumps(["run-command", {"gameId": game_id, "payload": commands}]))


def on_error(ws: websocket.WebSocketApp, error):
    print(error)


def on_open(ws: websocket.WebSocketApp):
    print("OPENED")
    ws.send(json.dumps(["sub-game", {"id": game_id}]))


def on_close(ws, close_status_code, close_msg):
    print("CLOSED")

# Change this to your own implementation
def generate_commands(game_state):
    commands = []
    aircraft = game_state['aircrafts']

    # Lisää pelissä kuluneiden tickien määrää yhdellä aina jos edes yksi kone on olemassa
    game_tick_count.append(aircraft[0]['id'])

    # Asetetaan koneen lähestymiskulma
    if len(game_tick_count) == 8:
        new_dir = normalize_heading(aircraft[0]['direction'] - 20)
        commands.append(f"HEAD {aircraft[0]['id']} {new_dir}")
        return commands

    # Kun kone on lähellä lentokenttää kännetään konetta 10 * 20°
    # 180° täyskäännökseen ja 20° lähestymiskulman nollaukseen
    while len(game_tick_count) >= 24 and len(game_tick_count) <= 33:
        new_dir = normalize_heading(aircraft[0]['direction'] + 20)
        commands.append(f"HEAD {aircraft[0]['id']} {new_dir}")
        return commands

    return commands

def main():
    config = dotenv_values()
    res = requests.post(
        f"https://{BACKEND_BASE}/api/levels/{config['LEVEL_ID']}",
        headers={
            "Authorization": config["TOKEN"]
        })

    if not res.ok:
        print(f"Couldn't create game: {res.status_code} - {res.text}")
        return

    game_instance = res.json()
    global game_id
    global game_tick_count
    # generate_commands funktiossa käytettävän game_tick_count muuttujan alustus
    game_tick_count = []
    game_id = game_instance["entityId"]

    url = f"https://{FRONTEND_BASE}/?id={game_id}"
    print(f"Game at {url}")
    webbrowser.open(url, new=2)
    time.sleep(2)

    ws = websocket.WebSocketApp(
        f"wss://{BACKEND_BASE}/{config['TOKEN']}/", on_message=on_message, on_open=on_open, on_close=on_close, on_error=on_error)
    ws.run_forever()


if __name__ == "__main__":
    main()