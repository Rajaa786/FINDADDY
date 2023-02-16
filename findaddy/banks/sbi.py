import os
import pandas as pd
import numpy as np
import datefinder
import re
import calendar
import pdfplumber

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)


class SBI:
    def __init__(self, file_name, password, startdate, enddate):
        self.file_name = file_name
        self.passwd = password
        self.startdate = startdate
        self.enddate = enddate
        self.valid = True
        self.df_total = pd.DataFrame()
        excel_folder = os.path.join(os.getcwd(), 'Excel_Files')
        # create excel folder if it does not exist
        if not os.path.exists(excel_folder):
            os.makedirs(excel_folder)
        else:
            # delete existing files
            for file in os.listdir(excel_folder):
                file_path = os.path.join(excel_folder, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(e)
        excel_loc = os.path.join(excel_folder, 'BankStatement.xlsx')

        self.Excel_File = pd.ExcelWriter(
            excel_loc, engine='openpyxl')
        self.show()

    def validation(self):
        try:
            # if self.passwd == '':
            #   pdf=pdfplumber.open(self.file_name)
            #   self.valid=True
            # else:
            self.pdf = pdfplumber.open(self.file_name, password=self.passwd)
            self.valid = True
        except Exception as e:
            print('PDF has Password')
            print(e)
            self.valid = False

    def extract(self):
        # pdf = pdfplumber.open(self.file_name, password=self.passwd)
        # if self.passwd == '':
        #   pdf=pdfplumber.open(self.file_name)
        # else:
        #   pdf=pdfplumber.open(self.file_name, password =self.passwd)
        pdf = self.pdf
        for i in range(len(pdf.pages)):
            p0 = pdf.pages[i]
            table = p0.extract_table()
            self.df_total = self.df_total.append(table, ignore_index=True)
            self.df_total.replace({r'\n': ' '}, regex=True, inplace=True)

        self.df_total = self.df_total.drop_duplicates()
        self.Index()
        self.df_total = self.df_total.replace(np.nan, '', regex=True)
        uniqueValues = self.df_total[self.date_index].unique()
        z = uniqueValues.tolist()
        z.pop(0)
        z.pop(0)
        l = len(self.df_total.columns)-1
        check = self.df_total[[self.date_index]]
        check = check.iloc[2:]
        check.columns = check.columns.astype(str)
        check.columns.values[0] = 'Date'
        check = check.reset_index(drop=True)
        check = check.drop_duplicates(subset=['Date'], keep='last')
        # eod dataframe with day, month, year columns

        def monthcheck(y):
            date = y['Date']
            matches = datefinder.find_dates(date)
            for match in matches:
                if date[3:5].isnumeric():
                    month = int(date[3:5])
                else:
                    month = int(match.month)
                return month
                break
        print('Error')
        check['Month'] = check.apply(monthcheck, axis=1, result_type="expand")
        ch = check['Month'].unique().tolist()

        def order(A):
            reverse = 0
            for i in range(1, len(A)):
                if (int(A[i-1]) == 1) and (int(A[i]) == 12):
                    reverse = 1
                elif (int(A[i-1]) == 12) and (int(A[i]) == 1):
                    reverse = 2

            if reverse == 1:
                return 'Descending'
            elif reverse == 2:
                print('A')
                return 'Ascending'
            else:
                if A == sorted(A, reverse=False):
                    return 'Ascending'
                elif A == sorted(A, reverse=True):
                    return 'Descending'
                else:
                    return 'Neither'

        if order(ch) == 'Descending':
            self.df_total = self.df_total.iloc[::-1]
            self.df_total = self.df_total.apply(np.roll, shift=1)
            self.df_total = self.df_total.reset_index(drop=True)

        self.df_total.to_excel(
            self.Excel_File, sheet_name="Transaction", index=False)
        # self.Excel_File.save()

    def EOD(self):
        print('start eod')
        uniqueValues = self.df_total[self.date_index].unique()
        z = uniqueValues.tolist()
        z.pop(0)
        z.pop(0)
        l = len(self.df_total.columns)-1
        x = self.df_total[[self.date_index, self.bal_index]]
        x = x.iloc[2:]
        x.columns = x.columns.astype(str)
        x.columns.values[0] = 'Date'
        x.columns.values[1] = 'EOD'
        x = x.reset_index(drop=True)
        x = x.drop_duplicates(subset=['Date'], keep='last')
        print('month')
        # eod dataframe with day, month, year columns

        def month(y):
            if y['EOD'] == '' or y['Date'] == '':
                return 0, 0, 0
            else:
                date = y['Date']
            matches = datefinder.find_dates(date)
            for match in matches:
                if date[3:5].isnumeric():
                    days = int(date[0:2])
                    month = int(date[3:5])
                else:
                    days = int(match.day)
                    month = int(match.month)
                years = int(match.year)
                return days, month, years
                break

        x[['Day', 'Month', 'Year']] = x.apply(
            month, axis=1, result_type="expand")

        # day dataframe
        day = []

        for i in range(1, 32):
            day.append(i)
        day = pd.DataFrame(day, columns=['Day'])

        # Monthly average Balance
        # function
        def MAB(month, year):
            month = int(month)
            year = int(year)
            for i in range(len(z)):
                mlist = [0, 'Jan', 'Feb', 'Mar', 'Apr', 'May',
                         'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                temp = x[x['Month'] == month]
                temp = temp[temp['Year'] == year]
                yearlb = list(temp[temp['Month'] == month]['Year'])
                temp = temp[['Day', 'EOD']]
                temp['EOD'] = temp['EOD'].str.replace(',', '')
                y = str(temp['EOD'].str.replace('.', ''))
                if y.isdigit():
                    pass
                else:
                    temp['EOD'] = temp['EOD'].str[:-3]
                temp['EOD'] = temp['EOD'].astype(float)
                temp.columns.values[1] = mlist[month]+'-'+str(yearlb[0])
                temp = temp.set_index(['Day'])
            return temp

        # merge all months
        # merge all months
        mon = x['Month'].tolist()
        yr = x['Year'].tolist()
        monyr = []
        for i in range(len(mon)):
            monyr.append([mon[i], yr[i]])
        temp1 = monyr[0]
        unqmy = [monyr[0]]
        for i in range(len(mon)):
            if temp1 == monyr[i]:
                pass
            else:
                unqmy.append(monyr[i])
                temp1 = monyr[i]

        if [0, 0] in unqmy:
            unqmy.remove([0, 0])
        first = unqmy[0]
        mab = pd.merge(day, MAB(first[0], first[1]), how="left", on=["Day"])
        unqmy.pop(0)
        for i in unqmy:
            s = MAB(i[0], i[1])
            mab = pd.merge(mab, s, how="left", on=["Day"])

        mab = mab.replace(np.nan, "null", regex=True)

        # Total
        col = mab.columns.tolist()
        col.pop(0)
        open_bal = self.df_total.iloc[1][self.bal_index]
        case = str(self.df_total.iloc[1][self.bal_index])
        case = case.replace('.', '')
        case = case.replace(',', '')
        if case.isdigit():
            pass
        else:
            open_bal = open_bal[:-3]

        open_bal = float(open_bal.replace(',', ''))

        ######
        for i in col:
            mon = i[0:3]
            if mon == 'Jan' or mon == 'Mar' or mon == 'May' or mon == 'Jul' or mon == 'Aug' or mon == 'Oct' or mon == 'Dec':
                for j in range(31):
                    cell = mab.iloc[j, mab.columns.get_loc(i)]
                    if cell == 'null':
                        mab.iloc[j, mab.columns.get_loc(i)] = open_bal
                    else:
                        open_bal = cell

            if mon == 'Apr' or mon == 'Jun' or mon == 'Sep' or mon == 'Nov':
                for j in range(30):
                    cell = mab.iloc[j, mab.columns.get_loc(i)]
                    if cell == 'null':
                        mab.iloc[j, mab.columns.get_loc(i)] = open_bal
                    else:
                        open_bal = cell

            if mon == 'Feb':
                year = int(i[4:8])
                leap_year = calendar.isleap(year)
                if leap_year:
                    for j in range(29):
                        cell = mab.iloc[j, mab.columns.get_loc(i)]
                        if cell == 'null':
                            mab.iloc[j, mab.columns.get_loc(i)] = open_bal
                        else:
                            open_bal = cell
                else:
                    for j in range(28):
                        cell = mab.iloc[j, mab.columns.get_loc(i)]
                        if cell == 'null':
                            mab.iloc[j, mab.columns.get_loc(i)] = open_bal
                        else:
                            open_bal = cell

        monthlist = [0, 'Jan', 'Feb', 'Mar', 'Apr', 'May',
                     'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        startdate = self.startdate
        enddate = self.enddate
        for i in range(0, 31):
            if i < int(startdate[:2])-1:
                mab.iloc[i, 1] = 'null'

            if i >= int(enddate[:2]):
                mab.iloc[i, -1] = 'null'

        mab = mab.replace('null', np.nan, regex=True)
        mab.loc['Total'] = mab.sum()
        mab['Day'].loc['Total'] = 'Total'
        mab.to_excel(self.Excel_File, sheet_name="EOD Balance", index=False)
        # self.Excel_File.save()

        # print('EOD')
        return mab

    def MonthlyAvg(self, eod):
        monthavg = eod.copy()
        monthavg.loc['Average'] = monthavg.iloc[0:31].mean().round(2)
        monthavg['Day'].loc['Average'] = 'Average'
        monthavg.to_excel(
            self.Excel_File, sheet_name="Monthly AVG Balance", index=False)
        # self.Excel_File.save()

        return monthavg

    def QuaterlyAvg(self, mab):
        quatavg = mab.copy()
        colwidth = len(quatavg.columns)
        # quatavg.loc['Average'] = ''
        # quatavg['Day'].loc['Average'] = 'Average'
        if colwidth > 3:
            tot = (colwidth-1)//3
            ind = 1
            for i in range(tot):
                index = 'Total_'+str(i+1)
                tot_index = (i+1)*3+ind
                quatavg.insert(tot_index, index, value='')
                ind += 1
                total_sum = quatavg.iloc[:31, tot_index-1].sum(
                )+quatavg.iloc[:31, tot_index-2].sum()+quatavg.iloc[:31, tot_index-3].sum()
                quatavg[index].iloc[31] = total_sum
                quatavg[index].iloc[32] = quatavg.iloc[:31, tot_index-1].mean(
                )+quatavg.iloc[:31, tot_index-2].mean()+quatavg.iloc[:31, tot_index-3].mean()
                quatavg.to_excel(
                    self.Excel_File, sheet_name="Quaterly AVG Balance", index=False)
                # self.Excel_File.save()

        else:
            pass

    def HalflyAvg(self, mab):
        halfavg = mab.copy()
        colwidth = len(halfavg.columns)
        # halfavg.loc['Average'] = ''
        # halfavg['Day'].loc['Average'] = 'Average'
        if colwidth > 6:
            tot = (colwidth-1)//6
            ind = 1
            for i in range(tot):
                index = 'Total_'+str(i+1)
                tot_index = (i+1)*6+ind
                halfavg.insert(tot_index, index, value='')
                ind += 1
                total_sum = halfavg.iloc[:31, tot_index-1].sum()+halfavg.iloc[:31, tot_index-2].sum()+halfavg.iloc[:31, tot_index-3].sum(
                )+halfavg.iloc[:31, tot_index-4].sum()+halfavg.iloc[:31, tot_index-5].sum()+halfavg.iloc[:31, tot_index-6].sum()
                halfavg[index].iloc[31] = total_sum
                halfavg[index].iloc[32] = halfavg.iloc[:31, tot_index-1].mean()+halfavg.iloc[:31, tot_index-2].mean()+halfavg.iloc[:31, tot_index-3].mean(
                )+halfavg.iloc[:31, tot_index-4].mean()+halfavg.iloc[:31, tot_index-5].mean()+halfavg.iloc[:31, tot_index-6].mean()
                halfavg.to_excel(
                    self.Excel_File, sheet_name="Half-Yearly AVG Balance", index=False)
                # self.Excel_File.save()

        else:
            pass

    def YearlyAvg(self, mab):
        yearavg = mab.copy()
        colwidth = len(yearavg.columns)
        # yearavg.loc['Average'] = ''
        # yearavg['Day'].loc['Average'] = 'Average'
        if colwidth > 12:
            tot = colwidth//12
            ind = 1
            for i in range(tot):
                index = 'Total_'+str(i+1)
                tot_index = (i+1)*12+ind
                yearavg.insert(tot_index, index, value='')
                ind += 1
                total_sum = yearavg.iloc[:31, tot_index-1].sum()+yearavg.iloc[:31, tot_index-2].sum()+yearavg.iloc[:31, tot_index-3].sum()+yearavg.iloc[:31, tot_index-4].sum()+yearavg.iloc[:31, tot_index-5].sum()+yearavg.iloc[:31, tot_index-6].sum(
                )+yearavg.iloc[:31, tot_index-7].sum()+yearavg.iloc[:31, tot_index-8].sum()+yearavg.iloc[:31, tot_index-9].sum()+yearavg.iloc[:31, tot_index-10].sum()+yearavg.iloc[:31, tot_index-11].sum()+yearavg.iloc[:31, tot_index-12].sum()
                yearavg[index].iloc[31] = total_sum
                yearavg[index].iloc[32] = yearavg.iloc[:31, tot_index-1].mean()+yearavg.iloc[:31, tot_index-2].mean()+yearavg.iloc[:31, tot_index-3].mean()+yearavg.iloc[:31, tot_index-4].mean()+yearavg.iloc[:31, tot_index-5].mean()+yearavg.iloc[:31, tot_index-6].mean(
                )+yearavg.iloc[:31, tot_index-7].mean()+yearavg.iloc[:31, tot_index-8].mean()+yearavg.iloc[:31, tot_index-9].mean()+yearavg.iloc[:31, tot_index-10].mean()+yearavg.iloc[:31, tot_index-11].mean()+yearavg.iloc[:31, tot_index-12].mean()

                yearavg.to_excel(
                    self.Excel_File, sheet_name="Yearly Average Balance", index=False)
                # self.Excel_File.save()

        else:
            pass

    def Index(self):
        columnlist = self.df_total.iloc[0].tolist()
        desc = ['Description', 'Particular', 'Details', 'Narration',
                'Particulars', 'Transaction Remarks', 'NARRATION', 'Remarks']
        debit = ['Debit', 'Withdrawals', 'Withdrawal (Dr)', 'Withdrawal(Dr)', 'Withdrawal Amount (INR )',
                 'Withdrawal Amt.', 'WITHDRAWAL (DR)', 'WITHDRAWAL(DR)', 'WITHDRAWS']
        credit = ['Credit', 'Deposits', 'Deposit(Cr)', 'Deposit (Cr)', 'Deposit Amount (INR )',
                  'Deposit Amt.', 'DEPOSIT (CR)', 'DEPOSIT(CR)', 'DEPOSIT']
        date = ['Date', 'Tran Date', 'Transaction Date',
                'Transaction Date & Time', 'DATE', 'TRANS DATE', 'Txn Date']
        chq = ['Chq./Ref.No.', 'Ref No./Cheque No', 'Cheque Number', 'Chq/Ref No',
               'Cheque No', 'REF/CHQ.NO', 'CHQ.NO.', 'Chq. no', 'Chq.no', 'Ref No./Cheque No.']
        bal = ['Balance', 'Balance (INR )', 'Closing Balance',
               'BALANCE', 'Balance (Rs.)', 'Running Balance']

        for i in range(len(columnlist)):
            if columnlist[i] in desc:
                self.desc_index = i
            if columnlist[i] in debit:
                self.debit_index = i
            if columnlist[i] in credit:
                self.credit_index = i
            if columnlist[i] in date:
                self.date_index = i
            if columnlist[i] in chq:
                self.chq_index = i
            if columnlist[i] in bal:
                self.bal_index = i

    def CASH_DEPOSITS(self):
        df_temp = self.df_total.copy()

        # keywords
        match = ['Cash & Deposit Machine',
                 'CASH DEPOSIT', 'CASH DEP', 'CDM', 'CDS']

        # to find keywords in dataframe
        templ = [0]
        for i in range(2, len(df_temp)):
            for x in match:
                if re.search(x, df_temp[self.desc_index].iloc[i], re.IGNORECASE):
                    templ.append(i)
                    break
                else:
                    pass

        df_cd = df_temp.iloc[templ]

        cd_head = df_cd.iloc[0]
        df_cd = df_cd[1:]
        df_cd.columns = cd_head

        df_cd.to_excel(self.Excel_File, sheet_name="CD", index=False)
        # self.Excel_File.save()

    def EMI(self):
        df_temp2 = self.df_total.copy()
        match2 = ['Equated Monthly Instalments', 'Automated clearing house',
                  'National Automated Clearing House', 'EMI', 'ACHDr', 'NACH']
        templ2 = [0]
        for i in range(2, len(df_temp2)):
            for x in match2:
                if re.search(x, df_temp2[self.desc_index].iloc[i], re.IGNORECASE):
                    templ2.append(i)
                    break
                else:
                    pass

        df_emi = df_temp2.iloc[templ2]
        emi_head = df_emi.iloc[0]
        df_emi = df_emi[1:]
        df_emi.columns = emi_head

        df_emi.to_excel(self.Excel_File, sheet_name="EMI", index=False)
        # self.Excel_File.save()

    def POS(self):
        df_temp3 = self.df_total.copy()
        match3 = ['POS ']
        templ3 = [0]
        for i in range(2, len(df_temp3)):
            for x in match3:
                if re.search(x, df_temp3[self.desc_index].iloc[i], re.IGNORECASE):
                    templ3.append(i)
                    break
                else:
                    pass

        df_pos = df_temp3.iloc[templ3]

        pos_head = df_pos.iloc[0]
        df_pos = df_pos[1:]
        df_pos.columns = pos_head

        df_pos.to_excel(self.Excel_File, sheet_name="POS", index=False)
        # self.Excel_File.save()

    def WITHDRAWL(self):
        df_temp3 = self.df_total.copy()
        df_ft = pd.DataFrame()
        match3 = ['withdraw', 'ATM', 'wdl']
        templ3 = [0]
        for i in range(2, len(df_temp3)):
            for x in match3:
                if re.search(x, df_temp3[2].iloc[i], re.IGNORECASE):
                    templ3.append(i)
                    break
                else:
                    pass

        if len(templ3) == 1:
            pass
        else:
            df_ft = df_temp3.iloc[templ3]
            ft_head = df_ft.iloc[0]
            df_ft = df_ft[1:]
            df_ft.columns = ft_head

            df_ft.to_excel(self.Excel_File,
                           sheet_name="Withdrawal", index=False)

    def FUND_TRANSFER(self):
        df_temp3 = self.df_total.copy()
        df_ft = pd.DataFrame()
        match3 = ['TFR', 'TRF', 'Transfer']
        templ3 = [0]
        for i in range(2, len(df_temp3)):
            for x in match3:
                if re.search(x, df_temp3[2].iloc[i], re.IGNORECASE):
                    templ3.append(i)
                    break
                else:
                    pass

        if len(templ3) == 1:
            pass
        else:
            df_ft = df_temp3.iloc[templ3]
            ft_head = df_ft.iloc[0]
            df_ft = df_ft[1:]
            df_ft.columns = ft_head

            df_ft.to_excel(self.Excel_File,
                           sheet_name="FundTransfer", index=False)

    def BOUNCE(self):
        df_temp4 = self.df_total.copy()
        match4 = ['return', 'ret ', 'bounce']
        templ4 = [0]
        for i in range(2, len(df_temp4)):
            for x in match4:
                if re.search(x, df_temp4[self.desc_index].iloc[i], re.IGNORECASE):
                    templ4.append(i)
                    break
                else:
                    pass

        df_bounce = df_temp4.iloc[templ4]

        bounce_head = df_bounce.iloc[0]
        df_bounce = df_bounce[1:]
        df_bounce.columns = bounce_head

        df_bounce.to_excel(self.Excel_File, sheet_name="Bounce", index=False)
        # self.Excel_File.save()

    def show(self):
        self.validation()
        if self.valid:
            try:
                self.extract()
                print('s')
                eod = self.EOD()
                print('e')
                mavg = self.MonthlyAvg(eod)
                self.QuaterlyAvg(mavg)
                self.HalflyAvg(mavg)
                self.YearlyAvg(mavg)
                # self.Index()
                # self.AverageBalancesT()
                self.CASH_DEPOSITS()
                self.WITHDRAWL()
                self.EMI()
                self.POS()
                self.BOUNCE()
                self.FUND_TRANSFER()
                self.Excel_File.close()
                print('Alldone')
            except Exception as e:
                print(e)
        else:
            print('Incorrect Password')


# passwd = ''
# startdate = '01/09/2020'
# enddate = '31/02/2021'
# AXIS('dec 2020 to july 2021.pdf', passwd, startdate, enddate)
'''
POOJAN
'''
