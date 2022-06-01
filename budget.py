import datetime
import os
import sys
import time

import matplotlib.pyplot as plt
import numpy
import numpy as np
import openpyxl
from matplotlib.ticker import (MultipleLocator)
from snakemd import Document

import categories

os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

# Check if help is requested
if sys.argv[1:7].__contains__('--help') or sys.argv[1:7].__contains__('-h'):
    print("HELP:\n"
          "To run:\n\tbudget.py <file>.xlsx -args\n"
          "Display the report after running:\n\t--display\n\t-d\n"
          "Add a credit score:\n\t--credit\n\t-cr\n"
          "Include your name in the report:\n\t--official\n\t-of\n"
          "Add your net worth (incl. debts and assets:\n\t--networth\n\t-nw\n"
          "Generate a full report and display it:\n\t--full\n\t-fl\n")
    exit()

# Spreadsheet start vvvvv
wb = None
sheet = None
try:
    if sys.argv[1].__contains__(".xlsx"):
        wb = openpyxl.open(sys.argv[1])
        sheet = wb["Data"]
    else:
        print("Invalid file. Please pass in an Excel file:  budget.py <file>.xlsx -args")
except:
    pass  # error printed above, silently catch error

if wb is None:
    exit()

start_time = time.perf_counter()
driver_start_time = time.perf_counter()


def driver():
    answer = input("Would you like to add an entry? y/n\n")
    run = False

    if str(answer).__eq__('y'):
        run = True
    elif str(answer).__eq__('n'):
        print(f'Time spent entering data: {str(datetime.timedelta(seconds=time.perf_counter() - driver_start_time))}')
        run = False
    else:
        driver()

    if run:
        category_selected = str(input("Entry category:\n"
                                      "\t(r) rent\n\t(i) internet\n\t(e) electricity\n\t(g) groceries\n\t"
                                      "(eo) eating out\n\t(ga) gas\n\t(v) vehicle\n\t(d) dog\n\t"
                                      "(cn) consumer - need\n\t(cw) consumer - want\n\t(in) income\n"))

        amount = float(input("Entry amount: $"))

        update_category(category_selected, amount)

        if category_selected != 'in':
            amount = amount * -1

        write_entry(int(input("Year: ")), int(input("Month: ")), int(input("Day: ")),
                    str(input("Description: ") + f' ... category = {category_selected}'),
                    amount)

        driver()


def cell_empty(i=2):
    while sheet[f'E{i}'].value is not None:
        i += 1

    return i


def write_entry(year, month, day, desc, amount):
    cell = cell_empty()
    sheet[f'E{cell}'].value = datetime.datetime(year, month, day)
    sheet[f'F{cell}'].value = desc

    if amount > 0:
        sheet[f'G{cell}'].value = amount
        sheet[f'I{cell}'].value = float(sheet[f'I{cell - 1}'].value) + amount
    if amount < 0:
        sheet[f'H{cell}'].value = amount * -1
        sheet[f'I{cell}'].value = float(sheet[f'I{cell - 1}'].value) + amount


def update_category(category_selected, amount):
    if category_selected == 'r':
        sheet[categories.RENT].value = sheet[categories.RENT].value + amount
    elif category_selected == 'i':
        sheet[categories.INTERNET].value = sheet[categories.INTERNET].value + amount
    elif category_selected == 'e':
        sheet[categories.ELECTRICITY].value = sheet[categories.ELECTRICITY].value + amount
    elif category_selected == 'g':
        sheet[categories.GROCERIES].value = sheet[categories.GROCERIES].value + amount
    elif category_selected == 'eo':
        sheet[categories.EATING_OUT].value = sheet[categories.EATING_OUT].value + amount
    elif category_selected == 'ga':
        sheet[categories.GAS].value = sheet[categories.GAS].value + amount
    elif category_selected == 'v':
        sheet[categories.VEHICLE].value = sheet[categories.VEHICLE].value + amount
    elif category_selected == 'd':
        sheet[categories.DOG].value = sheet[categories.DOG].value + amount
    elif category_selected == 'cn':
        sheet[categories.CONSUMER_NEED].value = sheet[categories.CONSUMER_NEED].value + amount
    elif category_selected == 'cw':
        sheet[categories.CONSUMER_WANT].value = sheet[categories.CONSUMER_WANT].value + amount
    elif category_selected == 'in':
        sheet[categories.INCOME].value = sheet[categories.INCOME].value + amount
    else:
        print("Not a valid category.")


