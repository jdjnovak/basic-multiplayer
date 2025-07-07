package client

import (
	"fmt"
	"net"
	"strings"
	"strconv"
)

type Vector2 struct {
	X float64
	Y float64
}

func ParseVector(s string) (Vector2,error) {
	// Input string in format x,y
	split := strings.Split(s, ",")
	if len(split) != 2 {
		return Vector2{},fmt.Errorf("Invalid Vector2 format: '%s'", s)
	}

	floatx,err := strconv.ParseFloat(split[0], 64)
	if err != nil {
		return Vector2{},fmt.Errorf("Invalid float64: '%s'", split[0])
	}
	floaty,err := strconv.ParseFloat(split[1], 64)
	if err != nil {
		return Vector2{},fmt.Errorf("Invalid float64: '%s'", split[1])
	}
	return Vector2{X: floatx, Y: floaty},nil
}

// TODO: Add vector functions?

type Client struct {
	Conn net.Conn
	//Addr net.Addr // Don't think I need?
	Id uint64
	Username string
	Position Vector2
	Velocity Vector2
	Colour string // hex value
}

func NewClient(c net.Conn) *Client { 
	return &Client{Conn: c, Id: 0, Username: "", Position: Vector2{}, Colour: "000000"}
}

// TODO: Add any necessary client functions
