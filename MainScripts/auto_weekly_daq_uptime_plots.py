##########################################################################
# Original Author: Nur, 04/11/2016
# Modified as needed: Nur, 04/30/2016
# Script to make automatic ECL entry for DAQ Clock Livetime Plot
##########################################################################

from ECLAPI import ECLConnection, ECLEntry
from mnv_ecl import * 
from re import search 
import os,glob,time

def FindShift(filepath):
    #Setting up the shift hours for owl
    OwlShiftHours=range(0,7)
    OwlShiftHours.append(23)

    localhour=time.localtime(os.path.getmtime(filepath)).tm_hour#Should be in CST, on the Fermilab servers
    t = time.localtime()
    current_time=time.asctime(t)
    print "Current Time %s " % current_time


    if localhour in OwlShiftHours:
        return "DAQ Weekly Clock Livetime Plot. Created on %s" % current_time
    elif localhour in range(7,15):
        return "DAQ Weekly Clock Livetime Plot. Created on %s" % current_time
    elif localhour in range(15,23):
        return "DAQ Weekly Clock Livetime Plot. Created on %s" % current_time

if __name__ == '__main__':
    import getopt, sys

    opts, args = getopt.getopt(sys.argv[1:], 'np:u:U:')

    print_only = False

    for opt, val in opts:
        if opt=='-n':           # Print the entry to screen, not to post it
            print_only = True
        if opt=='-p':           # User password
            password = val
        if opt=='-u':           # User name
            user = val
        if opt == '-U':         # ECL instance URL to use for the posts
            URL = val

##########################################################################
    #Find if there is a new run or output

    DAQUptimePlots="/home/minerva/cmtuser/Minerva_v10r9p1/Tools/ControlRoomTools/SmartShift/images/weekly_DAQ_live_time.png"
    ShiftName=FindShift(DAQUptimePlots)

    e = ECLEntry(category='Shift_Notes/Control_Room_Shifts',
                tags=['DAQUptimePlots'],
                formname='default',
                text="""{0}. Automated posting.""".format(ShiftName),
                preformatted=False)

    e.addImage("DAQ Clock Livetime Plots",DAQUptimePlots)
    
    if not print_only:
        # Define connection
        elconn = ECLConnection(url=URL, username=user, password=password)
        #
        # The user should be a special user created with the "raw password" by administrator.
        # This user cannot login via GUI

        # Post test entry created above
        response = elconn.post(e)

        # Print what we have got back from the server
        print response

        # Close the connection
        elconn.close()
        
    else:
        # Just print prepared XML
        print e.xshow()

