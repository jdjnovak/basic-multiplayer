package logging

import (
	"fmt"
	"time"
)

func GetTimestamp() string {
	return fmt.Sprintf("%s", time.Now().Local().Format("2006-12-31 23:59:59"))
}
