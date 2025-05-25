#!/bin/bash
cd "$(dirname "$0")"
mkdir -p /var/www/html/swiley.net/
mkdir -p /var/www/html/dopes.top/
mkdir -p /var/www/html/bingestop.com/
cp -r ./swiley.net/* /var/www/html/swiley.net/
cp -r ./dopes.top/* /var/www/html/dopes.top/
cp -r ./dopes.top/* /var/www/html/bingestop.com/
