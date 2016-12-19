#!/bin/sh

# APC and NUT UPS Service Monitor Installation script.

if [[ $(id -u) -ne 0 ]] ; then
   echo "Please run as root";
   exit 1;
fi

cp -p ./etc/init.d/apcmond /etc/init.d/apcmond
cp -p ./etc/init.d/nutmond /etc/init.d/nutmond

# and make sure file ownership and execute permissions are properly set.
chown root:root /etc/init.d/apcmond /etc/init.d/nutmond
chmod 555 /etc/init.d/apcmond /etc/init.d/nutmond

# Make config.py from template
if [! -f 'config.py' ]; then
   cp -p config.default.py config.py
fi

# Copy entire 'upsmon' folder into /usr/sbin/
cp -r upsmon /usr/sbin/

# and make sure file ownership and execute permissions are properly set.
chown -R root:root /usr/sbin/upsmon
chmod 775 /usr/sbin/upsmon/*.sh
chmod 555 /usr/sbin/upsmon/*d.py
chmod 775 /usr/sbin/upsmon/config.py


# Create symbolic links to the python scripts.
# This also enables us to execute them like regular comands from anywhere in the
# filesystem because /usr/sbin is already included in the PATH.

ln -s /usr/sbin/upsmon/apcmond.py /usr/sbin/apcmond
ln -s /usr/sbin/upsmon/nutmond.py /usr/sbin/nutmond
