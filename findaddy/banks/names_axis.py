

import pandas as pd
import openpyxl
import re
import PyPDF4


FILE_PATH = '/content/axisbank.pdf'

with open(FILE_PATH, mode='rb') as f:
    reader = PyPDF4.PdfFileReader(f)
    page = reader.getPage(0)
    txt = page.extractText()

acc_no = re.findall("Account No :[0-9]*", txt)
account_no = acc_no[0]  # get the first (and only) string in the list
last_15_digitsac = account_no[-15:]
df_acc_no = pd.DataFrame([[last_15_digitsac]])
co_no = re.findall("Customer No :[0-9]*", txt)
Customer_no = co_no[0]  # get the first (and only) string in the list
last_15_digitscc = Customer_no[-9:]
df_co_no = pd.DataFrame([[last_15_digitscc]])

res = re.split('\n', txt)

name = res[1]
list01 = [name]
df_name = pd.DataFrame(list01)

joint_holder = res[2]
list0 = [joint_holder]
df_joint_holder = pd.DataFrame(list0)

add1 = (res[3])
add2 = (res[4])
add3 = (res[5])
add4 = (res[6])
add5 = (res[8])
address = add1 + " "+add2 + " "+add3+" " + add4+" " + add5
list1 = [address]
df_address = pd.DataFrame(list1)

type1 = res[9]
list2 = [type1]
df_type1 = pd.DataFrame(list2)

result_name = pd.concat([df_name, df_acc_no, df_co_no,
                        df_joint_holder, df_address, df_type1], axis=0)

name = ['Name']
name1 = pd.DataFrame(name)
Acc = ["Account Number"]
Acc1 = pd.DataFrame(Acc)
Cust = ['Customer Number']
Cust1 = pd.DataFrame(Cust)
joint = ['Joint Holder']
joint1 = pd.DataFrame(joint)
Add = ['Address']
Add1 = pd.DataFrame(Add)
AT = ["Account Type"]
AT1 = pd.DataFrame(AT)
Names_list = pd.concat([name1, Acc1, Cust1, joint1, Add1, AT1], axis=0)

final_name = pd.concat([Names_list, result_name], axis=1)

with pd.ExcelWriter('BankStatement.xlsx', mode='a') as writer:
    final_name.to_excel(writer, sheet_name='Names', index=False)

workbook = openpyxl.load_workbook('BankStatement.xlsx')
names_sheet = workbook['Names']
summary_sheet = workbook['summary']


summary_sheet['C2'].value = names_sheet['B2'].value
summary_sheet['C3'].value = names_sheet['B6'].value
summary_sheet['C4'].value = "Axis Bank"
summary_sheet['C5'].value = names_sheet['B3'].value
summary_sheet['C6'].value = names_sheet['B7'].value
summary_sheet['C8'].value = names_sheet['B4'].value
summary_sheet['C7'].value = names_sheet['B5'].value

workbook.save('BankStatement.xlsx')
