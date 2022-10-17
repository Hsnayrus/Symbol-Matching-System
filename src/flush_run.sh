#!/bin/bash

python3 ../manage.py flush --no-input
python3 server.py