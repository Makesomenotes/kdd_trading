# pip install yfinance --upgrade --no-cache-dir
# pip install pandas_datareader


import datetime
import requests
import time


import pandas as pd
import pandas_datareader.data as web


import yfinance as yf


from dateutil.relativedelta import relativedelta


today = datetime.datetime.now().date()
oldest_day = today - relativedelta(years=2)


# getting list of tickers of companies from S&P500
table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
df = table[0]
df.to_csv('S&P500-Info.csv')
df.to_csv("S&P500-Symbols.csv", columns=['Symbol'])


list_of_tickers = df.Symbol


# uploading prices of S&P500 over the last 2 years
SP500 = web.DataReader(['sp500'], 'fred', oldest_day, today)


# creating feature matrix
total_df = pd.DataFrame()
bad_count = 0
for ticker in list_of_tickers:
    # request data
    company = yf.Ticker(ticker)
    df_quarterly_financials = company.quarterly_financials
    df_quarterly_balance_sheet = company.quarterly_balance_sheet
    df_quarterly_cashflow = company.quarterly_cashflow
    df_earnings = company.quarterly_earnings
    hist = company.history(period="2y")

    # time
    start = df_quarterly_cashflow.columns[3]
    future_date = start + datetime.timedelta(days=252)
    finish = start + datetime.timedelta(days=252) if future_date <= today else today

    # variables
    try:
        total_liab = df_quarterly_balance_sheet.loc['Total Liab'][start]
        total_equity = df_quarterly_balance_sheet.loc['Total Stockholder Equity'][start]
        total_assets = df_quarterly_balance_sheet.loc['Total Assets'][start]
        current_assets = df_quarterly_balance_sheet.loc['Total Current Assets'][start]
        cash = df_quarterly_balance_sheet.loc['Cash'][start]
        net_income = df_quarterly_cashflow.loc['Net Income'][start]
        earnings = df_earnings['Earnings'][0]
        number_of_stocks = df_quarterly_balance_sheet.loc['Common Stock'][start]
        start_close = hist.loc[start]['Close']
        finish_close = hist.loc[finish]['Close']
        operating_cashflow = df_quarterly_cashflow.loc['Total Cash From Operating Activities'][start]
        interest_expense = df_quarterly_financials.loc['Interest Expense'][start]
        ebit = df_quarterly_financials.loc['Ebit'][start]
        total_revenue = df_quarterly_financials.loc['Total Revenue'][start]
    except KeyError:
        bad_count += 1
        print(f'Bad company {ticker}. Overall number {bad_count}')
        continue

    # ratios
    try:
        # https://www.investopedia.com/terms/d/debtequityratio.asp
        debt_to_equity = total_liab / total_equity

        # https://www.investopedia.com/terms/c/currentratio.asp
        current_ratio = current_assets / total_liab

        # https://www.investopedia.com/terms/c/cash-ratio.asp
        cash_ratio = cash / total_liab

        # https://www.investopedia.com/terms/r/returnonassets.asp
        return_on_assets = net_income / total_assets

        # https://www.investopedia.com/terms/e/eps.asp
        eps = earnings / number_of_stocks

        # https://www.investopedia.com/terms/p/price-to-salesratio.asp
        price_to_sales = start_close / finish_close

        # https://www.investopedia.com/terms/p/price-to-cash-flowratio.asp
        price_to_cashflow = start_close / (operating_cashflow / number_of_stocks)

        # https://www.investopedia.com/terms/s/shareholderequityratio.asp
        shareholder_equity = total_equity / total_assets

        # https://www.investopedia.com/terms/i/interestcoverageratio.asp
        interest_coverage = ebit / interest_expense

        # https://www.investopedia.com/terms/n/net_margin.asp
        net_profit_margin = net_income / total_revenue

    except TypeError:
        bad_count += 1
        print(f'Bad company {ticker}. Overall number {bad_count}')
        continue

    # targets
    regression_target = start_close / finish_close  # prrice_change, regression
    target = (regression_target < 1)  # overweight, for classification
    SP_change = SP500.loc[start]['sp500'] / SP500.loc[finish]['sp500']
    SP_target = SP_change > regression_target  # overweight, for classification

    df_company = pd.DataFrame(
        {'debt_to_equity': debt_to_equity, 'current_ratio': current_ratio, 'cash_ratio': cash_ratio,
         'return_on_assets': return_on_assets, 'eps': eps, 'price_to_sales': price_to_sales,
         'price_to_cashflow': price_to_cashflow, 'shareholder_equity': shareholder_equity,
         'interest_coverage': interest_coverage, 'net_profit_margin': net_profit_margin,
         'regression_target': regression_target, 'target': target, 'SP_target': SP_target}, index=[ticker])

    total_df = pd.concat([total_df, df_company])
    # print(ticker, len(total_df))
    time.sleep(1)


# In the end, bad_count = 152
