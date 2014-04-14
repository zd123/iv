%pylab inline
import pandas as pd
import numpy as np
import json
from datetime import datetime
from datetime import timedelta
import random
import time
from pandas.tseries.offsets import Hour, Minute


# The formatData function cleans and removes any errors in your file and will return a data frame, csv, or json with the following calcualted metrics:

def formatData():    
    
    def convertEpochTime(z):
        return int(time.mktime(z.timetuple()) * 1000)
    
    pathtofile = "data/march29-texts.txt"
    phoneholder = "Zack DeSario"

    texts = pd.read_csv(pathtofile, delimiter='\t')
    texts.columns = ['direction', 'dt', 'party', 'msg']
    
    texts['Weight'] = texts['msg'].apply(lambda x: len(str(x)))
    texts['Weight'] = texts['Weight'].astype(int)        
    texts = texts[texts.Weight < 500]

    texts['nameLen'] = texts['party'].apply(lambda x: len(str(x)))
    texts = texts[texts.nameLen < 30]
    del texts['nameLen']
    
    texts['incoming'] = texts['direction'].apply(lambda x: 1 if x == "Incoming" else 0)
    texts['outgoing'] = texts['direction'].apply(lambda x: 1 if x == "Outgoing" else 0)

    texts['dayz'] = texts['dt'].apply(lambda x: x.split(" "))
    texts['dayz'] = texts['dayz'].apply(lambda x: x[0])

    texts['dt'] = pd.to_datetime(texts['dt'])
    texts['hr'] = texts['dt'].apply(lambda x: x.strftime('%H'))
    

    texts['shifted'] = texts['dt'].shift(-1)  
    texts['epoch'] = texts['dt'].apply(lambda x: convertEpochTime(x))
    texts['epochShift'] = texts['epoch'].shift(-1)

    texts['dow'] = texts['dt'].apply(lambda x: x.strftime('%a'))
    texts['Id'] = pd.factorize(texts.party)[0]

    texts = texts.set_index(texts.dt)
    return texts


def getBasicTotals():
    data = formatData()
    perPerson = data['direction'].groupby(data.party)
    perPersonVals = perPerson.value_counts().unstack().dropna()
    perPersonVals['Totals'] = perPersonVals.Incoming + perPersonVals.Outgoing
    return perPersonVals

################ BEGINNING OF GET DOUBLE TEXTS DATA ###################
def getDoubleTexts():
    testing = formatData()
    contactList =  testing.party.unique()
    
    for person in contactList:
        testing['whoSent'] = np.where(testing.direction == "Outgoing", "Zack to %s" %person, person )
        testing['timeSinceLast'] = testing['dt'] - testing['shifted']
        testing['epochDiff'] = testing['epoch'] - testing['epochShift']           #testing['dayornight'] = np.where(testing.index.strftime('%')        #testing['epochCumSum'] = testing
        convoPeriod = np.timedelta64(4,'h')
        testing['Convos'] = np.where(testing.timeSinceLast > convoPeriod, "Initiate", "A Response" )
        testing['timeSinceFirst'] = testing.dt - testing.dt[0]
        testing['LoserLap'] = np.where(testing.whoSent == testing.whoSent.shift(1), "Double Text", "SingleText" )                
        del testing['epochShift']
        del testing['shifted']
        return testing
##########################END OF GET INTERESTING DATA ##################################

########## GET COUNTS, RATIOS, AND NORMALIZE EM ################

def getTotalsAndRatios():
    texts = formatData()
    ## this rturns just the count of incoming and outoing msgs for each party
    def getIndividualRatios(data): 
        perPerson = data['direction'].groupby(data.party)
        perPersonVals = perPerson.value_counts().unstack().dropna()
        return perPersonVals

