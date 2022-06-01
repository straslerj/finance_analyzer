# Finance Analyzer
Budget tracking and visualizer, along with the ability to generate a report of general financial health.

## Getting Started

*Assuming all libraries are installed, which may require installation through `pip`, to start, do the following:*

1. Clone the repository
2. Open the example budget
   1. You may adjust categories on the left, but note that if you get rid of/add  categories, the code will need to be updated to reflect these changes.
3. Add the starting amount, likely either $0 or your bank balance, to the first row of the register, starting at `E2` on the Excel sheet. A valid row may look like this:
      
| Date   | Description      | Debit (+) | Credit (-) | Balance       |
| ------ | ---------------- | --------- | ---------- | ------------- |
| 6/1/22 | Starting balance |           |            | $    1,000.00 |

4. Run the program! To run the program, in your terminal, run `python3 budget.py <spreadsheet>.xlsx -args`, where `-args` is any (or none) of the following:
   
   `--display, -d`

   `--credit, -cr`

   `--official, -of `

   `--networth, -nw`

   `--full, -fl`

## Overview of Functionality

### Basics

The program will prompt user for expenses/incomes to add to the register, and add the data respectivly to the spreadsheet. The spreadsheet serves this system primarily as a database. A report, including plots, is generated at the end of running and can be found in the directory from which the program was run. 

**Note: the report is written over each time the program is run. To save specific reports, you must do so manually.**

### In addition to the basics,

### `--display`

This argument opens the markdown file that is generated at the end of running. Note that this is by default done through QLMarkdown and **the codebase should be updated to your favorite application to view Markdown**.

### `--credit`

A simple prompt that requires you to put in your credit score and the source from which you got it. Note that this is self-reporting - the program does not integrate with any credit services.

### `--official`

Adds a line indicating whom this report was run for, which the user is prompted to input, to add a layer of officialness to the document in case it is being presented to to, for example, a bank.

### `--networth`

Prompts user similarly to the core functionality to get all debts and assets, lists debts and assets in the report, and also calculates net worth, taking your current bank balance into consideration.

### `--full`

All of the above functionality is executed.

## External Libraries Used

 - Matplotlib
 - NumPy
 - openpyxl
 - SnakeMD
