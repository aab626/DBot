import random

#############
# CONSTANTS

CURRENCY_SYMBOL = "D\U000000A2"
CURRENCY_NAME_SINGULAR = "DCoin"
CURRENCY_NAME_PLURAL = "DCoins"

LOTTERY_NUMBERS_IN_POOL = 17
LOTTERY_NUMBERS_TO_DRAW = 10
LOTTERY_PRIZE_DICTIONARY = {10: 100, 9: 50, 8: 15, 7: 10}
LOTTERY_MAX_GAMES_ALLOWED = 15
LOTTERY_COST = 5

####################################
# GENERAL ECONOMY FUNCTIONS

# Returns a string, with the standard money format
# modes:
# simple	$12
# verbose	12 dollars | 1 dollar
def pMoney(amount, mode="simple"):
    # verbose
    if mode == "verbose":
        return "{} {}".format(amount, CURRENCY_NAME_PLURAL if amount > 1 else CURRENCY_NAME_SINGULAR)
    # simple (default)
    else:
        return "{} {}".format(amount, CURRENCY_SYMBOL)


####################################
# LOTTERY COMMAND RELATED FUNCTIONS


# Generates a ticket for the lottery
def generateTicket():
    ticket = []
    while len(ticket) < LOTTERY_NUMBERS_TO_DRAW:
        n = random.randint(1, LOTTERY_NUMBERS_IN_POOL)
        if n in ticket:
            continue
        else:
            ticket.append(n)

    ticket.sort()
    return ticket


# returns the quantity of number that are in both tickets (hits)
def checkTicket(ticket, winningTicket):
    hits = sum([1 if t in winningTicket else 0 for t in ticket])
    return hits


def gameLottery(gamesToPlay):
    winningTicket = generateTicket()

    lotteryReport = {"winningTicket": winningTicket, "games": []}
    while len(lotteryReport["games"]) < gamesToPlay:
        ticket = generateTicket()
        if ticket in lotteryReport["games"]:
            continue

        hits = checkTicket(ticket, winningTicket)
        prize = LOTTERY_PRIZE_DICTIONARY[hits] if hits in LOTTERY_PRIZE_DICTIONARY.keys(
        ) else 0

        lotteryDict = {"ticket": ticket, "hits": hits, "prize": prize}
        lotteryReport["games"].append(lotteryDict)

    return lotteryReport