## here are three different normalization methods, choose which one you feel best fit
    def normalizer(df):
        df_norm = (df - df.mean()) / (df.max() - df.min())
        df_norm1 = (df-df.min()) / df.max()
        df_norm2 = df / df.max()
        return df_norm2
    
    countedtexts = getIndividualRatios(texts)
    countedtexts['Ratios'] =  countedtexts.Incoming / (countedtexts.Incoming + countedtexts.Outgoing)    #ratios =  x / (x + y) #counted['ratios'] =  countedtexts.Incoming / (countedtexts.Incoming + countedtexts.Outgoing)
    countedtexts['Totals'] = countedtexts.Incoming + countedtexts.Outgoing 
    countedtexts['IncomingNorm'] = normalizer(countedtexts['Incoming'])
    countedtexts['OutgoingNorm'] = normalizer(countedtexts['Outgoing'])
    countedtexts['TotalsNorm'] = normalizer(countedtexts['Totals']) 
    return countedtexts

################ AT THE GET TOTLAS AND RATIOS #########################

##### THIS SPLITS UP THE DATA, THEN FINDS ALL TIME SENSETIVE DATA FOR EACH PERSON, THEN APPENDS THEM BACK TO GETHER IN THE END #####
def getTimeStatistics():
    masterdf = formatData()
    contactList =  masterdf.party.unique()
    peices = []
    
    ## this computes each indiviudal person's appends it to a list, the concats the list backtogether
    for person in contactList:
        testing = masterdf
        testing = testing[testing.party == person]
        testing['whoSent'] = np.where(testing.direction == "Outgoing", "Zack to %s" %person, person )       ### after parsing the data set to just one party, i label who the sender of the text is per row
    
    ## THIS COL INDICATES HOW LONG IT TOOK FOR THE TEXT MESSAGE TO GET A RESPONSE. 
        testing['timeSinceLast'] = testing['dt'] - testing['shifted']
        testing['epochDiff'] = testing['epoch'] - testing['epochShift']      #testing['epochCumSum'] = testing    #testing['dayornight'] = np.where(testing.index.strftime('%')
    
    ## DEFINING A CONVERSATION PERIOD 
        convoPeriod = np.timedelta64(1,'h')   ## if the timedifference between the last message has been greater than 4 hours, it is marked as a new conversation
        
    ## IF THE RESPONSE TIME FOR THAT MESSAGE IS GREATER THAN THE CONNVO PERIOD, IT INDICATES THAT IS A PART OF A NEW MESSAGE 
        testing['Convos'] = np.where(testing.timeSinceLast > convoPeriod, "Initiate", "A Response" )
        testing['timeSinceFirst'] = testing.dt - testing.dt[0]
       
    ## A DOUBLETEXT IS IF YOU SEND TWO TEXTS IN A ROW WITHOUT A RESPONSE FROM THEM 
        testing['LoserLap'] = np.where(testing.whoSent == testing.whoSent.shift(1), "Double Text", "SingleText" )
        
    ## SHIT IS DOING LIKE A COOL THIN,G BUT DIDN'T FLUSH IT OUT BECAUSE IT WAS A TANGENT
        peices.append(testing)

    concatted = pd.concat(peices)
    return concatted



### THIS CREATES A DICTIONARY FOR EACH CONTACT WITH DESCRIPTIVE STATS, BUT MOSTLY I USED IT FOR FINDING THE RESPONSE TIME FOR EACH PERSON  ####

