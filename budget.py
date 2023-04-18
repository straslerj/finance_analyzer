import datetime
import os
import time
import argparse

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mysql as mysql
import numpy as np

from matplotlib.ticker import MultipleLocator
from mysql import connector
from snakemd import Document


parser = argparse.ArgumentParser()
parser.add_argument(
    "-fl", "--full", help="generates a full report", action="store_true"
)
parser.add_argument(
    "-nr",
    "--no-reg",
    help="leaves register off full report",
    action="store_true",
)
parser.add_argument(
    "-nw",
    "--networth",
    help="includes networth in report",
    action="store_true",
)
parser.add_argument(
    "-cr",
    "--credit",
    help="includes credit score in report",
    action="store_true",
)
parser.add_argument(
    "-of",
    "--official",
    help="makes the report have all the parts of an official report",
    action="store_true",
)
parser.add_argument(
    "-d",
    "--display",
    help="displays the report after it's generated",
    action="store_true",
)
parser.add_argument(
    "-rg", "--register", help="adds register to report", action="store_true"
)
args = parser.parse_args()

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

DB_HOST = os.getenv("BUDGET_DB_HOST")
DB_USER = os.getenv("BUDGET_DB_USER")
DB_PASSWORD = os.getenv("BUDGET_DB_PASSWORD")
DB_DATABASE = os.getenv("BUDGET_DB_DATABASE")
DB_TABLE = os.getenv("BUDGET_DB_TABLE")


# MySQL start vvvvv
mydb = connector.connect(
    host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_DATABASE
)

mycursor = mydb.cursor(buffered=True)

SQL_TRANS_DATE = 0
SQL_AMOUNT = 1
SQL_CURRENT_TOTAL = 2
SQL_DESCRIPTION = 3
SQL_ID = 4
SQL_CATEGORY = 5
# MySQL end ^^^^^

start_time = time.perf_counter()
driver_start_time = time.perf_counter()


def most_recent_row():
    mycursor.execute(f"select current_total from {DB_TABLE} order by trans_date asc")
    if mycursor.rowcount > 0:
        return mycursor.rowcount - 1
    else:
        return 0


def most_recent_entry():
    mycursor.execute(f"select * from {DB_TABLE} order by trans_date asc")
    records = mycursor.fetchall()
    if most_recent_row() >= 0:
        # f'${register[i][1]:,.2f}'
        most_recent_date = records[most_recent_row()][SQL_TRANS_DATE]
        most_recent_description = records[most_recent_row()][SQL_DESCRIPTION]
        most_recent_amount = f"${records[most_recent_row()][SQL_AMOUNT]:,.2f}"
        most_recent_category = records[most_recent_row()][SQL_CATEGORY]
        print(
            f"Most recent entry:\t{most_recent_date}\t{most_recent_description}\t{most_recent_amount}\t{most_recent_category}"
        )
    else:
        print("There are currently no entries.")


most_recent_entry()


def driver():
    answer = input("Would you like to add an entry? y/n\n")
    run = False

    if str(answer).__eq__("y"):
        run = True
    elif str(answer).__eq__("n"):
        print(
            f"Time spent entering data: {str(datetime.timedelta(seconds=time.perf_counter() - driver_start_time))}"
        )
        run = False
    else:
        driver()

    if run:
        category_selected = str(
            input(
                "Entry category:\n"
                "\t(r) rent\n\t(i) internet\n\t(e) electricity\n\t(g) groceries\n\t"
                "(eo) eating out\n\t(ga) gas\n\t(v) vehicle\n\t(d) dog\n\t"
                "(cn) consumer - need\n\t(cw) consumer - want\n\t(in) income\n"
            )
        )

        amount = float(input("Entry amount: $"))

        try:
            write_entry(
                int(input("Year: ")),
                int(input("Month: ")),
                int(input("Day: ")),
                str(input("Description: ")),
                amount,
                category_selected,
            )

        except ValueError:
            print("Invalid input. Please try again.\n")

        driver()


