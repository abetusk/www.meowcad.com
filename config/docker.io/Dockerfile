FROM debian:jessie

# The npm module 'canvas' has a lot of issue and is subseptible
# to bit-rot.  Periodically the 'npm install -g canvas' will fail
# claiming that 'node-gyp' failed for some reason or other.  The
# past few failures have been because of the package 'cairo' not
# compiling/being installed.  The past few fixes have been to
# add in cairo packages and additional dependencies.
#
# The latest 'npm install canvas' issue was resolved by adding
# 'libjpeg8-dev libpango1.0-dev libgif-dev' (probably the pango
# is the most important of those).
# See: https://github.com/Automattic/node-canvas/wiki/Installation---Ubuntu-and-other-Debian-based-systems
#
RUN apt-get update && apt-get install -y git apache2 haproxy \
  nodejs npm build-essential gcc g++ python \
  redis-server redis-tools python-redis \
  imagemagick python-numpy libboost-thread-dev libjpeg-dev libcairo2-dev \
  libpango1.0-dev libgif-dev \
  telnet vim

#  libjpeg8-dev libpango1.0-dev libgif-dev \

# Enable apahce2 settings and setup 'meow' user with password 'mewmew'.
#
RUN a2enmod rewrite && \
  a2enmod cgi && \
  useradd -m meow && \
  echo 'meow:mewmew' | chpasswd

# Grab git repos
#  - bleepsix holds the JavaScript editors
#  - www.meowcad.com holds the backend servers and project management web site.
#  - pykicad are the python kicad conversion scripts
#  - weakpwh is the helper utitlity to do gerber compatible fills.
#
RUN su meow -c " cd /home/meow && \
  git clone https://github.com/abetusk/bleepsix && \
  git clone https://github.com/abetusk/www.meowcad.com && \
  git clone https://github.com/abetusk/pykicad && \
  git clone https://github.com/abetusk/gbl2ngc && \
  git clone https://github.com/abetusk/weakpwh "

# Tweak installed repos
#
RUN su meow -c " cd /home/meow && \
  mkdir queue stage usr bin && \
  chmod a+rwx stage && \
  cd /home/meow/weakpwh && ./cmp.sh && \
  cd /home/meow/gbl2ngc/src && ./cmp.sh && \
  cd /home/meow/bin && \
  ln -s /home/meow/gbl2ngc/src/gbl2ngc . && \
  ln -s /home/meow/weakpwh/weakpwh . && \
  ln -s /home/meow/gbl2ngc/scripts/drl2ngc.py ./drl2ngc && \
  cd /home/meow/www.meowcad.com/scripts && ln -s ../cgi/meowaux.py . && \
  cd /home/meow/www.meowcad.com/aux && ln -s ../cgi/meowaux.py . "

# Setup certificate, pem file and setup listening port to point
# to port 8080.
#
RUN cd /etc/ssl && \
    openssl req \
    -new \
    -newkey rsa:4096 \
    -days 365 \
    -nodes \
    -x509 \
    -subj "/C=US/ST=Denial/L=Springfield/O=Dis/CN=www.meowcad.com" \
    -keyout snakeoil.key \
    -out snakeoil.crt && \
    cat snakeoil.crt snakeoil.key > snakeoil.pem && \
    cd /etc/apache2 && \
    sed -i 's/^#ServerRoot/ServerRoot/' apache2.conf && \
    sed -i 's/^/#/' ports.conf && \
    sed -i 's/^#Listen 80$/Listen 8080/' ports.conf && \
    cp /home/meow/www.meowcad.com/config/haproxy/haproxy.cfg /etc/haproxy && \
    cp /home/meow/www.meowcad.com/config/apache2/default /etc/apache2/sites-available/000-default.conf && \
    cd /usr/bin && ln -s nodejs node

# This has to be done after we setup the node -> nodejs symbolic link.
# See above if the 'canvas' install is failing.
#
RUN npm install -g async yargs canvas redis && \
  su meow -c " cd /home/meow && \
  cd /home/meow/www.meowcad.com/js && \
  npm install async yargs canvas redis "



# Kept as a reminder to replace the 'snakeoil' generation with something
# more substantial if you want something other than a self signed certificate.
#
#    -keyout www.meowcad.com.key \
#    -out www.meowcad.com.cert

# FOR LOCALHOST DEBUGGING
# This changes the host rewriting rules from 'meowcad(\\\.|\.)com' to 'localhost'.
# Comment out (or replace with your own host name) for other/produciton use.
#=============
RUN sed -i 's/meowcad\\\.com/localhost/' /etc/apache2/sites-available/000-default.conf && \
    sed -i 's/meowcad\.com/localhost/' /etc/apache2/sites-available/000-default.conf
#=============

# SETUP HTML/JS
# Copy the relevant files from the git repo to /var/www.
#
RUN cd /var/www && \
  cp -R /home/meow/www.meowcad.com/template . && \
  cp -R /home/meow/www.meowcad.com/cgi . && \
  cp -R /home/meow/www.meowcad.com/cgi/* . && \
  cp -R /home/meow/www.meowcad.com/html/* . && \
  cp -R /home/meow/bleepsix/cgi . && \
  cp -R /home/meow/bleepsix/cgi/* . && \
  cp -R /home/meow/bleepsix/css . && \
  cp -R /home/meow/bleepsix/js . && \
  cp -R /home/meow/bleepsix/json . && \
  cp -R /home/meow/bleepsix/eeschema . && \
  cp -R /home/meow/bleepsix/pcb . && \
  cp -R /home/meow/bleepsix/img . && \
  cp -R /home/meow/bleepsix/data . && \
  cp --preserve=links /home/meow/bleepsix/sch . && \
  cp --preserve=links /home/meow/bleepsix/brd . && \
  cp /home/meow/bleepsix/*.html .

# Turn off analytics (for development option).
#
RUN mv /var/www/template/analytics_template.html analytics_template.meowcad.html && \
    touch /var/www/template/analytics_template.html && \
    chmod 644 /var/www/template/analytics_template.html

# Finally, copy the startup script that Docker needs to
# keep the container running.
#
COPY ./startup_and_persist.sh /root/startup_and_persist.sh

# 80 should redirect to 443.
#
EXPOSE 80 443

CMD ["/root/startup_and_persist.sh"]
