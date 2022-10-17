#!/bin/bash

echo $1
echo "yes" | python3 ../manage.py flush

for FILE in basic_order_operations/*; do python3 ../src/client.py -i $FILE -host $1; done