driver()

wb.save(sys.argv[1])

# Spreadsheet end ^^^^^


# REPORT
data_entry_start_time = time.perf_counter()

DAYS_PER_MONTH = 30.4375

categorical_amounts = []
for i in range(2, 12):
    categorical_amounts.append(sheet[f'B{i}'].value)

dates = []
amounts = []
i = 2
while sheet[f'E{i}'].value is not None:
    dates.append(sheet[f'E{i}'].value)
    amounts.append(sheet[f'I{i}'].value)
    i += 1

spending_sum = np.sum(categorical_amounts)
days_passed = (datetime.datetime.now() - dates[0]).days
savings = sheet[categories.INCOME].value - spending_sum
saved_per_day = savings / days_passed
original_amount = sheet['I2'].value
current_amount = amounts[-1]
remaining = float(sheet['B17'].value) - spending_sum

# MatPlotLib start vvvvv
plot_start_time = time.perf_counter()

# Fig 1
data = np.array(
    [float(sheet[categories.RENT].value), float(sheet[categories.INTERNET].value),
     float(sheet[categories.ELECTRICITY].value),
     float(sheet[categories.GROCERIES].value), float(sheet[categories.EATING_OUT].value),
     float(sheet[categories.GAS].value),
     float(sheet[categories.VEHICLE].value), float(sheet[categories.DOG].value),
     float(sheet[categories.CONSUMER_NEED].value),
     float(sheet[categories.CONSUMER_WANT].value)])
labels = ["Rent", "Internet", "Electricity", "Groceries", "Eating Out", "Gas", "Vehicle", "Dog", "Consumer - Need",
          "Consumer - Want"]

fig1, ax1 = plt.subplots(figsize=(16, 16))
ax1.pie(data, startangle=90)
ax1.axis('equal')
ax1.set_title('Spending by Category', size="20")

plt.legend(labels)
plt.savefig("images/spending_breakdown.png", dpi=200, bbox_inches='tight')
plt.clf()

# Fig 2
fig, ax = plt.subplots(figsize=(8, 6))
ax.plot(dates, amounts)
fig.autofmt_xdate()
ax.set_ylim(ymin=numpy.min(amounts) * .75, ymax=numpy.max(amounts) * 1.25)
plt.grid(axis='y', alpha=0.3)
plt.minorticks_on()
ax.minorticks_on()
ax.yaxis.set_major_locator(MultipleLocator(2000))
ax.yaxis.set_minor_locator(MultipleLocator(500))
plt.ylabel("Amount in Bank ($)")
plt.xlabel("Date")
plt.title("Money Over Time", size="20")
plt.annotate('$%0.2f' % amounts[-1], xy=(1, amounts[-1]), xytext=(8, 0),
             xycoords=('axes fraction', 'data'), textcoords='offset points')

fig.savefig("images/money_over_time.png", dpi=200, bbox_inches='tight')

plt.clf()

# Fig 3
x = np.linspace(0, 24, 13)
y = saved_per_day * x * DAYS_PER_MONTH + current_amount
plt.plot(x, y, label='y=2x+1')
plt.title('Savings Rate')
plt.xlabel('Months')
plt.ylabel('Projected Amount ($)')
plt.xticks(x)
plt.grid()
plt.savefig("images/savings_rate.png", dpi=200, bbox_inches='tight')

print(f'Time spent generating plots: {str(datetime.timedelta(seconds=time.perf_counter() - plot_start_time))}')
# MatPlotLib end ^^^^^

# Document start vvvvv
doc = Document("Financial Report")
doc.add_header("Financial Report", 1)
doc.add_header(f'Generated {datetime.datetime.now().strftime("%x %X")}', 6)
doc.add_horizontal_rule()

