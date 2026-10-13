#!/usr/bin/env bash

DIR="./hardWear"
OPTIMIZE="-g"
FLAGS="-shared -fPIC -xc -I/usr/include/python3.14"

gcc $OPTIMIZE -o ./rando.so  $FLAGS $DIR/crando.c  -w
gcc $OPTIMIZE -o ./spring.so $FLAGS $DIR/cspring.c -w
