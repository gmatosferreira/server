#!/bin/sh
while true; do
    nc -l -p 8888 > /tmp/nc_req.txt 2>/dev/null
    if grep -q "POST /shutdown" /tmp/nc_req.txt; then
        echo -e "HTTP/1.1 200 OK\r\n\r\nShutting down..." | nc -l -p 8888 2>/dev/null
        poweroff
    else
        # Send proper HTTP headers followed by index.html content
        echo -e "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n" > /tmp/http_res.txt
        cat /git/server/index.html >> /tmp/http_res.txt
        cat /tmp/http_res.txt | nc -l -p 8888 2>/dev/null
    fi
done