#!/bin/bash
# --------------------------------------------------------------------------------------------------
#
# This script will extract all relevant log file monitoring data from the present log files and
# prepare them for further monitoring display.
#
#                                                                             C.Paus (June 10, 2014)
# --------------------------------------------------------------------------------------------------
# check if detox package is properly setup
# calling 
#   monitor.sh 1
# will compute nSitesAv instead of nSites
if [ -z "$DETOX_DB" ] || [ -z "$MONITOR_DB" ]
then
  echo " ERROR - logfile base not defined: DETOX_DB = \"$DETOX_DB\"  MONITOR_DB = \"$MONITOR_DB\""
  exit 0
fi

cd $MONITOR_DB #preventing temp files from being created in weird places

# are we interested in nSites or nSitesAv
average=1
if [ -z $1 ]
then
  average="1"
else
  average=$1
fi
# define relevant environment variables
export MIT_ROOT_STYLE=/home/cmsprod/MitRootStyle/MitRootStyle.C
export SITE_MONITOR_FILE=$MONITOR_DB/MonitorSummary.txt
rm -f $SITE_MONITOR_FILE
touch $SITE_MONITOR_FILE
#echo "# Site Quota Used ToDelete LastCp" >> $SITE_MONITOR_FILE

echo ""
echo "Extracting log file monitoring data from DETOX_DB = $DETOX_DB."
echo ""

# find present site quotas
for site in `ls -1 $DETOX_DB/$DETOX_RESULT | grep ^T[0-3]`
do

#  echo " Analyzing site : $site"
  quota=`grep 'Total Space' $DETOX_DB/$DETOX_RESULT/$site/Summary.txt|cut -d: -f2|tr -d ' '`
  used=`grep 'Space Used' $DETOX_DB/$DETOX_RESULT/$site/Summary.txt|cut -d: -f2|tr -d ' '`
  toDelete=`grep 'Space to delete' $DETOX_DB/$DETOX_RESULT/$site/Summary.txt|cut -d: -f2|tr -d ' '`
  lastCp=`grep 'Space last CP' $DETOX_DB/$DETOX_RESULT/$site/Summary.txt|cut -d: -f2|tr -d ' '`
  echo "$site $quota $used $toDelete $lastCp" >> $SITE_MONITOR_FILE

done
# make nice histograms
pwd
 root -q -b -l $MONITOR_BASE/plotSites.C
echo "Done making site plots"

# extract dataset info
let interval=$(date --date=$(date +"%m/%d/%Y") +%s)-1378008000
$MONITOR_BASE/readJsonSnapshotAll.py T2*
export DATASET_MONITOR_TEXT="since 09/2013"
  mv DatasetSummary.txt DatasetSummaryAll.txt
  export DATASET_MONITOR_FILE=DatasetSummaryAll
root -q -b -l $MONITOR_BASE/plotDatasets.C\("$average",$interval\)

start=$(date --date=01/01/2014 +%s)
end=$(date --date=$(date +"%m/%d/%Y") +%s)
let interval=end-start
# let interval=$(date --date=$(date +"%m/%d/%Y") +%s)-$(date --date=01/01/2014 +%s)
$MONITOR_BASE/readJsonSnapshotAll.py T2* $start $end
export DATASET_MONITOR_TEXT="Summary 2014"
  mv DatasetSummary.txt DatasetSummary2014.txt
  export DATASET_MONITOR_FILE=DatasetSummary2014
root -q -b -l $MONITOR_BASE/plotDatasets.C\("$average",$interval\)

month=`date +%m`
for period in $(seq 01 $month) 
do 
  if [[ ${#period}<2 ]] 
  then 
    period=0$period 
  fi 
  case $period in
    0[13578] | 1[02] ) 
      lastday=31;;
    0[469] | 11 )
      lastday=30;;
    02 )
      lastday=28;;
  esac
  start=$(date --date=01/${period}/2014 +%s)
  end=$(date --date=${period}/${lastday}/2014 +%s)
  let interval=end-start
  # let interval=$(date --date=${period}/${lastday}/2014 +%s)-$(date --date=${period}/01/2014 +%s)
  $MONITOR_BASE/readJsonSnapshotAll.py T2* $start $end
  export DATASET_MONITOR_TEXT="${period}/2014"
    mv DatasetSummary.txt DatasetSummary${period}-2014.txt
    export DATASET_MONITOR_FILE=DatasetSummary${period}-2014
  root -q -b -l $MONITOR_BASE/plotDatasets.C\("$average",$interval\)
done


# move the results to the log file area ( to be updated to the monitor areas )
mkdir -p    $MONITOR_DB
mv    *.txt $MONITOR_DB
mv    *.png $MONITOR_DB

exit 0
