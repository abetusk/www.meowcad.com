#!/bin/bash

service apache2 start
service haproxy start
service redis-server start

su meow -c " cd /home/meow/www.meowcad.com/js ; nodejs meowserver.js >> meowserver.log 2>> meowserver.err & "
su meow -c " cd /home/meow/www.meowcad.com/scripts ; ./libmod_import_d.py >> libmod_import_d.log 2>> libmod_import_d.err & "
su meow -c " cd /home/meow/www.meowcad.com/scripts ; ./libmod_snap_d.py >> libmod_snap_d.log 2>> libmod_snap_d.err & "
su meow -c " cd /home/meow/www.meowcad.com/aux ; ./mewprojectsnapshot_d.py >> mewprojectsnapshot_d.log 2>> mewprojectsnapshot_d.err & "

while [ true ]
do
  echo mew
  sleep 3
done
