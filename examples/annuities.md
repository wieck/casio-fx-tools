# Annuity Calculations

This series of programs is for solving equations for traditional, fixed rate
mortgages, such as home loans and similar recurring payments.

Traditional, fixed interest rate mortgages have an initial loan amount,
called the Present Value (PV), a Future Value (FV) a number of payment
and compounding periods (often 180 or 360 months for 15 and 30 year terms
respectively), an interest rate (i) in percent (for the length of the periods)
and a Payment (PMT) like the monthly combined principal and interest.

The program text for `fx502p_load` is [here](annuities.cas?raw=true).

## Memory assignment

Instead of prompting to input data at the beginning of each run
these programs expect and store inputs and results in specific memory
registers. This makes it easier to change a single paramenter, like the
number of payment periods, and run the calculation for the required
payment amount over and over without reentering the interest rate and
Present Value.

| Register | Name | Description
| -------- | ---- | ------------
| M1       | PV   | Present Value (usually the initial load amount) |
| M2       | FV   | Future Value (usually 0 meaning the loan is fully paid off) |
| M3       | n    | Duration of the loan in compounding periods (usually months) |
| M4       | i    | Interest rate in % per compounding period (divide an annual interest rate by 12 if the compounding/payment periods are monthly) |
| M5       | PMT  | Payment per compounding period |
| M18	   | -    | Temporary value from P8 |
| M19      | -    | Temporary value from P8 |

## P0: Solving for Payment (PMT)

Solving for Payment answers the question "how much will the monthly
payment for specific mortgage be?"

This example is based on a $300,000 mortgage, 30 years fixed at 5.0%
interest rate. 

| Action          | Comment     |
| --------------- | ----------- |
| AC              | Clear State |
| 300000 Min1     | Set PV      |
| 0 Min2          | Set FV (to all paid off) |
| 360 Min3        | Set n (30 years * 12 months) |
| 5 / 12 = Min4   | Set i (5.0% annual / 12 months) |
| P0              | Output: 1610.46487 |

This mortgage will have a monthly payment of $1,610.46
(interest and principal only without any escrow).

We can now simulate how a change in interest rate to 5.5% annual will
affect the monthly payment. Without clearing any registers we
just change the interest rate:

| Action          | Comment     |
| --------------- | ----------- |
| 5.5 / 12 = Min4 | Change interest rate to 5.5% annual |
| P0              | Output: 1703.367004 |

This means that the increase of the interest rate to 5.5%
results in almost $93 higher monthly payments. To offset a higher
interest rate an initial down payment is often used.
Let us simulate a 5% down payment of $15,000. This
changes PV to $285,000:

| Action           | Comment     |
| ---------------- | ----------- |
| MR1 * 5 % - Min1 | Reduce PV by 5% to $285,000 |
| P0               | Output: 1618.198654 |

Adding a 5% down payment to the mortgage brought the monthly payment
back down to $1,618.20.

## P1: Solving for Future Value (FV)

Solving for Future Value answers the question "what will the
remaining balance of the mortgage be after *m* months?"

Keeping with our ongoing example we currently look at a mortgage of
$285,000 with 5.5% fixed interest for 360 months (at least that is
what should be in the memory registers at this point).

If we simply change the number of months to 120 (10 years) we can
use P1 to calculate the remaining balance at that point.

| Action          | Comment     |
| --------------- | ----------- |
| 120 Min3        | Change the number of payments |
| P1              | Output: 235241.8247 |

That is quite disappointing, isn't it? After 10 years we have paid
off only 17.5% of the original 30 year $285,000 loan. 

## P2: Solving for Present Value

Solving for Present Value answers the question "how much money can I
borrow today under the terms of a specific mortgage and the monthly
payment I can afford."

Let us assume we can afford
(after accounting for taxes, insurance, utilities and living expenses)
$1,600 for a monthly mortgage payment. The current interest rate for a
30 year fixed mortgage is 5.25%.

| Action           | Comment     |
| ---------------- | ----------- |
| AC               | Clear State |
| 0 Min1      	   | Set PV (we don't know this) |
| 0 Min2           | Set FV (to all paid off) |
| 360 Min3         | Set n (30 years * 12 months) |
| 5.25 / 12 = Min4 | Set i (5.0% annual / 12 months) |
| 1600 Min5        | Set PMT (monthly payment) |
| P2               | Output: 289748.1479 |

Our budget is $289,748 plus whatever we have saved for a down payment.

## A more complex example using P0

For the final example how to use these programs let us assume the
following case. We need $300,000 and can afford a 5% down payment of
$15,000. We also anticipate retirement funds of about $140,000 in 13
years (like a 401k in the US or a Cash Value Life Insurance as more
usual in European countries). The bank offers us a 30 year fixed mortgage
at 5.25% annually.

We first calculate the monthly payment for that mortgage:

| Action           | Comment     |
| ---------------- | ----------- |
| AC               | Clear State |
| 285000 Min1      | Set PV      |
| 0 Min2           | Set FV (to all paid off) |
| 360 Min3         | Set n (30 years * 12 months) |
| 5.25 / 12 = Min4 | Set i (5.0% annual / 12 months) |
| P0               | Output: 1573.780551 |
| MinF             | Save default mortgage payment |

We now reduce the number of payments to 156 (13 years * 12 months)
and set the desired Future Value (FW) to $140,000.

| Action           | Comment     |
| ---------------- | ----------- |
| 13 * 12 = Min3   | Set number of months to 156 |
| 140000 Min 2     | Set FV to $140,000 |
| P0               | Output: 1896.932597 |
| - MRF =          | Output: 323,152046 |

This means that if we increase our monthly payment by $323.15
principal only to a total of $1,896.93 the remaining balance will
be $140,000. The retirement funds will pay off the mortgage and
we will live rent and mortgage free.

## Other use cases

While the previous examples primarily focused on mortgage payments, the
programs can be used for other calculations around annuities.

### Saving a monthly amount

For example, consider paying $500 every month for 10 years
into an investment account that yields 4% on average and compounds
the gains monthly.

| Action           | Comment     |
| ---------------- | ----------- |
| AC               | Clear State |
| 0 Min1           | Set PV (we start at zero balance) |
| 120 Min3         | Set n (10 years) |
| 4 / 12 = Min4    | Set i (4% split into months) |
| 500 Min5         | Set PMT |
| P2               | Output: -73624.9023 |

Don't be confused by the negative result. In this case the bank owes
us, so it is the opposite of a loan. Therefore the Future Value is
negative.

### Withdrawing an annual amount

The reverse of the previous example is an investment account where we
have a balance of $100,000 and the investment yields 4.5% on average.
Instead of withdrawing monthly, we only do so once a year.

| Action           | Comment     |
| ---------------- | ----------- |
| AC               | Clear State |
| 100000 Min1      | Set Present Value |
| 0 Min2           | Set Future Value |
| 20 Min 3         | Set n (in this case in years assuming the account also compounds annually) |
| 4.5 Min 4        | Set i (again, this time annual based) |
| P0               | Output: 7687.614433 |
