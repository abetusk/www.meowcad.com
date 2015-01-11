#!/bin/bash
 
docker build --no-cache -t meowcad .
docker run -d -p 80:80 -p 443:443 meowcad
docker ps
