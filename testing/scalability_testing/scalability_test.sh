#!/bin/bash

clear
for FILE in $1/*; 
    do python3 ../../src/client.py -i $FILE;
done

