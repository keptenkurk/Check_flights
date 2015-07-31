# Check_flights
Checks flights received by Dump1090 ADSB over defined area and emails track.

This Python script reads the json data from a Dumo1090 instance (on local host or networked) every second and determines
if this data contains a flight crossing a defined area of interest (AOI). This AIO ia square area and defined by its longitudes 
and lattitudes.
Once a plane is caught its track will be recorded and emailed in .GPX format once the aircraft has left the AOI.

Use case: How often do flights cross areas which have been marked as no-fly zones?
