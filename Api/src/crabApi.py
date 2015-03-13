#!/usr/local/bin/python
#---------------------------------------------------------------------------------------------------
# Access CRAB3 data via HTCondor
#---------------------------------------------------------------------------------------------------
import os, htcondor, ConfigParser
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.Utils import formataddr
from subprocess import Popen, PIPE

class crabApi():
    def __init__(self):
        config = ConfigParser.RawConfigParser()
        config.read(os.path.join(os.path.dirname(__file__), 'intelroccs.cfg'))
        collectorName = config.get('CRAB', 'collector')
        fromItems = config.items('from_email')
        self.fromEmail = fromItems[0]
        emailItems = config.items('error_emails')
        toNames = []
        toEmails = []
        for name, email in emailItems:
            toNames.append(name)
            toEmails.append(email)
        self.toList = (toNames, toEmails)
        # Will try to get schedulers 3 times before reporting an error
        for attempt in range(3):
            try:
                collector = htcondor.Collector(collectorName)
                self.schedulers = collector.locateAll(htcondor.DaemonTypes.Schedd)
            except IOError, e:
                continue
            else:
                break
        else:
            self.error(e)

    def error(self, e):
        # report error
        title = "FATAL IntelROCCS Error -- CRAB"
        text = "FATAL -- %s" % (str(e),)
        msg = MIMEMultipart()
        msg['Subject'] = title
        msg['From'] = formataddr(self.fromEmail)
        msg['To'] = self._toStr(self.toList)
        msg1 = MIMEMultipart("alternative")
        msgText1 = MIMEText("<pre>%s</pre>" % text, "html")
        msgText2 = MIMEText(text)
        msg1.attach(msgText2)
        msg1.attach(msgText1)
        msg.attach(msg1)
        msg = msg.as_string()
        p = Popen(["/usr/sbin/sendmail", "-toi"], stdin=PIPE)
        p.communicate(msg)
        print "FATAL -- %s" % (str(e))

    def _toStr(self, toList):
        names = [formataddr(i) for i in zip(*toList)]
        return ', '.join(names)

#===================================================================================================
#  M A I N   F U N C T I O N
#===================================================================================================
    def crabCall(self, query, attributes=[]):
        data = []
        for scheduler in self.schedulers:
            # query all schedulers, if error retry up to 3 times
            for attempt in range(3):
                try:
                    schedd = htcondor.Schedd(scheduler)
                    jobs = schedd.query(query, attributes)
                    for job in jobs:
                        data.append(job)
                except IOError, e:
                    continue
                else:
                    break
            else:
                self.error(e)
        return data