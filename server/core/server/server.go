package server

import (
	"fmt"
	"log"
	"net"
	"sync"
	"strconv"
	"strings"

	"github.com/jdjnovak/simple-game-server/core/client"
	"github.com/jdjnovak/simple-game-server/core/logging"
	"github.com/jdjnovak/simple-game-server/core/command"
)

type Reply struct {
	Broadcast bool
	Message string
}

type Server struct {
	Listener 	*net.TCPListener
	TCPAddr		*net.TCPAddr
	Port 		int
	Clients		[]*client.Client

	lastId		uint64
	mu			sync.Mutex
}

func InitServer(addrString string, portString string) (*Server,error) {
	port, err := strconv.Atoi(portString)
	if err != nil {
		return nil,fmt.Errorf("[ERROR] port number is required to be an integer value")
	}
	addr, err := net.ResolveTCPAddr("tcp", fmt.Sprintf(":%s", portString))
	if err != nil {
		return nil,fmt.Errorf("[ERROR] could not resolve TCP port %s\n", portString)
	}
	return &Server{Listener: nil, TCPAddr: addr, Port: port, lastId: 1000}, nil
}

func (s *Server) StartListener() error {
	listener,err := net.ListenTCP("tcp", s.TCPAddr)
	if err != nil {
		return fmt.Errorf("[ERROR] Could not start listener on localhost\n" )
	}
	s.Listener = listener
	log.Printf("[INFO] Started listener")
	//return nil
	for {
		conn, err := s.Listener.Accept()
		if err != nil {
			log.Fatalf("[ERROR] Error accepting connection: %s\n", err)
		}
		go s.handleConnection(conn)
	}
}

func (s *Server) handleCommand(clientid uint64, cmd string) (Reply,error) {
	replyString := ""
	broadcastReply := false
	// Parse the string
	log.Printf("[DEBUG] Handling command '%s'\n", cmd)
	c,err := command.ParseString(cmd)
	if err != nil {
		return Reply{},err
	}
	// Perform actions necessary
	switch c.Action {
	case "init":
		parts := strings.Split(c.Body, ":")
		pos := strings.Split(parts[0], ",")
		floatx,err := strconv.ParseFloat(pos[0], 64)
		if err != nil {
			return Reply{},err
		}
		floaty,err := strconv.ParseFloat(pos[1], 64)
		if err != nil {
			return Reply{},err
		}
		s.UpdateClientUsername(clientid, c.Username)
		s.UpdateClientPosition(clientid, client.Vector2{X: floatx, Y: floaty})
		s.UpdateClientColour(clientid, parts[1])

		return Reply{},nil
	case "tick":
		split := strings.Split(strings.TrimSpace(c.Body),":")
		if len(split) != 2 {
			return Reply{},fmt.Errorf("tick action requires client position and velocity - ...||tick||pos:vel")
		}
		vec,err := client.ParseVector(strings.TrimSpace(split[0]))
		if err != nil {
			return Reply{},err
		}
		vel,err := client.ParseVector(strings.TrimSpace(split[1]))
		if err != nil {
			return Reply{},err
		}
		s.UpdateClientUsername(clientid, c.Username)
		s.UpdateClientPosition(clientid, vec)
		s.UpdateClientVelocity(clientid, vel)
		replyString += "playerlist||" + s.tickClientList()
	case "update_colour":
		s.UpdateClientColour(clientid, c.Body)
		return Reply{},nil
	default:
		replyString += "invalid||" + c.Action
	}
	// Return reply string
	return Reply{Broadcast: broadcastReply, Message: replyString},nil
}

func (s *Server) handleConnection(conn net.Conn) {
	defer conn.Close()
	clnt := client.NewClient(conn)
	s.AddClient(clnt)
	buf := make([]byte, 1024)
	for {
		n, err := conn.Read(buf)
		if err != nil {
			log.Println(err)
			return
		}
		//fmt.Printf("Received: %s", string(buf[:n]))

		data := string(buf[:n])
		reply,err := s.handleCommand(clnt.Id, data)
		if err != nil {
			log.Print(fmt.Errorf("[ERROR] %w\n", err))
		}

		// Check if you need to broadcast the reply or just reply to
		// this individual client
		if len(reply.Message) > 0 {
			if reply.Broadcast {
				s.BroadcastExcept(reply.Message, clnt)
			} else {
				s.SendMessage(clnt, reply.Message)
			}
		}
	}
}

func (s *Server) BroadcastAll(msg string) {
	for _,c := range s.Clients {
		s.SendMessage(c, msg)
	}
}

func (s *Server) BroadcastExcept(msg string, cl *client.Client) {
	for _,c := range s.Clients {
		if c.Id == cl.Id {
			continue // skip the specified client
		}
		s.SendMessage(cl, msg)
	}
}

func (s *Server) SendMessage(cl *client.Client, msg string) {
	fullMsg := fmt.Sprintf("%s||server||%s",logging.GetTimestamp(), msg)
	_,err := cl.Conn.Write([]byte(fullMsg))
	if err != nil {
		log.Print(fmt.Errorf("[ERROR] Error sending message '%s' to client %d: %w\n", msg, cl.Id, err))
	}
}

func (s *Server) AddClient(c *client.Client) {
	s.mu.Lock()
	c.Id = s.lastId // Set ID before adding to list
	s.Clients = append(s.Clients, c)
	s.lastId++
	s.mu.Unlock()
}

func (s *Server) RemoveClient(id uint64) {
	s.mu.Lock()
	defer s.mu.Unlock() // Use cause early return
	for i, c := range s.Clients {
		if c.Id == id {
			s.Clients = append(s.Clients[:i], s.Clients[i+1:]...)
			return
		}
	}
}

/*
* TODO: Figure out if I want to merge these update functions into one
*/
func (s *Server) UpdateClientPosition(id uint64, newPos client.Vector2) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _,c := range s.Clients {
		if c.Id == id {
			c.Position = newPos
			return
		}
	}
}

func (s *Server) UpdateClientUsername(id uint64, newName string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _,c := range s.Clients {
		if c.Id == id {
			c.Username = newName
			return
		}
	}
}

func (s *Server) UpdateClientColour(id uint64, newColour string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _,c := range s.Clients {
		if c.Id == id {
			c.Colour = newColour
			return
		}
	}
}

func (s *Server) UpdateClientVelocity(id uint64, newVel client.Vector2) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _,c := range s.Clients {
		if c.Id == id {
			c.Velocity = newVel
			return
		}
	}
}

// Print out the client list in the format 
// 'username1:pos_x,pos_y:vel_x,vel_y:colour/username2:...'
// Used when clients send tick commands to the server
func (s *Server) tickClientList() string {
	outString := ""
	for _,c := range s.Clients {
		outString += fmt.Sprintf("%s:%f,%f:%f,%f:%s/", c.Username, c.Position.X, c.Position.Y, c.Velocity.X, c.Velocity.Y, c.Colour)
	}
	return outString[:len(outString)-1]
}

// TODO: Add update functions