# Sec 1
doc.add_header("Spending Breakdown by Category", 2)
doc.add_paragraph("![images/spending_breakdown.png](images/spending_breakdown.png)")
doc.add_table(["Category", "Amount Spent", "Percent of Spending"], [
    ["Rent", f'${categorical_amounts[0]:,.2f}', "{:.2%}".format(categorical_amounts[0] / float(spending_sum))],
    ["Internet", f'${categorical_amounts[1]:,.2f}', "{:.2%}".format(categorical_amounts[1] / float(spending_sum))],
    ["Electricity", f'${categorical_amounts[2]:,.2f}', "{:.2%}".format(categorical_amounts[2] / float(spending_sum))],
    ["Groceries", f'${categorical_amounts[3]:,.2f}', "{:.2%}".format(categorical_amounts[3] / float(spending_sum))],
    ["Eating Out", f'${categorical_amounts[4]:,.2f}', "{:.2%}".format(categorical_amounts[4] / float(spending_sum))],
    ["Gas", f'${categorical_amounts[5]:,.2f}', "{:.2%}".format(categorical_amounts[5] / float(spending_sum))],
    ["Vehicle", f'${categorical_amounts[6]:,.2f}', "{:.2%}".format(categorical_amounts[6] / float(spending_sum))],
    ["Dog", f'${categorical_amounts[7]:,.2f}', "{:.2%}".format(categorical_amounts[7] / float(spending_sum))],
    ["Consumer - Need", f'${categorical_amounts[8]:,.2f}',
     "{:.2%}".format(categorical_amounts[8] / float(spending_sum))],
    ["Consumer - Want", f'${categorical_amounts[9]:,.2f}',
     "{:.2%}".format(categorical_amounts[9] / float(spending_sum))]])

doc.add_table(["Category", "Amount Spent", "Percent of Spending"], [
    ["Transportation", f'${np.sum(categorical_amounts[5:7]):,.2f}',
     "{:.2%}".format(np.sum(categorical_amounts[5:7]) / float(spending_sum))],
    ["Cost of Living", f'${spending_sum - np.sum(categorical_amounts[5:7]):,.2f}',
     "{:.2%}".format((spending_sum - np.sum(categorical_amounts[5:7])) / spending_sum)],
    ["**Total**", f'**${spending_sum:,.2f}**',
     f'**{"{:.2%}".format(spending_sum / float(np.sum(categorical_amounts[0:11])))}**']
])

# Sec 2
doc.add_header("Money Over Time", 2)
doc.add_paragraph("![images/money_over_time.png](images/money_over_time.png)")
doc.add_paragraph(
    f'Amount of change since {sheet["E2"].value.strftime("%m/%d/%Y")} ({days_passed} '
    f'days):<br/>**• ${current_amount - original_amount:+,.2f}'
    f'<br/>• {100 * ((current_amount / original_amount) - 1):+,.2f}%**')

# Sec 3
doc.add_header("Income", 2)
doc.add_table(["Category", "Amount"], [
    ["Total Income", "$" + "{:,.2f}".format(sheet['B17'].value)],
    ["Remaining After Spending", "$" + "{:,.2f}".format(remaining)],
    ["Saving", "{:,.2%}".format(remaining / float(sheet['B17'].value))]
])

# Sec 4
doc.add_header("Savings", 2)
doc.add_paragraph(f'Thus far, you have saved: **${"{:,.2f}".format(savings)}**')
doc.add_paragraph(f'This is savings of **${"{:,.2f}".format(saved_per_day)}** per day.\n'
                  f'This graph shows how your savings are trending:\n'
                  f'![images/savings_rate.png](images/savings_rate.png)')
doc.add_paragraph(f'**Notable projections:**')
doc.add_table(["Months", "Projected Amount"],
              [["3", "${:,.2f}".format(saved_per_day * 3 * DAYS_PER_MONTH + current_amount)],
               ["6", "${:,.2f}".format(saved_per_day * 6 * DAYS_PER_MONTH + current_amount)],
               ["12", "${:,.2f}".format(saved_per_day * 12 * DAYS_PER_MONTH + current_amount)],
               ["24", "${:,.2f}".format(saved_per_day * 24 * DAYS_PER_MONTH + current_amount)]])


