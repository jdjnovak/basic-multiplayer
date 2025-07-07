package command

import (
	"fmt"
	"strings"
)

type Command struct {
	Timestamp string
	Username string
	Action string
	Body string
}

func ParseString(s string) (Command,error) {
	// timestamp||username||action||body
	split := strings.Split(s, "||")
	if len(split) != 4 {
		return Command{},fmt.Errorf("Invalid command '%s'\n", s)
	}
	return Command{Timestamp: split[0], Username: split[1], Action: split[2], Body: split[3]}, nil
}
