package main

import (
	"os"
	"fmt"
	"log"

	"github.com/jdjnovak/simple-game-server/core/server"
)

func main() {
	fmt.Println("[STARTUP] Starting server...")

	// Get arguments
	args := os.Args
	if len(args) != 2 {
		log.Fatal("USAGE: simple-server <port>")
		os.Exit(1)
	}
	port_string := args[1]

	// Initialize the server
	serv,err := server.InitServer("0.0.0.0", port_string)
	if err != nil {
		log.Fatalf("[ERROR] Error initializing server: %s\n", err)
		os.Exit(2)
	}

	// Start the server
	serv.StartListener()
}
