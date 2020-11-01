# stonkAlerts
Alerts you to a drop in the price of a security (via [telegram](https://telegram.org/)) provided it has a ticker.

![stonks](https://imgur.com/0PIrXXw.jpg)

## How it works
Simply, a telegram message will be sent out if a security's value decreases by more than a given percentage threshold in the past X days (X is specified in the config.json file - an explanation of the file can be found below). The telegram message includes the ticker name and the percentage of the drop.

## Configuration values
* `logFileName` (string) - Name of the log file. Only used if logging is enabled
* `loggingEnabled` (true/false) - Enables or disables the debug logs
* `telegramBotId` (string) - the ID of the [telegram bot](https://core.telegram.org/bots)
* `telegramChatId` (string) - the ID of the telegram chat room to post in
* `precentDropped` (int) - the threshold percentage by which a security must drop (from it's highest point in the past X days where X is the number represented by recentPeak) before the alert is sent
* `recentPeak` (int) - the number of days to look back for the highest price point
* `recentTrend` (int) - the number of days to look back to see if a security is increasing or decreasing in price. No fancy math here, just a simple price comparison - is the price X days ago more than today?
* `tickers` (list of strings) - a list of tickers to look up
