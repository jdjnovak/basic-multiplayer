import sys
import time
import socket
import pygame
import traceback
import threading

from util import Message
from util import ClientPeer
from util import PeerList

SCREEN_W, SCREEN_H = 1280, 720
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12345

COLOURS = {
    "WHITE": (255, 255, 255),
    "BLACK": (0, 0, 0),
    "BLUE": (0, 0, 255)
}

#OTHER_PLAYERS = [] # {"name": "player_name", "pos": "player_pos", "vel": "player_vel", "colour": "player_colour"}
OTHER_PLAYERS = PeerList()
MESSAGES = []
LOCK = threading.Lock()

def rgb2hex(r,g,b):
    return "{:02x}{:02x}{:02x}".format(r,g,b)


def hex2rgb(hexcode):
    return (int(hexcode[:2],16),int(hexcode[2:4],16),int(hexcode[4:],16))


def get_timestamp():
    return f"{time.strftime('%d/%m/%Y %H:%M:%S')}"


def log(level, msg):
    print(f"{time.strftime("%d-%m-%Y %H:%M:%S")} [{level}] {msg}")


def parse_message(message):
    split = message.strip().split("||")
    return Message(split[0], split[1], split[2], split[3])


def parse_playerlist(playerlist_string):
    global OTHER_PLAYERS
    outlist = []
    # username:position:velocity:colour/username2:position:velocity:colour/username3:position:velocity:colour/etc...
    print(f"playerliststring = {playerlist_string}")
    for player in playerlist_string.split("/"):
        components = player.split(":")
        pos_split = components[1].split(",")
        pos = (float(pos_split[0]),float(pos_split[1]))
        vel_split = components[2].split(",")
        vel = (float(vel_split[0]),float(vel_split[1]))
        print(f"pos_split = {pos_split}\tvel_split = {vel_split}")
        #colour = eval(components[2]) # When using python server
        colour = hex2rgb(components[3])
        #exists = [p for p in OTHER_PLAYERS if p["name"] == components[0]]
        #if len(exists) > 0:
        if OTHER_PLAYERS.has_user(components[0]):
            data = {
                "position": pos,
                "velocity": vel,
                "colour": colour
            }
            OTHER_PLAYERS.update_peer(components[0], data)
            #outlist.append({"name": components[0], "pos": pos, "vel": vel, "colour": colour})
        else:
            OTHER_PLAYERS.add_peer(ClientPeer(components[0], pos, vel, colour))
            #outlist.append({"name": components[0], "pos": pos, "vel": vel, "colour": colour})
    return outlist


def receive_messages(sock, message_list):
    global MESSAGES
    global OTHER_PLAYERS
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break
            print(f"[DEBUG] Data decode: '{data.decode()}'")
            parsed = parse_message(data.decode())
            #split = parsed.split("||")
            print(parsed)
            if parsed.cmd == "playerlist":
                #OTHER_PLAYERS = parse_playerlist(parsed.body)
                parse_playerlist(parsed.body)
            with LOCK:
                message_list.append(parsed)
                #message_list.append(data.decode())
            #log("INFO", data.decode())
        except Exception as e:
            log("ERROR", f"An exception occured while reading messages: {e}")
            print(traceback.format_exc())
            break


def start_client(sock):
    log("INFO", "Connected to server.")
    try:
        while True:
            msg = input()
            if msg.strip().lower() == 'quit':
                break
            sock.sendall(msg.encode())
    finally:
        sock.close()
        log("INFO", "Disconnected from server.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("USAGE: python3 client.py <username>")
        sys.exit(1)

    # TODO: Make this section better
    player_username = sys.argv[1]

    # Initialize socket to server
    SOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SOCK.connect((SERVER_HOST, SERVER_PORT))


    # Initialize pygame and the basic settings
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Game")

    # TODO: Figure this out
    #start_client(SOCK)
    #threading.Thread(target=start_client, args=(SOCK,), daemon=True).start()

    UPDATE_INTERVAL = 60 # ms per update
    LAST_UPDATE_SENT = pygame.time.get_ticks()

    threading.Thread(target=receive_messages, args=(SOCK,MESSAGES), daemon=True).start()

    player_colour = COLOURS["WHITE"]
    player_position = pygame.Vector2(SCREEN_W // 2, SCREEN_H // 2)
    player_velocity = pygame.Vector2(0, 0)
    player_speed = 5

    # Send server initial settings
    SOCK.sendall(f"{get_timestamp()}||{player_username}||init||{player_position.x},{player_position.y}:{rgb2hex(player_colour[0],player_colour[1],player_colour[2])}".encode())
    
    running = True
    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    player_colour = COLOURS["BLUE"] if player_colour == COLOURS["WHITE"] else COLOURS["WHITE"]
                    hex_colour = rgb2hex(player_colour[0],player_colour[1],player_colour[2])
                    SOCK.sendall(f"{get_timestamp()}||{player_username}||update_colour||{hex_colour}".encode())


        keys = pygame.key.get_pressed()
        x, y = 0, 0
        if keys[pygame.K_a]:
            x -= player_speed
        elif keys[pygame.K_d]:
            x += player_speed

        if keys[pygame.K_w]:
            y -= player_speed
        elif keys[pygame.K_s]:
            y += player_speed


        player_velocity = pygame.Vector2(x, y)
        if player_velocity.length() != 0:
            player_velocity.normalize_ip()
            player_position = player_position + player_velocity * player_speed

        if pygame.time.get_ticks() - LAST_UPDATE_SENT > UPDATE_INTERVAL:
            # ...||tick||player_posx,player_posy:player_move_vecx,player_move_vecy
            SOCK.sendall(f"{get_timestamp()}||{player_username}||tick||{player_position.x},{player_position.y}:{player_velocity.x},{player_velocity.y}".encode())
            LAST_UPDATE_SENT = pygame.time.get_ticks()
            with LOCK:
                print(f"Players: {OTHER_PLAYERS}")
                #print(f"Messages: {[str(m) for m in MESSAGES]}")

        screen.fill(COLOURS["BLACK"])

        # Draw other players, if any
        with LOCK:
            for p in OTHER_PLAYERS.peerlist:
                #if p["name"] != player_username:
                if p.username != player_username:
                    """
                    direction = pygame.Vector2(p["pos"][0], p["pos"][1]) - pygame.Vector2(p["last_pos"][0], p["last_pos"][1])
                    distance = direction.length()
                    move = 0
                    if distance != 0:
                        direction.normalize_ip()
                        move = min(player_speed, distance)
                    move_vector = pygame.Vector2(p["last_pos"][0], p["last_pos"][1]) + (direction * move)
                    pygame.draw.circle(screen, p["colour"], move_vector, 50)
                    """
                    #move_vector = pygame.Vector2(p["pos"][0], p["pos"][1]) + pygame.Vector2(p["vel"][0], p["vel"][1]) * player_speed
                    #pygame.draw.circle(screen, p["colour"], move_vector, 50)
                    move_vector = pygame.Vector2(p.position[0], p.position[1]) + pygame.Vector2(p.velocity[0], p.velocity[1]) * player_speed
                    pygame.draw.circle(screen, p.colour, move_vector, 50)

        # Draw this player on top
        pygame.draw.circle(screen, player_colour, player_position, 50)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

