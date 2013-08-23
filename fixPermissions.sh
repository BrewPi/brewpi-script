#!/bin/sh
sudo chown -R www-data:www-data /var/www
sudo chown -R brewpi:brewpi /home/brewpi
sudo chmod -R g+rwx /home/brewpi
sudo find /home/brewpi -type d -exec chmod g+s {} \;
sudo chmod -R g+rwx /var/www
sudo find /var/www -type d -exec chmod g+rwxs {} \;