def write_entry(year, month, day, desc, amount, entry_category):
    mycursor.execute(f"select current_total from {DB_TABLE}")
    records = mycursor.fetchall()
    if most_recent_row() >= 0:
        current_total = float(records[most_recent_row()][0])
    else:
        current_total = 0
    sql = f"INSERT INTO {DB_TABLE} (trans_date, amount, current_total, description, category) VALUES (%s, %s, %s, %s, %s)"
    if entry_category.__eq__("in"):
        val = (
            datetime.datetime(year, month, day).date(),
            amount,
            current_total + amount,
            desc,
            entry_category,
        )
    else:
        val = (
            datetime.datetime(year, month, day).date(),
            amount,
            current_total - amount,
            desc,
            entry_category,
        )
    mycursor.execute(sql, val)

    mydb.commit()


driver()

# REPORT
# Variables
data_entry_start_time = time.perf_counter()

DAYS_PER_MONTH = 30.4375

category_totals = {
    "r": 0.0,
    "i": 0.0,
    "e": 0.0,
    "g": 0.0,
    "eo": 0.0,
    "ga": 0.0,
    "v": 0.0,
    "d": 0.0,
    "cn": 0.0,
    "cw": 0.0,
    "in": 0.0,
}

# Adding values for each category in the category_totals dict
for category in category_totals:
    mycursor.execute(
        f'select amount from {DB_TABLE} where category = "%s" order by trans_date asc;'
        % category
    )
    i = 0
    value = 0.0
    rowcount = mycursor.rowcount

    if rowcount > 0:
        results = mycursor.fetchall()
        results = [i[0] for i in results]
        category_totals[category] = float(sum(results))
        i += 1
    else:
        value = 0
        i += 1

mycursor.execute(
    f"select trans_date, current_total from {DB_TABLE} order by trans_date asc;"
)
results = mycursor.fetchall()
dates = []
amounts = []
for datum in results:
    dates.append(datum[0])
    amounts.append(float(datum[1]))

mycursor.execute(
    f'select amount from {DB_TABLE} where category != "in" and category != "sa" order by trans_date asc;'
)
spending_sum = float(np.sum([i[0] for i in mycursor.fetchall()]))

mycursor.execute(
    f'select amount from {DB_TABLE} where category = "in" order by trans_date asc;'
)
total_income = float(np.sum([i[0] for i in mycursor.fetchall()]))

days_passed = (datetime.datetime.now().date() - dates[0]).days
savings = total_income - spending_sum
saved_per_day = savings / days_passed

mycursor.execute(f"SELECT current_total FROM {DB_TABLE} LIMIT 1;")
original_amount = float(mycursor.fetchone()[0])

current_amount = float(amounts[-1])
percent_change = 100 * ((current_amount / original_amount) - 1)
savings_percentage = savings / total_income

mycursor.execute(
    f"SELECT trans_date, amount, description, category, current_total FROM {DB_TABLE} order by trans_date asc;"
)
register = [i[0:5] for i in mycursor.fetchall()]

# Adding asterisks for Makrdown formatting so the entries that are income are bolded in the register in the report.
i = 0
while i < len(register):
    if register[i][3].__eq__("in"):
        register[i] = [
            "**" + str(register[i][0]) + "**",
            "**" + f"${register[i][1]:,.2f}" + "**",
            "**" + str(register[i][2]) + "**",
            "**" + str(register[i][3]) + "**",
            "**" + f"${register[i][4]:,.2f}" + "**",
        ]
    else:
        register[i] = [
            str(register[i][0]),
            f"${register[i][1]:,.2f}",
            str(register[i][2]),
            str(register[i][3]),
            f"${register[i][4]:,.2f}",
        ]
    i += 1

transportation_keys = ["ga", "v"]
transportation_spending = np.sum(
    [category_totals.get(key) for key in transportation_keys]
)

living_spending = spending_sum - transportation_spending

mycursor.execute(f"select trans_date from {DB_TABLE} LIMIT 1;")
first_date_in_register = mycursor.fetchone()[0]

# MatPlotLib start vvvvv
plot_start_time = time.perf_counter()

