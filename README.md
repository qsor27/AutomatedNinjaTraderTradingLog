# AutomatedNinjaTraderTradingLog
Automatically exports NinjaTrader Trade Performance report and parses into an XLSX sheet.

Requirements:

-- Autoit https://www.autoitscript.com/cgi-bin/getfile.pl?autoit3/autoit-v3-setup.zip

-- Python https://www.python.org/ftp/python/3.12.5/python-3.12.5-amd64.exe

-- pip3 install pandas, openpyxl


The AutoIt Script is currently unreliable, Its recommended to manually export the Trade Performance Report:
New > Trade Performance > Display Dropdown (Trades (pts)) > Date Range Today to Today > Generate > Righ Click background underneath data > Export... Save as CSV to data folder

Run Python.exe .\TradePerformanceGenerator.py
