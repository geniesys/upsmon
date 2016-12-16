
APC and NUT UPS Service Monitor. GPL and MIT Public Licenses.

Version 0.2

*************************************************************************************
(!) This application is not ready for deployment.
The code works as intended, but there is more work needs to be done with the
packaging and installation process. Particularly, creating VIB package for ESXi hosts.
*************************************************************************************

General purpose UPS-NIS monitor and host "shutdowner" utility for Linux systems.
This software is compatible with APCUPSD and NUT Network Information Services (NIS).
It is intended to monitor these services over the network and execute system
shutdown when certain power conditions are reported by the monitored UPS device.
This project primary targets VMware ESXi hosts which lack ability to monitor UPS-NIS
on their own (instead rely on additional VMware software) but it is not limited to ESX.
This software also works on openSUSE 13.x, Ubuntu and should be compatible with
pretty much any Linux-based system where Python can run.

This software does not work directly with USB- or RS232-connected UPS devices. This
is a "UPS-client" daemon. It monitors remote UPS-NIS, not the UPS itself. You have
to have a working APCUPSD or NUT somewhere else on your network with UPS connected
to it via USB or serial cable to make this work.
This monitor may work with network-enabled UPS devices that use APC or NUT protocol,
but we're unable to verify that since we don't have any.

System shutdown is executed by calling shutdown.sh which calls a system utility
that actually performs the shutdown. All Linux systems have one. Usually it is called
'shutdown', but you should verify that this is in fact correct command for your system.
You can also customize shutdown.sh as you see fit (send email notification, for example).

--------------------------------------------------------------------------------------
					INSTALLATION
--------------------------------------------------------------------------------------

1) Download and unpack.
2) See install.sh for what needs to be done. Run it if you agree with it.

--------------------------------------------------------------------------------------
					CONFIGURATION
--------------------------------------------------------------------------------------

1) Modify /usr/sbin/upsmon/config.py
   Specify IP address or name and port number of the remote NIS server being monitored.

--------------------------------------------------------------------------------------
					TEST
--------------------------------------------------------------------------------------

1) Run apcmond or nutmond from terminal to see if it works. Ctrl+C to exit.

	$ apcmond

	or

	$ nutmond


2) Try to run as service

	$ [sudo] /etc/init.d/apcmond start


	To stop:
	$ [sudo] /etc/init.d/apcmond stop


--------------------------------------------------------------------------------------