# Fig 1
data = np.array(
    [
        category_totals["r"],
        category_totals["i"],
        category_totals["e"],
        category_totals["g"],
        category_totals["eo"],
        category_totals["ga"],
        category_totals["v"],
        category_totals["d"],
        category_totals["cn"],
        category_totals["cw"],
    ]
)
labels = [
    "Rent",
    "Internet",
    "Electricity",
    "Groceries",
    "Eating Out",
    "Gas",
    "Vehicle",
    "Dog",
    "Consumer - Need",
    "Consumer - Want",
]

fig1, ax1 = plt.subplots(figsize=(16, 16))
ax1.pie(data, startangle=90)
ax1.axis("equal")
ax1.set_title("Spending by Category", size="20")

plt.legend(labels)
plt.savefig("images/spending_breakdown.png", dpi=200, bbox_inches="tight")
plt.clf()

# Fig 2
fig, ax = plt.subplots(figsize=(8, 6))

i = 0
while i < len(dates):
    dates[i] = datetime.datetime.combine(dates[i], datetime.datetime.min.time())
    i += 1

ax.plot(dates, amounts)
fig.autofmt_xdate()
ax.set_ylim(ymin=np.min(amounts) * 0.85, ymax=np.max(amounts) * 1.15)
plt.grid(axis="y", alpha=0.3)
plt.minorticks_on()
ax.minorticks_on()
ax.yaxis.set_major_locator(MultipleLocator(2000))
ax.yaxis.set_minor_locator(MultipleLocator(500))
ax.yaxis.set_major_formatter("${x:1,.0f}")
plt.ylabel("Amount in Bank ($)")
plt.xlabel("Date")
plt.title("Money Over Time", size="20")
plt.annotate(
    "${:0,.2f}".format(amounts[-1]),
    xy=(1, amounts[-1]),
    xytext=(8, 0),
    xycoords=("axes fraction", "data"),
    textcoords="offset points",
)

fig.savefig("images/money_over_time.png", dpi=200, bbox_inches="tight")

plt.clf()

# Fig 3
x = np.linspace(0, 24, 13)
y = saved_per_day * x * DAYS_PER_MONTH + current_amount

line_color = "blue"
if saved_per_day > 0:
    line_color = "green"
elif saved_per_day < 0:
    line_color = "red"

plt.plot(x, y, color=line_color)

plt.title("Savings Rate")
plt.xlabel("Months")
plt.ylabel("Projected Amount ($)")
plt.xticks(x)
plt.gca().yaxis.set_major_formatter(ticker.StrMethodFormatter("${x:,.0f}"))
plt.annotate(
    "{:0,.2%}".format(savings_percentage),
    xy=(1, saved_per_day * 24 * DAYS_PER_MONTH + current_amount),
    xytext=(8, 0),
    xycoords=("axes fraction", "data"),
    textcoords="offset points",
)
plt.grid()
plt.savefig("images/savings_rate.png", dpi=200, bbox_inches="tight")

print(
    f"Time spent generating plots: {str(datetime.timedelta(seconds=time.perf_counter() - plot_start_time))}"
)
# MatPlotLib end ^^^^^

# Document start vvvvv
doc = Document("Financial Report")
doc.add_header("Financial Report", 1)
doc.add_header(
    f'Generated {datetime.datetime.now().strftime("%-m/%-d/%Y %-I:%M %p")}', 6
)
doc.add_header(
    f'This document reflects financial activity since {dates[0].strftime("%-m/%-d/%Y")} ({days_passed} days).',
    6,
)
doc.add_horizontal_rule()

