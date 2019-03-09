##########################################################################
# Original Author: Nur, 04/26/2017
# Lat Modified as needed: Nur, 04/27/2017
# Script to make automatic ECL entry for Start Run Series
##########################################################################

from email.mime.text import MIMEText
from subprocess import Popen, PIPE
from ECLAPI import ECLConnection, ECLEntry
from minos_ecl import * 
from re import search 
import os,glob,sys,time

class NewRuns(object): #Will look for new runs in the swap area, fill the information about them
    def __init__(self):#Set up dictionaries, nonsense values if not filled
        self._Modes= {"minos":"MINOS"} 
        self._Configs={"standard":"Standard"}
        self.RunNum=str(-1)
        self.RunMode="MINOS"
        self.RunConfig="Standard"
        self.RunStart="auto"
        self.RunComment="This is just the test output"
        self.Subrun=str(-1)
        self._LastLog=self._GetLastLog()
    def _GetLastLog(self):
        return sorted(glob.glob("{0}/*_CurrentMinosRun.log".format(LOGDIR)),reverse=True)[0]
    def GetNewRuns(self,any_subrun=False):#Run through each file in swap, say if it is a new run
        swapfiles=sorted(glob.iglob('{0}/N0*.mdaq.root'.format(SWAPDIR)),key=os.path.getctime)
        for f in swapfiles:
            if self._isNewRun(f) or any_subrun:
                yield True
    def SetRunInfo(self,regex):
        self.RunNum=str(int(regex.group(1)))
#        self.RunMode=self._Modes[regex.group(3)]
#        self.RunConfig=self._Configs[regex.group(3)]
        self.RunComment="{0}".format(time.ctime(os.path.getmtime(self._LastLog)))
        self.Subrun=str(int(regex.group(2)))
    def SetRunRef(self,NewRunNumber):
        print "SetRunRef: {0}".format(NewRunNumber)
        logfile=open("{0}/{1}_CurrentMinosRun.log".format(LOGDIR,int(time.time())),"w")
        logfile.write("Run {0}\n".format(NewRunNumber))
        logfile.close()
    def ReadRunRef(self):	
        logfile=open(self._LastLog,"r")
        runline=logfile.readline()#There should only ever be one, and it should be near the top
        logfile.close()
        lognum=search("Run ([0-9]+)",runline)
        if lognum:
            return int(lognum.group(1))
        else:
            print "Could not find a run number from the logfile {0}/CurrentMinosRun.log".format(LOGDIR)
            sys.exit(1)
    def _isNewRun(self, filename):#Sees if a file is from a new run
        RunRef=self.ReadRunRef()
        runsearch=search("{0}/N0([0-9]+)_([0-9]+)*.mdaq.root".format(SWAPDIR),filename)
        if runsearch:
            self.SetRunInfo(runsearch)
            if int(self.Subrun)!=1:#If subrun is not 1
                return False
            else:
                if int(self.RunNum)<=RunRef:#Not a new run
                    return False
                else:
                    return True
        else:
            print "Cannot match file", filename
            return

def SendEmail(Address="nur@fnal.gov",nRuns=-1): 
    msg = MIMEText("RunControl has skipped {0} runs".format(nRuns))
    msg["From"] = "minos@minos-daq24-nd"
    msg["To"] = Address
    msg["Subject"] = "RunControl has skipped {0} runs".format(nRuns)
    p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
    p.communicate(msg.as_string())
def SendText(): 
    msg = MIMEText("")
    msg["From"] = "minos@minos-daq24-nd"
#    msg["To"] = "6309960091@usamobility.net"
    msg["To"] = ""
    msg["Subject"] = "RunControl has skipped"
    p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
    p.communicate(msg.as_string())

if __name__ == '__main__':
    import getopt

    opts, args = getopt.getopt(sys.argv[1:], 'hnp:u:U:',["help","set=","toaddr=","ignore"])

    print_only = False
    any_subrun = False
    update_run = -1
    toAddr     = "nur@fnal.gov"

    helptext="auto_start_run series.py  Sends a log entry about new runs to the ECL\n"\
             "Options:\n"\
             "-n       Print entry to screen, not to post it\n"\
             "-p       User password\n"\
             "-u       User name\n"\
             "-U       ECL instance URL to use for the posts\n"\
             "--set    Change the reference run in the logfile\n"\
             "--ignore Print out the start shift form with any subrun (DEBUG)\n"
    for opt, val in opts:
        if opt in ('-h','--help'):
            print helptext
            sys.exit(0)
        if opt =='-n':           # Print the entry to screen, not to post it
            print_only = True
        if opt =='-p':          # User password                                            
            password = val                                                                 
        if opt =='-u':          # User name                                                
            user = val                                                                     
        if opt == '-U':         # ECL instance URL to use for the posts                    
            URL = val                                                                      
        if opt == "--set":      # Change the reference run in the logfile                  
            update_run = val                                                               
        if opt == "--ignore":     # Print out the start shift form with any subrun (DEBUG) 
            any_subrun = True
        if opt == "--toaddr":   #Sets the email address
            toAddr = val

##########################################################################
    #Not an efficient way of doing this, but...
    nNewRuns=0    

    #Find if there is a new run or output
    run=NewRuns()
    if update_run>-1:
        run.SetRunRef(update_run)
    for subrun in run.GetNewRuns(any_subrun):
        nNewRuns+=1
        e = ECLEntry(category='Shift_Notes/Control_Room_Shifts',
                    tags=['MinosRunSeries'],
                    formname='ShiftForms/Start_Run_Series',
                    text="""This is an automated posting""",
                    preformatted=False)

        e.setValue(name="Run number", value=run.RunNum)
        e.setValue(name="Run Mode",   value=run.RunMode)
        e.setValue(name="HW config",  value=run.RunConfig)
        e.setValue(name="Comments",value="Automated ECL entry for MINOS Run {0} Subrun {1}\n Last logfile mod: {2}\n Logfile Run: {3}".format(run.RunNum,run.Subrun,run.RunComment,run.ReadRunRef()))
            
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
            print run.ReadRunRef()

    print run._LastLog
    print "ReadRunRef: {0}".format(run.ReadRunRef())
    if nNewRuns>0:
        run.SetRunRef(run.RunNum)#This must be here. Have to update the logfile

    #Email someone if there is more than one run
    if nNewRuns>1 or any_subrun:
        SendEmail(toAddr,nNewRuns)
        SendText()
