from flask_frozen import Freezer
from money_dashboard import money_dashboard

freezer = Freezer(money_dashboard)

if __name__ == '__main__':
    freezer.freeze()