# Sec 1
doc.add_header("Spending Breakdown by Category", 2)
doc.add_paragraph("![images/spending_breakdown.png](images/spending_breakdown.png)")
doc.add_table(
    ["Category", "Amount Spent", "Percent of Spending", "Amount per Month"],
    [
        [
            "Rent",
            f'${category_totals["r"]:,.2f}',
            "{:.2%}".format(category_totals["r"] / spending_sum),
            f'${category_totals["r"]  / (days_passed / DAYS_PER_MONTH):,.2f}',
        ],
        [
            "Internet",
            f'${category_totals["i"]:,.2f}',
            "{:.2%}".format(category_totals["i"] / spending_sum),
            f'${category_totals["i"]  / (days_passed / DAYS_PER_MONTH):,.2f}',
        ],
        [
            "Electricity",
            f'${category_totals["e"]:,.2f}',
            "{:.2%}".format(category_totals["e"] / spending_sum),
            f'${category_totals["e"]  / (days_passed / DAYS_PER_MONTH):,.2f}',
        ],
        [
            "Groceries",
            f'${category_totals["g"]:,.2f}',
            "{:.2%}".format(category_totals["g"] / spending_sum),
            f'${category_totals["g"]  / (days_passed / DAYS_PER_MONTH):,.2f}',
        ],
        [
            "Eating Out",
            f'${category_totals["eo"]:,.2f}',
            "{:.2%}".format(category_totals["eo"] / spending_sum),
            f'${category_totals["eo"]  / (days_passed / DAYS_PER_MONTH):,.2f}',
        ],
        [
            "Gas",
            f'${category_totals["ga"]:,.2f}',
            "{:.2%}".format(category_totals["ga"] / spending_sum),
            f'${category_totals["ga"]  / (days_passed / DAYS_PER_MONTH):,.2f}',
        ],
        [
            "Vehicle",
            f'${category_totals["v"]:,.2f}',
            "{:.2%}".format(category_totals["v"] / spending_sum),
            f'${category_totals["v"]  / (days_passed / DAYS_PER_MONTH):,.2f}',
        ],
        [
            "Dog",
            f'${category_totals["d"]:,.2f}',
            "{:.2%}".format(category_totals["d"] / spending_sum),
            f'${category_totals["d"]  / (days_passed / DAYS_PER_MONTH):,.2f}',
        ],
        [
            "Consumer - Need",
            f'${category_totals["cn"]:,.2f}',
            "{:.2%}".format(category_totals["cn"] / spending_sum),
            f'${category_totals["cn"]  / (days_passed / DAYS_PER_MONTH):,.2f}',
        ],
        [
            "Consumer - Want",
            f'${category_totals["cw"]:,.2f}',
            "{:.2%}".format(category_totals["cw"] / spending_sum),
            f'${category_totals["cw"]  / (days_passed / DAYS_PER_MONTH):,.2f}',
        ],
    ],
)

doc.add_table(
    ["Category", "Amount Spent", "Percent of Spending", "Amount per Month"],
    [
        [
            "Transportation",
            f"${transportation_spending:,.2f}",
            "{:.2%}".format(transportation_spending / float(spending_sum)),
            f"${transportation_spending / (days_passed / DAYS_PER_MONTH):,.2f}",
        ],
        [
            "Cost of Living",
            f"${float(spending_sum) - transportation_spending:,.2f}",
            "{:.2%}".format((spending_sum - transportation_spending) / spending_sum),
            f"${(float(spending_sum) - transportation_spending) / (days_passed / DAYS_PER_MONTH):,.2f}",
        ],
        [
            "**Total**",
            f"**${spending_sum:,.2f}**",
            f'**{"{:.2%}".format((transportation_spending + living_spending) / float(spending_sum))}**',
            f"${spending_sum / (days_passed / DAYS_PER_MONTH):,.2f}",
        ],
    ],
)

# Sec 2
doc.add_header("Money Over Time", 2)
doc.add_paragraph("![images/money_over_time.png](images/money_over_time.png)")
doc.add_paragraph(
    f'Amount of change since {first_date_in_register.strftime("%m/%d/%Y")} ({days_passed} '
    f"days):<br/>**• ${current_amount - original_amount:+,.2f}"
    f"<br/>• {percent_change:+,.2f}%**"
)

# Sec 3
doc.add_header("Income", 2)
doc.add_table(
    ["Category", "Amount"],
    [
        ["Total Income", "$" + "{:,.2f}".format(total_income)],
        ["Remaining After Spending", "$" + "{:,.2f}".format(savings)],
        ["Saving", "{:,.2%}".format(savings_percentage)],
    ],
)

