#!/usr/bin/python2 -O
# -------------------------------------------------------------------
# Python script which records and e-mails flights over specified area
# All positions in the square area lowlat, lowlon to hilat, hilon and below
# level (feet) will be recorded into a .gpx file and emailed to 
# recipient.
# Only serious tracks which contain at least 5 positions will be sent
# Prequisits: Dump1090-mutability running
#-------------------------------------------------------------------- 
import json, math, time
from contextlib import closing
from urllib2 import urlopen
import urlparse
# Import smtplib, mimetypes and email for the email sending part
import smtplib
import mimetypes
import email
import email.mime.application

# Definitions
# Mail parameters
FromAddr = 'youradres@gmail.com'
Password = 'gmailpasswd'
# multiple addresses may be given in the list separated by comma's
ToAddr   =  ['recipient1@domain.com', 'recipient2@domain.com']
CcAddr   = ['recipient3@domain.com']

# Area of interest
lowlat   = 51.456833
hilat    = 51.479605
lowlon  = 5.238706
hilon   = 5.275276
hialt    = 8200

# Init vars 
aircraft_seen = {}
aircraft_tracks = []
aircraft_count = 0
maxage = 60                 # email data 60s after last position was received
host = 'http://127.0.0.1'   # dump1090 receiver to be used (could be networked)
url = '/dump1090'           # dump1090 url
    
# Do the job until forever
while True:
#   read_aircraft from Dump1090 to aircraft dictionary
    with closing(urlopen(host + url + '/data/aircraft.json', None, 5.0)) as aircraft_file:
        aircraft_data = json.load(aircraft_file)

#   record new planes and reset age for those still within range
    for a in aircraft_data['aircraft']:
        # check if the record has a position
        if a.has_key('seen_pos'):
            # check if the position within range
            if a['lat'] > lowlat and a['lat'] < hilat and a['lon'] > lowlon and a['lon'] < hilon and a['altitude'] < hialt:
                index = a['hex']
                # reset 'last seen' timer
                aircraft_seen[index]=0
                # append position and other info to tracklist
                aircraft_tracks.extend([index,a['lat'],a['lon'],a['altitude'],time.strftime("%Y%m%dT%H%M%S")])
                print("."),
                   
#   increment age and purge aircraft from our list if not seen for a long time
    for hexcode,age in aircraft_seen.items():
        aircraft_seen[hexcode] += 1
        if age > maxage:
            del aircraft_seen[hexcode]
            # move positions from list to xml in gpx format
            xmlfilename = hexcode + "_" + time.strftime("%y%m%d_%H%M") + ".gpx"
            xmlfile = open(xmlfilename,'w')

            # write xml start to file
            xmlfile.write(
              "<?xml version=\"1.0\"?>\n"
              "<gpx version=\"1.1\" creator=\"Paul Merkx\" "
              "xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" "                    
              "xmlns=\"http://www.topografix.com/GPX/1/1\" "
              "xsi:schemaLocation=\"http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd\" >\n"
              "<trk>\n"
              "<name>"+hexcode+"</name>\n"
              "<type>Aircraft tracklog by dump1090</type>\n"
              "<trkseg>\n")

            # write positions of aircraft indentified by hexcode to file
            NumberOfPositions = aircraft_tracks.count(hexcode)
            while aircraft_tracks.count(hexcode) > 0:
                # pop hexcode, lat, lon, ele and time from list in exactly this order
                pos = aircraft_tracks.index(hexcode)
                aircraft_tracks.pop(pos)
                xmlfile.write("<trkpt lat=\"" + str(aircraft_tracks.pop(pos)) + "\" lon=\"" + str(aircraft_tracks.pop(pos)) + "\">\n")
                xmlfile.write("<ele>" + str(aircraft_tracks.pop(pos)) + "</ele>\n")
                xmlfile.write("<time>" + str(aircraft_tracks.pop(pos)) + "</time>\n</trkpt>\n")
            # write xml remainder to file  
            xmlfile.write(
              "</trkseg>\n"
              "</trk>\n"
              "</gpx>\n")
            xmlfile.close()
            
            # email gpx file only if track contains 5 positions or more
            # Create a text/plain message
            if NumberOfPositions > 5 :
                content = """
                    <html>
                        <head></head>
                        <body>
                            <p>Dear Sir!<br>
                            Write your email content here in html format. 
                            </p>
                        </body>
                    </html>
                    """
                msg = email.mime.Multipart.MIMEMultipart()
                msg['Subject'] = 'Subject of this mail'
                msg['From'] = FromAddr
                msg['To'] = ', '.join(ToAddr)
                msg['Cc'] = ', '.join(CcAddr)
                body = email.mime.Text.MIMEText(content, 'html')               
                msg.attach(body)
                type='gpx'
                xmlfile = open(xmlfilename,'rb')
                att = email.mime.application.MIMEApplication(xmlfile.read(),_subtype=type)
                xmlfile.close()
                att.add_header('Content-Disposition','attachment',filename=xmlfilename)
                msg.attach(att)
                
                # send via Gmail server
                s = smtplib.SMTP('smtp.gmail.com:587')
                s.starttls()
                s.login(FromAddr,Password)
                s.sendmail(FromAddr,ToAddr+CcAddr, msg.as_string())
                s.quit()
    time.sleep(1)

