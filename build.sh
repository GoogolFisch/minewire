#!/usr/bin/env bash

DIR=./hardWear/

gcc -g -o ./rando.so -shared -fPIC -xc -I/usr/include/python3.14 $DIR/crando.c -w