# Sec 4
doc.add_header("Savings", 2)
doc.add_paragraph(f'Thus far, you have saved: **${"{:,.2f}".format(savings)}**')
doc.add_paragraph(
    f'This is savings of **${"{:,.2f}".format(saved_per_day)}** per day.\n'
    f"This graph shows how your savings are trending:\n"
    f"![images/savings_rate.png](images/savings_rate.png)"
)
doc.add_paragraph(f"**Notable projections:**")
doc.add_table(
    ["Months", "Projected Amount"],
    [
        ["3", "${:,.2f}".format(saved_per_day * 3 * DAYS_PER_MONTH + current_amount)],
        ["6", "${:,.2f}".format(saved_per_day * 6 * DAYS_PER_MONTH + current_amount)],
        ["12", "${:,.2f}".format(saved_per_day * 12 * DAYS_PER_MONTH + current_amount)],
        ["24", "${:,.2f}".format(saved_per_day * 24 * DAYS_PER_MONTH + current_amount)],
    ],
)


# Sec 5
def add_debts(file):
    keep_asking = True
    debts = []
    total_debt = 0
    while keep_asking:
        ans = input("Do you have debts to add? y/n\n")
        if ans.__eq__("y"):
            desc = input("Description: ")
            amount = float(input("Amount: $"))
            total_debt += amount
            debts.append([desc, "${:,.2f}".format(amount)])
        if ans.__eq__("n"):
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
        if ans.__eq__("y"):
            desc = input("Description: ")
            amount = float(input("Amount: $"))
            total_assets += amount
            assets.append([desc, "${:,.2f}".format(amount)])
        if ans.__eq__("n"):
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
    file.add_table(
        ["Category", "Amount"],
        [
            ["Debt", "${:,.2f}".format(debt)],
            ["Assets", "${:,.2f}".format(assets)],
            ["**Total**", f'**{"${:+,.2f}".format(assets - debt)}**'],
        ],
    )


# Sec 8
def add_credit_score(file, score, source):
    file.add_header("Credit Score", 2)
    file.add_paragraph(
        f'Credit score as of {datetime.datetime.now().date().strftime("%-m/%-d/%Y")}: **{score}**'
    )
    file.add_paragraph(f"*Source: {source}*")


# Sec 9
def add_official(file, name):
    file.add_paragraph("<br/><br/>")
    file.add_quote(
        f'This report has been generated for {name} on {datetime.datetime.now().date().strftime("%-m/%-d/%Y")}.'
    )


# Sec 10
def add_register(file):
    file.add_header("Appendix", 1)

    file.add_header("Register", 2)
    register_count_query = mycursor.execute(f"select count(*) from {DB_TABLE}")
    result = mycursor.fetchone()
    file.add_paragraph(f"Showing {result[0]} entries.")
    file.add_table(["Date", "Amount", "Description", "Category", "Balance"], register)


# Document end ^^^^^

try:
    args = vars(args)

    if args["full"]:
        add_net_worth(doc)
        add_credit_score(
            doc, input("What is your credit score? "), input("What is your source? ")
        )
        add_register(doc)
        add_official(doc, input("What name would you like to appear on the report? "))
        time.sleep(1.0)
        os.system("open report.md -a QLMarkdown")
    if args["no_reg"]:
        add_net_worth(doc)
        add_credit_score(
            doc, input("What is your credit score? "), input("What is your source? ")
        )
        add_official(doc, input("What name would you like to appear on the report? "))
        time.sleep(1.0)
        os.system("open report.md -a QLMarkdown")
    if args["networth"]:
        add_net_worth(doc)
    if args["credit"]:
        add_credit_score(
            doc, input("What is your credit score? "), input("What is your source? ")
        )
    if args["official"]:
        add_official(doc, input("What name would you like to appear on the report? "))
    if args["display"]:
        os.system("open report.md -a QLMarkdown")  # change to your desired viewer
    if args["register"]:
        add_register(doc)
except IndexError:
    print(
        "Report generated but not displayed. To display the report, pass in\n\t--display\n\t-d"
    )

print(
    f"Time spent entering additional data: {str(datetime.timedelta(seconds=time.perf_counter() - data_entry_start_time))}"
)

report_start_time = time.perf_counter()
f = open("report.md", "w")
f.write(str(doc))
f.close()
print(
    f"Time spent generating report: {str(datetime.timedelta(seconds=time.perf_counter() - report_start_time))}"
)
print(
    f"Total time spent: {str(datetime.timedelta(seconds=time.perf_counter() - start_time))}"
)