def buildProfile():
    funnies = getTimeStatistics()
    ##############
    def convertTime(z):
        return int(time.mktime(z.timetuple()) * 1000)

    ##############
    funnies = funnies.set_index(funnies.party)
    mf = funnies
    mf.timeSinceLast = mf.timeSinceLast.astype(int) / 1000000000  ### THIS CONVERTS TO SECONDS
    mf.timeSinceLast = mf.timeSinceLast.astype(int) / 60000000000   ### MINUTES
    mf = mf[mf.party != 'Brian GA']
    ##############


    timeDict = {}
    cl = mf.party.unique()

    for each in cl:
        tempdf = mf[mf.party == each]

        medianIN = tempdf[ (tempdf.Convos == "A Response") & (tempdf.direction == "Incoming") ]['timeSinceLast'].median()
        medianOUT = tempdf[ (tempdf.Convos == "A Response") & (tempdf.direction == "Outgoing") ]['timeSinceLast'].median()
        activeInAVG = tempdf[ (tempdf.Convos == "A Response") & (tempdf.direction == "Incoming") ].groupby(['direction'])['timeSinceLast'].mean()
        activeOutAVG = tempdf[ (tempdf.Convos == "A Response") & (tempdf.direction == "Outgoing") ].groupby(['direction'])['timeSinceLast'].mean() 
        aim = activeInAVG.values[0] if activeInAVG.values else 0
        aom = activeOutAVG.values[0] if activeOutAVG.values else 0

        InitInCNT = tempdf[ (tempdf.Convos == "Initiate") & (tempdf.party == each) & (tempdf.direction == "Incoming")].groupby(['direction'])['timeSinceLast'].count()
        InitOutCNT = tempdf[ (tempdf.Convos == "Initiate") & (tempdf.party == each) & (tempdf.direction == "Outgoing")].groupby(['direction'])['timeSinceLast'].count()
        iic = InitInCNT.values[0] if InitInCNT.values else 0

        ioc = InitOutCNT.values[0] if InitOutCNT.values else 0

        
        initiateAvgIn = tempdf[ (tempdf.Convos == "Initiate") & (tempdf.party == each) & (tempdf.direction == "Incoming")].groupby(['direction'])['timeSinceLast'].mean()
        initiateAvgOut = tempdf[ (tempdf.Convos == "Initiate") & (tempdf.party == each) & (tempdf.direction == "Outgoing")].groupby(['direction'])['timeSinceLast'].mean()
        imi = initiateAvgIn.values[0] if initiateAvgIn.values else 0
        imo = initiateAvgOut.values[0] if initiateAvgOut.values else 0
        
        
        firstResponseIn = tempdf[(tempdf.party == each) & (tempdf.direction == "Incoming")].groupby(['direction'])['dt'].min()
        firstResponseOut = tempdf[(tempdf.party == each) & (tempdf.direction == "Outgoing")].groupby(['direction'])['dt'].min()
        fri = firstResponseIn.values[0] if firstResponseIn.values else 0
        fro = firstResponseOut.values[0] if firstResponseOut.values else 0
        lastResponseIn = tempdf[(tempdf.party == each) & (tempdf.direction == "Incoming")].groupby(['direction'])['dt'].max()
        lastResponseOut = tempdf[(tempdf.party == each) & (tempdf.direction == "Outgoing")].groupby(['direction'])['dt'].max()
        lri = lastResponseIn.values[0] if lastResponseIn.values else 0
        lro = lastResponseOut.values[0] if lastResponseOut.values else 0
        
        doubleCountIn = tempdf[ (tempdf.LoserLap == "Double Text") & (tempdf.party == each) & (tempdf.direction == "Incoming")].groupby(['direction'])['timeSinceLast'].count()
        doubleCountOut = tempdf[ (tempdf.LoserLap == "Double Text") & (tempdf.party == each) & (tempdf.direction == "Outgoing")].groupby(['direction'])['timeSinceLast'].count()
        dci = doubleCountIn.values[0] if doubleCountIn.values else 0
        dco = doubleCountOut.values[0] if doubleCountOut.values else 0
        timeDict[each] = {"name": each, \
                          "InitiateIN": iic, \
                          "InitiateOUT": ioc, \
                          "ActiveIN": aim, \
                          "ActiveOUT": aom,  \
                          "DoubleIN": dci, \
                          "DoubleOUT": dco, \
                          "MedianIN": medianIN, \
                          "MedianOUT": medianOUT, \
                          }
    
    return timeDict

