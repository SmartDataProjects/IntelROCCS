#===================================================================================================
#  C L A S S
#===================================================================================================
import os, subprocess, re, signal, sys, MySQLdb, json
import datetime, time
import phedexDataset

class Alarm(Exception):
    pass

def alarm_handler(signum, frame):
    raise Alarm

class PhedexDataHandler:
    def __init__(self,allSites):
        self.newAccess = False
        self.phedexDatasets = {}
        self.otherDatasets = {}
        self.runAwayGroups = {}
        self.allSites = allSites
        self.epochTime = int(time.time())

    def shouldAccessPhedex(self):
        # number of hours until it will rerun
        renewMinInterval = int(os.environ.get('DETOX_CYCLE_HOURS'))
        statusDir = os.environ['DETOX_DB'] + '/' + os.environ['DETOX_STATUS']
        fileName = statusDir + '/' + os.environ['DETOX_PHEDEX_CACHE']
        if not os.path.isfile(fileName):
            return True
        if not os.path.getsize(fileName) > 0:
            return True

        timeNow = datetime.datetime.now()
        deltaNhours = datetime.timedelta(seconds = 60*60*(renewMinInterval-1))
        modTime = datetime.datetime.fromtimestamp(os.path.getmtime(fileName))
        if (timeNow-deltaNhours) < modTime:
            print "  -- last time cache renewed on " + str(modTime)
            return False
        return True

    def extractPhedexData(self,federation):
        if self.shouldAccessPhedex() :
            try:
                self.retrievePhedexData(federation)
                self.newAccess = True
            except:
                raise
        else:
            print "  -- reading from cache --"

        self.readPhedexData()

    def retrievePhedexData(self,federation):
        phedexDatasets = {}
        webServer = 'https://cmsweb.cern.ch/'
        phedexBlocks = 'phedex/datasvc/json/prod/blockreplicas'
        args = 'show_dataset=y&subscribed=y&' + federation

        url = '"'+webServer+phedexBlocks+'?'+args+'"'
        cmd = 'curl -k -H "Accept: text/xml" ' + url

        print ' Access phedexDb: ' + cmd
        tmpname = os.environ['DETOX_DB'] + '/' + os.environ['DETOX_STATUS'] + '/tmp.txt'
        tmpfile = open(tmpname, "w")

        process = subprocess.Popen(cmd, stdout=tmpfile, stderr=subprocess.PIPE,
                                   bufsize=4096,shell=True)

        signal.signal(signal.SIGALRM, alarm_handler)
        signal.alarm(30*60)  # 30 minutes
        try:
            strout, error = process.communicate()
            tmpfile.close()
            signal.alarm(0)
        except Alarm:
            print " Oops, taking too long!"
            raise Exception(" FATAL -- Call to PhEDEx timed out, stopping")

        if process.returncode != 0:
            print " Received non-zero exit status: " + str(process.returncode)
            raise Exception(" FATAL -- Call to PhEDEx failed, stopping")

        tmpfile = open(tmpname, "r")
        strout = tmpfile.readline()
        tmpfile.close()
        #os.remove(tmpname)
        dataJson = json.loads(strout)
        datasets = (dataJson["phedex"])["dataset"]
        for dset in datasets:
            datasetName = dset["name"]

            user = re.findall(r"USER",datasetName)
            blocks = dset["block"]
            for block in blocks:
                replicas = block["replica"]
                for siterpl in replicas:
                    group = siterpl["group"]
                    if group == 'IB RelVal':
                        group = 'IB-RelVal'

                    site = str(siterpl["node"])
                    if site not in self.allSites:
                        continue

                    if datasetName not in phedexDatasets:
                        phedexDatasets[datasetName] = phedexDataset.PhedexDataset(datasetName)
                    dataset = phedexDatasets[datasetName]

                    size = float(siterpl["bytes"])/1000/1000/1000
                    compl = siterpl["complete"]
                    cust = siterpl["custodial"]
                    subs = int(float(siterpl["time_create"]))
                    made = int(float(siterpl["time_update"]))
                    files = int(siterpl["files"])
                    iscust = 0

                    if len(user) > 0 or cust == 'y':
                        iscust = 1
                    valid = 1
                    #if compl == 'n' and (made-subs) < 60*24*14:
                    #    valid = 0
                    if (self.epochTime-subs) < 60*60*24*14 and compl == 'n':
                        valid = 0
                    dataset.updateForSite(site,size,group,made,files,iscust,valid)

        # Create our local cache files of the status per site
        filename = os.environ['DETOX_PHEDEX_CACHE']
        outputFile = open(os.environ['DETOX_DB'] + '/' + os.environ['DETOX_STATUS'] + '/'
                          + filename, "w")
        for datasetName in phedexDatasets:
            line = phedexDatasets[datasetName].printIntoLine()
            #any dataset line should be above 10 characters
            if len(line) < 10:
                print " SKIPING " + datasetName
                continue
            outputFile.write(line)
        outputFile.close()

    def readPhedexData(self):
        filename = os.environ['DETOX_PHEDEX_CACHE']
        fileName = os.environ['DETOX_DB'] + '/' + os.environ['DETOX_STATUS'] + '/' + filename
	if not os.path.exists(fileName):
	    return phedexDatasets

	inputFile = open(fileName,'r')
        for line in inputFile.xreadlines():
            items = line.split()
            datasetName = items[0]
            group = items[1]
            siteName = items[7]
            size = float(items[3])

            if self.allSites[siteName].getStatus() == 0:
                continue
            if group == 'local':
                continue

            dataset = None
            if group != 'AnalysisOps':
                if datasetName not in self.otherDatasets:
                    self.otherDatasets[datasetName] = phedexDataset.PhedexDataset(datasetName)
                dataset = self.otherDatasets[datasetName]
            else:
                if datasetName not in self.phedexDatasets:
                    self.phedexDatasets[datasetName] = phedexDataset.PhedexDataset(datasetName)
                dataset = self.phedexDatasets[datasetName]
            dataset.fillFromLine(line)
        inputFile.close()

        self.printRunawaySets()

    def getPhedexDatasets(self):
        return self.phedexDatasets

    def getPhedexDatasetsAtSite(self,site):
        dsets = []
        for datasetName in self.phedexDatasets.keys():
            dataset = self.phedexDatasets[datasetName]
            if dataset.isOnSite(site):
                dsets.append(self.phedexDatasets[datasetName])
        return dsets

    def getDatasetsAtSite(self,site):
        dsets = []
        for datasetName in self.phedexDatasets.keys():
            dataset = self.phedexDatasets[datasetName]
            if dataset.isOnSite(site):
                dsets.append(datasetName)
        return dsets

    def getDatasetsByRank(self,site):
        dsets = {}
        for datasetName in self.phedexDatasets.keys():
            dataset = self.phedexDatasets[datasetName]
            if dataset.isOnSite(site):
                dsets[datasetName] = dataset.getLocalRank(site)
        return sorted(dsets,key=dsets.get,reverse=True)


    def renewedCache(self):
        return self.newAccess

    def getRunAwayGroups(self,site):
        groups = []
        if site in self.runAwayGroups:
            groups = self.runAwayGroups[site]
        return groups

    def getRunAwaySets(self,site):
        runAway = {}
        for dset in self.phedexDatasets:
            if dset not in self.otherDatasets:
                continue

            dataset = self.otherDatasets[dset]
            if not dataset.isOnSite(site):
                continue
            group = dataset.group(site)
            runAway[dset] = group
        return runAway

    def printRunawaySets(self):
        siteSizes = {}
        siteSets = {}
        for dset in self.phedexDatasets:
            if dset not in self.otherDatasets:
                continue

            dataset = self.otherDatasets[dset]
            for site in dataset.siteNames:
                group = dataset.group(site)
                size  = dataset.size(site)
                if site not in siteSizes:
                    siteSizes[site] = 0
                    siteSets[site] = 0
                siteSizes[site] = siteSizes[site] + size/1000
                siteSets[site] = siteSets[site] + 1
                if site not in self.runAwayGroups:
                    self.runAwayGroups[site] = [group]
                else:
                    if group not in self.runAwayGroups[site]:
                        self.runAwayGroups[site].append(group)

        if (len(siteSizes) < 1):
            return
        print " !! WARNING !! - those sites have datasets in wrong groups"
        for site in sorted(siteSizes):
            print ' %3d %6.2f TB'%(siteSets[site],siteSizes[site]) + ": " + site



