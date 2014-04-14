Iv
==

The insecurity validator

“””  
This is the ‘insecurity validator’ app source file
Process text message data to inspect if you are crazy or...
Statistically, they are just not that into you.

First, you need to your data from your cell phone
You can get ghetto and get it yourself by following this tutorial < http://www.Iphone-sms.Com/ >
I used diskaid.App which costs 20 buck.

The raw data should be tab separated, without a header:

    The first column is the direction: outgoing or incoming
    The second column is the datetime:  mm/dd/yyyy hh:mm:ss
    The third column is the contact’s name: dad
    The fourth column is the msg itself:  Hey dudes, I am soo secure with my validity

Here is an example line of how the raw data should look going in:
    
    Outgoing    03/29/2014 16:42:50 sophia sf   how did the hipster burn his tongue?

In the script, each column is called:  [‘direction’, ‘dt’, ‘party’, ‘msg’]



Once you have your data, just set the variable named:

    pathtofile = “data/texts.csv”

Where the "data/texts.csv" is whereever your data file is.



Run the script, and upon completion, you will have access to the following metrics via the functions listed below:



    def formatData():
    def getBasicTotals():
    def getTotalsAndRatios():
    def getDoubleTexts():
    def getTimeStatistics():
    def buildProfile():
    def groupStats():
    def formatForGephi():
    
![Alt text](/screenshots/buildProfile.png "Optional title")
