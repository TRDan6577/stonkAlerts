#!/usr/bin/python3
#File: stonkAlerts.py
#Author: Tom Daniels <github.com/trdan6577>

#############
## Imports ##
#############
import datetime
import json
import logging
import requests
import yfinance


#################
## Global Vars ##
#################
OK = 200
TODAY = -1


###############
## Functions ##
###############
def send_message(botID, chatID, message, debug):
    """
    Purpose: Sends a telegram message. Docs: https://core.telegram.org/bots/api#sendmessage
    @param   botID (string) - the ID of the bot to use
    @param   chatID (string) - the ID of the target chat to use
    @param   message (string) - the message to send
    @param   debug (bool) - enabled if we're logging messages
    @return  bool - true if the message was sent, false otherwise
    """
    
    # Turn on logging if specified
    if (debug):
        logger = logging.getLogger()
        logger.debug("Entering send_message. Parameters are:\n\tChatId: {0}\n\tBotID: {1}\n\tMessage: {2}".format(botID, chatID, message))
    
    # Build the URI based off of the bot ID and set the body
    uri = 'https://api.telegram.org/bot{0}/sendMessage'.format(botID)
    body = {'text': message}
    body['chat_id'] = chatID
    
    # Send the message
    try:
        response = requests.post(uri, data=body)
        messageSent = True if response.status_code == OK else False
    except Exception as e:
        messageSent = False
        if (debug):
            logger.error("Error sending the telegram message. Error: '{0}'".format(repr(e)))
    
    return messageSent


def create_ticker_message(tickers, recentPeak, recentTrend, precentDroppedThreshold, debug):
    """
    Purpose: Provided today's closing value is less than the closing value
             X days ago (where X is recentTrend), return a message with
             information about the ticker history if the security dropped by
             at least the amount specified in precentDroppedThreshold
    @param   tickers (list)    - a list of strings that contain the symbol of the security
             to get information about
    @param   recentPeak (int)  - the number of days to look back, searching for the higest
             closing value for the particular ticker
    @param   recentTrend (int) - the number of days to look back to determine if a security
             is rising or falling. If the closing value for today minus closing value for
             X days ago (where X is recentTrend) is negative, then we're likely on a downward trend
    @param   precentDroppedThreshold (int) - the threshold for the percentage of loss of the given
             ticker. If the percentage loss between the highest point in the last X
             days and today is greater than or equal to precentDroppedThreshold, create the message
    @param   debug (bool) - enabled if we're logging mesages
    @return  (string) - if the precentDroppedThreshold is reached, returns a message with
             the percentage lost, highest value in <recentPeak> days, and current
             closing value
    """

    # Turn on logging if specified
    if (debug):
        logger = logging.getLogger()
        logger.debug("Entering create_ticker_message. Parameters are:\n\tTickers: {0}\n\tRecentPeak: {1}\n\tRecentTrend: {2}\n\tprecentDroppedThreshold: {3}".format(tickers, recentPeak, recentTrend, precentDroppedThreshold))

    # Iterate through the tickers building the message to be sent
    message = ''
    for ticker in tickers:

        if (debug):
            logger.debug("Working on ticker '{0}'".format(ticker))

        # Get the history of the ticker for the past <recentPeak> days
        try:
            history = yfinance.Ticker(ticker).history(start=(datetime.datetime.now() - datetime.timedelta(days=recentPeak)))
        except Exception as e:
            if (debug):
                logger.error("Failed to retrieve prices for ticker '{0}'. Error: '{1}'".format(ticker, repr(e)))
            continue

        # Check to make sure we're on a downward trend
        if (history.Close[-recentTrend] < history.Close[TODAY]):
            if (debug):
                logger.debug("Current price ({0}) is higher than {1} days ago ({2}). Skipping ticker '{3}'".format(history.Close[TODAY], recentTrend, history.Close[-recentTrend], ticker))
            continue

        # Find the highest price in the last <recentPeak> days
        maxPrice = 0
        priceToday = history.Close[-1]
        for price in history.Close:
            if (price > maxPrice):
                maxPrice = price
        if (debug):
            logger.debug("Max Price: {0}; Price Today: {1}".format(maxPrice, priceToday))
        
        # Add to the message if the security dropped below our threshold
        percentDropped = ((priceToday - maxPrice)/maxPrice) * 100
        if (debug):
            logger.debug("PercentDropped: {0}%".format(percentDropped))
        if (percentDropped < -precentDroppedThreshold):
            message += "{0} dropped {1}%\n".format(ticker, round(-percentDropped, 2))
    
    return message


def main():
    """
    Purpose: Loads the config and send a telegram message if any ticker
             dropped by a given amount in a specified time period
    @return  int - 0 on success and -1 on failure
    """
    
    # Load the configuration
    try:
        with open("config.json") as f:
            config = json.load(f)
    except Exception as e:
        print("Failed to load the configuration file (config.json). Error: '{0}'".format(repr(e)))
        return -1
    
    # Set up logging if it's enabled
    if (config["loggingEnabled"]):
        try:
            logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s",filename=config['logFileName'],filemode='a')
            logger = logging.getLogger()
            logger.setLevel(10)
        except Exception as e:
            print("Failed to set up logging. Error: '{0}'".format(repr(e)))
            return -1
    
    # Validate the configuration
    assert config['recentPeak'] >= config['recentTrend'], "RecentPeak must be greater than or equal to recentTrend"

    # Create a message to send based on which tickers dropped below the threshold
    # Message is an empty string if no ticker crossed the threshold
    message = create_ticker_message(config['tickers'], config['recentPeak'], config['recentTrend'], config['percentDropped'], config["loggingEnabled"])
    
    # Notify via telegram if any dropped
    if (message):
        
        if (config["loggingEnabled"]):
            logger.debug("Attempting to send message '{0}'...".format(message))
        
        if (send_message(config['telegramBotId'], config['telegramChatId'], message, config["loggingEnabled"])):
            return 0   # We successfuly sent the message
        else:
            return -1  # We weren't successful in sending the message
    else:
        # Check to see if there's problem with the API
        try:
            assert (yfinance.Ticker("SPY")), "Error interacting with API"
        except Exception as e:
            if (config["loggingEnabled"]):
                logger.critical("Failed to reach Yahoo Finance API. Error: {0}".format(repr(e)))
            send_message(config['telegramBotId'], config['telegramChatId'], "Failed to reach Yahoo Finance API. Error: {0}".format(repr(e)), config["loggingEnabled"])
            return -1

    # No message to send
    return 0

main()