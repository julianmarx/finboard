import streamlit as st
import pandas as pd
from yahoo_fin import stock_info as si
import datetime as dt

def get_integer(number):
    number_lst = list(number)
    if number_lst[-1] == 'T':
        number_lst.pop(-1)
        number_lst.append((15-(len(number_lst)-number_lst.index('.'))-2)*'0')
        number_lst.pop(number_lst.index('.'))
        return int(''.join(number_lst))
    if number_lst[-1] == 'B':
        number_lst.pop(-1)
        number_lst.append((12-(len(number_lst)-number_lst.index('.'))-2)*'0')
        number_lst.pop(number_lst.index('.'))
        return int(''.join(number_lst))
    if number_lst[-1] == 'M':
        number_lst.pop(-1)
        number_lst.append((9-(len(number_lst)-number_lst.index('.'))-2)*'0')
        number_lst.pop(number_lst.index('.'))
        return int(''.join(number_lst))
    
class Company:
    def __init__(self, ticker):
        price_df = si.get_data(ticker, dt.datetime.now()-dt.timedelta(days=2*365), dt.datetime.date(dt.datetime.now()))
        overview_df = si.get_stats(ticker)
        overview_df = overview_df.set_index('Attribute')
        overview_dict = si.get_quote_table(ticker)
        income_statement = si.get_income_statement(ticker)
        balance_sheet = si.get_balance_sheet(ticker)
        cash_flows = si.get_cash_flow(ticker)

        self.year_end = overview_df.loc['Fiscal Year Ends'][0]
        self.market_cap = get_integer(overview_dict['Market Cap'])
        self.market_cap_cs = '{:,d}'.format(int(self.market_cap))
        self.prices = price_df['adjclose']

        self.sales = income_statement.loc['totalRevenue'][0]
        self.gross_profit = income_statement.loc['grossProfit'][0]
        self.ebit = income_statement.loc['ebit'][0]
        self.interest = - income_statement.loc['interestExpense'][0]
        self.net_profit = income_statement.loc['netIncome'][0]

        self.assets = balance_sheet.loc['totalAssets'][0]
        self.currenta = balance_sheet.loc['totalCurrentAssets'][0]
        self.currentl = balance_sheet.loc['totalCurrentLiabilities'][0]
        self.working_cap = self.currenta - self.currentl
        try:                                                                                                    # Apologies for the pathetic error handling
            self.debt = balance_sheet.loc['shortLongTermDebt'][0] + balance_sheet.loc['longTermDebt'][0]
        except Exception:
            self.debt = balance_sheet.loc['longTermDebt'][0]
        self.cash = balance_sheet.loc['cash'][0]
        self.net_debt = self.debt - self.cash
        try:
            self.inventory = balance_sheet.loc['inventory'][0]
        except Exception:
            self.inventory = 'NaN'
        self.receivables = balance_sheet.loc['netReceivables'][0]
        self.payables = balance_sheet.loc['accountsPayable'][0]
        self.equity = balance_sheet.loc['totalStockholderEquity'][0]
        self.ev = self.market_cap + self.net_debt
        self.ev_cs = '{:,d}'.format(int(self.ev))

        self.operating_cf = cash_flows.loc['totalCashFromOperatingActivities'][0]
        self.investing_cf = cash_flows.loc['totalCashflowsFromInvestingActivities'][0]
        self.financing_cf = cash_flows.loc['totalCashFromFinancingActivities'][0]
        self.capex = - cash_flows.loc['capitalExpenditures'][0]
        self.free_cash_flow = self.operating_cf - self.capex

    def get_overview(self):
        self.price_earnings_ratio = self.market_cap/self.net_profit
        self.ev_sales_ratio = self.ev/self.sales
        self.overview_dict = {
            'Values' : [self.ev_cs, self.market_cap_cs, self.ev_sales_ratio, self.price_earnings_ratio]
            }
    
    def get_profit_margins(self):
        self.gross_margin = self.gross_profit/self.sales
        self.operating_margin = self.ebit/self.sales
        self.net_margin = self.net_profit/self.sales
        self.profit_margin_dict = {
            'Values' : [self.gross_margin, self.operating_margin, self.net_margin]
            }
    
    def get_liquidity_ratios(self):
        self.current_ratio = self.currenta/self.currentl
        if self.inventory != 'NaN':
            self.quick_ratio = (self.currenta - self.inventory)/self.currentl
        else:
            self.quick_ratio = 0
        self.cash_ratio = self.cash/self.currentl
        self.liquidity_ratio_dict = {
            'Values' : [self.current_ratio, self.quick_ratio, self.cash_ratio]
            }

    def get_leverage_ratios(self):
        self.debt_ratio = self.debt/self.assets
        self.debt_equity_ratio = self.debt/self.equity
        self.interest_coverage_ratio = self.ebit / self.interest
        self.leverage_ratio_dict = {
            'Values' : [self.debt_ratio, self.debt_equity_ratio, self.interest_coverage_ratio]
            }
        
    def get_efficiency_ratios(self):
        self.asset_turnover = self.sales/self.assets
        self.receivables_turnover = self.sales/self.receivables
        if self.inventory != 'NaN':
            self.inventory_turnover = (self.sales-self.gross_profit)/self.inventory
        else:
            self.inventory_turnover = 0
        self.efficiency_ratio_dict = {
            'Values' : [self.asset_turnover, self.receivables_turnover, self.inventory_turnover]
            }

st.title('Financial Dashboard')
ticker_input = st.text_input('Please enter your company ticker:')
search_button = st.button('Search')

if search_button:
    company = Company(ticker_input)
    company.get_overview()
    company.get_profit_margins()
    company.get_liquidity_ratios()
    company.get_leverage_ratios()
    company.get_efficiency_ratios()

    st.header('Company overview')
    overview_index = ['Enterprise value', 'Market cap', 'EV/sales ratio', 'P/E ratio']
    overview_df = pd.DataFrame(company.overview_dict, index = overview_index)
    st.line_chart(company.prices)
    st.table(overview_df)

    with st.beta_expander('Profit margins (as of {})'.format(company.year_end)):
        profit_margin_index = ['Gross margin', 'Operating margin', 'Net margin']
        profit_margin_df = pd.DataFrame(company.profit_margin_dict, index = profit_margin_index)
        st.table(profit_margin_df)
        st.bar_chart(profit_margin_df)

    with st.beta_expander('Liquidity ratios (as of {})'.format(company.year_end)):  
        liquidity_ratio_index = ['Current ratio', 'Quick ratio', 'Cash ratio']
        liquidity_ratio_df = pd.DataFrame(company.liquidity_ratio_dict, index = liquidity_ratio_index)
        st.table(liquidity_ratio_df)
        st.bar_chart(liquidity_ratio_df)

    with st.beta_expander('Leverage ratios (as of {})'.format(company.year_end)):
        leverage_ratio_index = ['Debt/total assets ratio', 'Debt/equity ratio', 'Interest coverage ratio']
        leverage_ratio_df = pd.DataFrame(company.leverage_ratio_dict, index = leverage_ratio_index)
        st.table(leverage_ratio_df)
        st.bar_chart(leverage_ratio_df)

    with st.beta_expander('Efficiency ratios (as of {})'.format(company.year_end)):
        efficiency_ratio_index = ['Asset turnover', 'Receivables turnover', 'Inventory turnover']
        efficiency_ratio_df = pd.DataFrame(company.efficiency_ratio_dict, index = efficiency_ratio_index)
        st.table(efficiency_ratio_df)
        st.bar_chart(efficiency_ratio_df)