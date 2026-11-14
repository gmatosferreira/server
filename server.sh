while true; do
    nc -l -p 8888 -q 1 > /tmp/nc_req.txt
    if grep -q "POST /shutdown" /tmp/nc_req.txt; then
        echo -e "HTTP/1.1 200 OK\r\n\r\nShutting down..." | nc -l -p 8888 -q 1
        poweroff
    else
        echo -e "HTTP/1.1 200 OK\r\n\r\n$(cat /git/server/index.html)" | nc -l -p 8888 -q 1
    fi
done