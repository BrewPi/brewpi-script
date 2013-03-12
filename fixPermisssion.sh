sudo chown -R www-data:www-data /var/www
sudo chown -R brewpi:brewpi /home/brewpi
sudo find /home/brewpi -type f -exec chmod g+rwx {} \;
sudo find /home/brewpi -type d -exec chmod g+rwxs {} \;
sudo find /var/www -type d -exec chmod g+rwxs {} \;
sudo find /var/www -type f -exec chmod g+rwx {} \;