# Sec 5
def add_debts(file):
    keep_asking = True
    debts = []
    total_debt = 0
    while keep_asking:
        ans = input("Do you have debts to add? y/n\n")
        if ans.__eq__('y'):
            desc = input("Description: ")
            amount = float(input("Amount: $"))
            total_debt += amount
            debts.append([desc, "${:,.2f}".format(amount)])
        if ans.__eq__('n'):
            keep_asking = False

    debts.append(["**Total**", f'**{"${:,.2f}".format(total_debt)}**'])
    file.add_header("Debts", 2)
    file.add_table(["Description", "Amount"], debts)

    return total_debt


# Sec 6
def add_assets(file):
    keep_asking = True
    assets = []
    total_assets = current_amount
    while keep_asking:
        ans = input("Do you have assets to add? y/n\n")
        if ans.__eq__('y'):
            desc = input("Description: ")
            amount = float(input("Amount: $"))
            total_assets += amount
            assets.append([desc, "${:,.2f}".format(amount)])
        if ans.__eq__('n'):
            keep_asking = False

    assets.append(["Cash", "${:,.2f}".format(current_amount)])
    assets.append(["**Total**", f'**{"${:,.2f}".format(total_assets)}**'])
    file.add_header("Assets", 2)
    file.add_table(["Description", "Amount"], assets)

    return total_assets


# Sec 7
def add_net_worth(file):
    debt = add_debts(doc)
    assets = add_assets(doc)

    file.add_header("Net Worth", 2)
    file.add_table(["Category", "Amount"], [
        ["Debt", "${:,.2f}".format(debt)],
        ["Assets", "${:,.2f}".format(assets)],
        ["**Total**", f'**{"${:+,.2f}".format(assets - debt)}**']
    ])


# Sec 8
def add_credit_score(file, score, source):
    file.add_header("Credit Score", 2)
    file.add_paragraph(f'Credit score as of {datetime.datetime.now().date()}: **{score}**')
    file.add_paragraph(f'*Source: {source}*')


# Sec 9
def add_official(file, name):
    file.add_paragraph("<br/><br/>")
    file.add_quote(f'This report has been generated for {name} on {datetime.datetime.now().date()}.')


# Document end ^^^^^

try:
    if sys.argv[2:7].__contains__('--full') or sys.argv[2:7].__contains__('-fl'):
        add_net_worth(doc)
        add_credit_score(doc, input("What is your credit score? "), input("What is your source? "))
        add_official(doc, input("What name would you like to appear on the report? "))
        time.sleep(1.0)
        os.system("open report.md -a QLMarkdown")
    if sys.argv[2:7].__contains__('--networth') or sys.argv[2:7].__contains__('-nw'):
        add_net_worth(doc)
    if sys.argv[2:7].__contains__('--credit') or sys.argv[2:7].__contains__('-cr'):
        add_credit_score(doc, input("What is your credit score? "), input("What is your source? "))
    if sys.argv[2:7].__contains__('--official') or sys.argv[2:7].__contains__('-of'):
        add_official(doc, input("What name would you like to appear on the report? "))
    if sys.argv[2:7].__contains__('--display') or sys.argv[2:7].__contains__('-d'):
        os.system("open report.md -a QLMarkdown")
        # os.system("/usr/local/bin/qlmarkdown_cli -o report.html report.md")
except IndexError:
    print("Report generated but not displayed. To display the report, pass in\n\t--display\n\t-d")

print(
    f'Time spent entering additional data: {str(datetime.timedelta(seconds=time.perf_counter() - data_entry_start_time))}')

report_start_time = time.perf_counter()
f = open("report.md", "w")
f.write(str(doc))
f.close()
print(f'Time spent generating report: {str(datetime.timedelta(seconds=time.perf_counter() - report_start_time))}')
print(f'Total time spent: {str(datetime.timedelta(seconds=time.perf_counter() - start_time))}')
