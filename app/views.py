import os
from flask import render_template, Flask
from flask.ext.sqlalchemy import SQLAlchemy
import pandas as pd
from app import app, db


@app.route('/')
def index():
    data = pd.read_sql_table('transaction', db.engine)
    del data['id'], data['note']
    data['reconciled'] = data['reconciled'].astype(str)
    reconciled = data.reconciled
    reconciled[reconciled == 'True'] = '<i class="fa fa-check-square-o"></i>'
    reconciled[reconciled == 'False'] = '<i class="fa fa-square-o"></i>'
    data['reconciled'] = reconciled
    df = pd.DataFrame({'correlation':[0.5, 0.1,0.9], 'p_value':[0.1,0.8,0.01]})
	fmt = format.DataFrameFormatter(data, 
		                            formatters={'reconciled':lambda x: '<i class="fa fa-check-square-o"></i>' 
		                                                               if x==True else '<i class="fa fa-square-o"></i>',
		                                        'reconciled':lambda x: '<i class="fa fa-check-square-o"></i>' 
		                                                               if x==True else '<i class="fa fa-square-o"></i>'})

    data = data.sort(['date'])
    data['balance'] = data['amount'].cumsum()

    # balance = data.balance
    # def _color_success(value):
    # 	return '<td class="success"> ' + str(value) + '</td>'
    # def _color_warning(value):
    # 	return '<td class="warning"> ' + str(value) + '</td>'
    # balance[balance > 0] = balance[balance > 0].apply(_color_success)
    # balance[balance <= 0] = balance[balance <= 0].apply(_color_warning)
    # data['balance'] = balance

    data = data.to_html(classes=['table table-hover table-bordered colorMe'], index=False, escape=False)
    return render_template('index.html', data=data)