#### THIS IS CHARACTERIZING BY GROUPS,  MUST MANUALLY MARK EACH PERSON IN YOUR DATA AS MALE, FEMALE, FAMILY, OR IDK (FOR I DONT KNOW WHO)
def groupStats():    
    ##############
    def getSex():
        pathtofile = "data/sex.csv"
        sexes = pd.read_csv(pathtofile, delimiter=',')
        return sexes
    
    gotSex = getSex()
    gotSex = gotSex.set_index(gotSex.party)
    ##############
    
    ##############
    def convertTime(z):
        return int(time.mktime(z.timetuple()) * 1000)
    ##############
    
    ##############
    funnies = getTimeStatistics()
    funnies = funnies.set_index(funnies.party)
    mf = pd.merge(gotSex, funnies)
    ##############
    
    
    ### CONVERTING THE TIME DIFF TO HOURS
    mf.timeSinceLast = mf.timeSinceLast.astype(int)
    mf.timeSinceLast = mf.timeSinceLast.astype(int) / 60000000000   ### MINUTES
    mf = mf[mf.party != 'Charley']
    mf = mf[mf.party != 'Brian GA']
    ##############
    
    returnStats = []
    ##############
    #### THESE GIVE US THE AVERAGE RESPOSE TIME PER GROUP FOR EITHER A CONVERSATION, AND ALSO THE NUMBERS OF REACH OUTS ####
    activeConvoAVG = mf[mf.Convos == "A Response"].groupby(['Sex','direction'])['timeSinceLast'].mean()   #mf[mf.Convos == "A Response"].groupby(['party','direction'])['timeSinceLast'].mean()
    activeConvoCNT = mf[mf.Convos == "A Response"].groupby(['Sex','direction'])['timeSinceLast'].count()
    newConvoAVG = mf[mf.Convos == "Initiate"].groupby(['Sex','direction'])['timeSinceLast'].mean()
    newConvoCNT = mf[mf.Convos == "Initiate"].groupby(['Sex','direction'])['timeSinceLast'].count()
    doubleTexts = mf[ (mf.LoserLap == "Double Text")].groupby(['Sex','direction'])['timeSinceLast'].count()
    returnStats.append([activeConvoAVG, activeConvoCNT, newConvoAVG, doubleTexts])
    return returnStats
    
################ BEGINNING OF GET SPARKLINE DATA FOR THE NETWORK GRRAPH #########################
def formatForGephi():
    def convertTime(z):
        return int(time.mktime(z.timetuple()) * 1000)
    
    data = formatData()
    data = data.sort('dt', 'party')
    sparkline = data[['Weight', 'Id','party','dt']]
    sparkline['epo'] = sparkline['dt'].apply(lambda x: convertTime(x))
    sparkline['PID-INT'] = sparkline.Id * 10
    sparkline = sparkline.reset_index(drop=True)
    sparkline['order'] = sparkline.index
    sparkline['shiftedOrder'] = sparkline.order.shift(1)
    sparkline['nodeId'] = sparkline.party
    sparkline['shiftednodeId'] = sparkline.nodeId.shift(1)   
    sparkline['Source'] = sparkline.order
    sparkline['Target'] = np.where(sparkline.nodeId == sparkline.shiftednodeId, sparkline.shiftedOrder, sparkline.order)
    sparkline['Target'] = sparkline['Target'].astype(int)
    sparkline['factorizedId'] =  sparkline['Id']
    del sparkline['Id']
    sparkline['Id'] = sparkline.order
    del sparkline['shiftedOrder']
    del sparkline['shiftednodeId']
    del sparkline['nodeId']   
    sparkline = sparkline.set_index(sparkline.party)
    edgetable = sparkline[['Id', 'Source', 'Target','party']]
    return sparkline

################ END OF GET SPARKLINE DATA #########################

# <codecell>


