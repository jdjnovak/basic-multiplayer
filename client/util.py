class ClientPeer:
    def __init__(self, username, position, velocity, colour):
        self.username = username

        self.position = position       # Position is their "target" position
                                       # or where the server says they are

        self.local_position = position # Local position shows their current
                                       # position rendered on this client
        self.velocity = velocity

        self.colour = colour

    def set_username(self, username):
        self.username = username

    def set_position(self, new_position):
        self.position = new_position

    def set_velocity(self, new_velocity):
        self.velocity = new_velocity

    def set_colour(self, new_colour):
        self.colour = new_colour

    def __str__(self):
        return f"{self.username}:{self.position}:{self.velocity}:{self.colour}"


class PeerList:
    peerlist: list[ClientPeer] = []
    #def __init__(self):
        #self.peerlist = [] # idk if this is needed

    def has_user(self, username: str):
        for _,p in enumerate(self.peerlist):
            if username == p.username:
                return True
        return False

    def add_peer(self, new_peer: ClientPeer):
        if not self.has_user(new_peer.username):
            self.peerlist.append(new_peer)
        else:
            print(f"[ERROR] Peer {new_peer.username} in client list already")

    def update_peer(self, username, new_info):
        for p in self.peerlist:
            if p.username == username:
                try:
                    p.set_position(new_info["position"])
                except:
                    pass

                try:
                    p.set_velocity(new_info["velocity"])
                except:
                    pass

                try:
                    p.set_colour(new_info["colour"])
                except:
                    pass
                return

class Message:
    def __init__(self, timestamp, sender, cmd, body):
        self.timestamp = timestamp
        self.sender = sender
        self.cmd = cmd
        self.body = body

    def pretty_print(self, timestamp):
        # Don't need to use the sent timestamp as we can just input local timestamp
        return f"({timestamp})[{self.sender}]: {self.cmd} = {self.body}"

    def __str__(self):
        return f"{self.sender}||{self.cmd}||{self.body}"

