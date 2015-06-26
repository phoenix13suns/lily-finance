from __future__ import division

__author__ = 'Steve'

import MySQLdb as mdb
import time

TRANSACTION_TABLE = "transaction"
BALANCE_TABLE = "balance"
TRANS_DETAIL_TABLE = "trans_detail"
LINE_SEPARATOR = "----"


class Transaction:
    def __init__(self, owner, amount, date, message, who, type1):
        self.owner = owner
        self.amount = amount
        self.date = date
        self.message = message
        self.who = who
        self.type = type1
        self.ts = get_timestamp()
        if type1 == 'buy':
            self.amount_per_each = self.amount / len(self.who)
            str1 = LINE_SEPARATOR + " shared with "
            cnt = 0
            for i in who:
                if cnt > 0:
                    str1 += ","
                str1 += i
                cnt += 1
            self.message += str1


def conn():
    con1 = mdb.connect(host="127.0.0.1", user="root", passwd="123", db="lily", port=3309)
    return con1


def get_timestamp():
    return long(time.time() * 100)


def get_all_transaction(con):
    cursor = con.cursor()
    sql = "select * from {0} order by id desc".format(TRANSACTION_TABLE)
    cursor.execute(sql)
    rows = cursor.fetchall()
    return rows


def save_transaction(con, trans, username):
    cursor = con.cursor()
    sql = "insert into transaction values('{0}' ,  '{1}' , '{2}' , '{3}' ,  {4} , '{5}')".format(trans.ts, username,
                                                                                                 trans.type,
                                                                                                 trans.message,
                                                                                                 trans.amount,
                                                                                                 trans.date)
    cursor.execute(sql)
    con.commit()
    if trans.type == 'buy':
        for debtor in trans.who:
            if debtor == username:
                continue
            sql = "insert into trans_detail ( trans_id,debtor,amount) values({0},'{1}',{2})".format(trans.ts,
                                                                                                    debtor,
                                                                                                    trans.amount_per_each)
            cursor.execute(sql)
            con.commit()
            change_balance(con, debtor, username, trans.amount_per_each, trans.ts)
    elif trans.type == 'pay':
        change_balance(con, trans.who, username, trans.amount, trans.ts)
    print "transaction saved"


# money goes to creditor
# 1. debtor active pay
# 2. debtor passive pay (debtor buy sth)
def change_balance(con, creditor, debtor, amount, trans_id):
    current = get_balance(con, creditor, debtor)
    current2 = get_balance(con, debtor, creditor)
    print ""
    print debtor, "paid $", amount, "to", creditor
    if current == 0:
        remain = current2 + amount
        update_balance(con, debtor, creditor, remain)
        msg = "{0} owe {1} from ${2} to ${3}".format(creditor, debtor, current2, remain)
        print creditor, "owe", debtor, "from $", current2, "to $", remain
    elif current > amount:
        remain = current - amount
        update_balance(con, creditor, debtor, remain)
        msg = "{0} owe {1} from ${2} to ${3}".format(debtor, creditor, current, remain)
        print debtor, "owe", creditor, "from $", current, "to $", remain
    else:
        remain = amount - current
        update_balance(con, creditor, debtor, 0)
        update_balance(con, debtor, creditor, remain)
        msg = "{0} owe {1} from ${2} to ${3}".format(creditor, debtor, -current, remain)
        print creditor, "owe", debtor, "from $", -current, "to $", remain
    append_transaction_message(con, trans_id, msg)


def update_balance(con, creditor, debtor, amount):
    cursor = con.cursor()
    sql = "update balance set amount={0} where creditor='{1}' and debtor='{2}'".format(amount, creditor, debtor)
    cursor.execute(sql)
    con.commit()
    print "update balance", creditor, debtor, amount


def user_authentication(con, username, password):
    cursor = con.cursor()
    sql = "select username from users where username='{0}' and password='{1}' ".format(username, password)
    cursor.execute(sql)
    result = cursor.fetchone()
    return result


def get_all_normal_users(con):
    cursor = con.cursor()
    sql = "SELECT username from users where type='normal'"
    cursor.execute(sql)
    result = cursor.fetchall()
    array = []
    for i in result:
        array.append(i[0])
    return array


def get_creditor_debtor_list(con):
    users = get_all_normal_users(con)
    cursor = con.cursor()
    list1 = []
    for u in users:
        sql = "select creditor,amount from balance where debtor='{0}'".format(u)
        cursor.execute(sql)
        result = cursor.fetchall()
        tuple1 = (u, result)
        list1.append(tuple1)
    return list1


def get_balance(con, creditor, debtor):
    cursor = con.cursor()
    sql = "select amount from  balance where creditor ='{0}' and debtor='{1}'".format(creditor, debtor)
    cursor.execute(sql)
    result = cursor.fetchone()
    return result[0]


def append_transaction_message(con, trans_id, message):
    message = LINE_SEPARATOR + message
    cursor = con.cursor()
    sql = "update transaction set message=concat(message,'{0}') where id={1}".format(message, trans_id)
    cursor.execute(sql)
    con.commit()


if __name__ == "__main__":
    con = conn()
    # get_all_transaction(con)
    # r = user_authentication(con, 'zl', '123')
    # r = get_all_normal_users(con)
    # print r == None
    list = get_creditor_debtor_list(con)
    # print r
    for item in list:
        print item[0]
        for j in item[1]:
            print j[0], j[1]
        print ""