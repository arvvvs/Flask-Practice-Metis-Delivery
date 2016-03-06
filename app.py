from flask import Flask, render_template, request, json, jsonify, session, redirect, url_for, current_app
from flask.ext.mysqldb import MySQL
from flask_wtf import Form
from wtforms import TextField, StringField, SubmitField, validators
from wtforms.validators import Required

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'metis_delivery'
app.config['MYSQL_HOST'] = 'localhost'
mysql = MySQL(app)
#A form object for the main page asking for phone number
class request_phone_form(Form):
    phone = TextField('What is the number (Enter without spaces)', validators=[Required()])
    submit = SubmitField('Submit')
#A form object to create a new entry for a customer
class create_new_entry(Form):
    submit = SubmitField('Create new Entry?')
#A form entry that asks for new customers information
class new_entry(Form):
    name = TextField("What's the customers name?", validators=[Required()])
    address = TextField("What is the customers address?", validators=[Required()])
    phone = TextField("What is the customers phone number?", validators=[Required()])
    createNewEntry = SubmitField('Submit')
#created for the main page- asks for phone number, and shows deliveries
@app.route("/", methods=['POST', 'GET'])
def main():
    form = request_phone_form()
    if form.validate_on_submit():
        session['phone'] = form.phone.data
        return redirect(url_for('lookup'))
    return render_template("index.html", form = form)
#Renders page showing a list of delivery drivers (so that one can select to see the deliveries assigned to them)
#Gets names from a SQL query to tbl_delivery_drivers
@app.route("/delivery_drivers")
def drivers():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tbl_delivery_drivers")
    rv = cur.fetchall()
    return render_template("drivers.html", results = rv)
#Displays phone numbers from the search query entered
#shows all phone numbers similar to number typed so one can even enter the first four digits to see customers
@app.route('/results', methods=['POST', 'GET'])
def lookup():
    phone = session['phone'];
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tbl_customer_info WHERE phone_number LIKE \'"+ phone+"%\'")
    rv = cur.fetchall()
    return render_template("lookup.html", results = rv, phone=phone)
#This function adds the order to the deliveries list and assigns those orders based off random to a driver
#Unfortunately there is no indication if the order was placed
@app.route('/_order', methods=['POST','GET'])
def order_emplate():
    #uses javascript to get selected customers information through submit phone function in delivery.js file
    address = request.args.get('address', 0, type=str)
    phone = request.args.get('phone', 0, type=str)
    name = request.args.get('name', 0, type=str)
    cur = mysql.connection.cursor()
    cur.execute("SELECT delivery_person FROM tbl_delivery_drivers ORDER by RAND() LIMIT 1")
    rv = cur.fetchall()
    driver = str(rv[0][0])
    status = "Ready For Delivery"
    cur.execute("INSERT INTO tbl_deliveries (customer_name, delivery_status, customer_address, delivery_person) VALUES(\"" + name + "\", \"" + status +"\",\""+address + "\",\"" + driver+ "\");")
    mysql.connection.commit()
    cur.execute("SELECT LAST_INSERT_ID();")
    rv = cur.fetchall()
    id1=str(rv[0][0])
    cur.execute("INSERT INTO tbl_delivery_statuses VALUES(" +id1 + ", \"" + status +"\");")
    mysql.connection.commit()
    cur.close()
    return 'hello'
#Generates a page show completed deliveries
@app.route('/delivery_complete', methods=['POST','GET'])
def completed_updates():
    sql="SELECT * FROM tbl_deliveries where delivery_status = 'Completed Delivery'"
    cur = mysql.connection.cursor()
    cur.execute(sql)
    rv = cur.fetchall()
    cur.close()
    return render_template("completed.html", results=rv)
#updates deliveries to either "Out on Delivery" or "Completed Delivery"
@app.route('/delivery_updates', methods=['POST','GET'])
def delivery_updates():
    #Gets multiple orders using post
    multiselect = request.form.getlist('deliveries')
    button = request.form['submit']
    cur = mysql.connection.cursor()
    #if "Out on Delivery button is chosen"
    if(button == 'out'):
        #Since multiple orders can be chosen we cycle through that list and commit them one by one
        for id1 in multiselect:
            sql="UPDATE tbl_deliveries SET delivery_status = 'Out On Delivery' WHERE DeliveryID = " + id1 + ";"
            sql1 = "UPDATE tbl_delivery_statuses SET status = 'Out On Delivery' WHERE deliveryID = " + id1 + ";"
            cur.execute(sql)
            cur.execute(sql1)
            mysql.connection.commit()
    #If completed button is chosen
    if(button == 'completed'):
        for id1 in multiselect:
            sql="UPDATE tbl_deliveries SET delivery_status = 'Completed Delivery' WHERE DeliveryID = " + id1 + ";"
            sql1 = "UPDATE tbl_delivery_statuses SET status = 'Completed Delivery' WHERE deliveryID = " + id1 + ";"
            cur.execute(sql)
            cur.execute(sql1)
            mysql.connection.commit()
    cur.close()
    return redirect(url_for('deliveries'))
#Pages showing all deliveries in progress, including Driver Name, Customer Name, and Status
@app.route('/lookup_delivery', methods=['POST', 'GET'])
def deliveries():
    multiselect = request.form.getlist('drivers')
    cur =mysql.connection.cursor()
    sql= "SELECT * FROM tbl_deliveries WHERE (delivery_status = \'Ready For Delivery\' OR \'ready for delivery\' OR delivery_status = 'Out On Delivery')"
    if multiselect:
        sql +="AND ("
        for driver in multiselect:
            sql +="delivery_person = '" + driver + "'  OR "
        sql += " delivery_person = \"placeholder\" );"
    cur.execute(sql)
    rv = cur.fetchall()
    cur.close()
    return render_template("deliveries.html",results=rv) 
#test funciton
@app.route('/hello', methods=['POST', 'GET'])
def submitPhone():
    _phone = request.form['submitPhone']
    return render_template("lookup.html", phone = _phone)
#Gets the customer information that needs to be edited and renders an html snippet to page
#Allowing one to edit the customer info
@app.route('/_edit_customer', methods=['POST', 'GET'])
def editCustomer():
    form = new_entry()
    #Uses post and javascript to get the information 
    #needs javascript for ajax
    address = request.args.get('address', 0, type=str)
    phone = request.args.get('phone', 0, type=str)
    name = request.args.get('name', 0, type=str)
    form.address.data = address
    form.phone.data = phone
    form.name.data = name
    #returns a rendered template by json so it can be rendered in page
    return json.dumps(render_template("edit_entry.html", form=form))
#A function to update the customer info once the new information is provided
@app.route('/_finish_edit', methods=['POST','GET'])
def submitEdits():
    #uses javascript to get thew new info
    phone = request.args.get('phone', 0, type=str)
    name = request.args.get('name', 0, type=str)
    address = request.args.get('address', 0, type=str)
    phone_value = request.args.get('phone_value', 0, type=str)
    if phone!='0'and name!='0' and address!='0':
        cur = mysql.connection.cursor()
        cur.execute("UPDATE tbl_customer_info SET name=\"" + name + "\", address=\"" + address + "\",phone_number = \"" + phone + "\" WHERE phone_number = \""+phone_value+"\"")
        mysql.connection.commit()
    return 'hello'
#Allows employee to enter new information on a new customer
@app.route('/new-entry', methods=['POST', 'GET'])
def newEntry():
    form = new_entry()
    form.phone.data = session['phone']
    #uses post and validates submit
    if form.validate_on_submit():
        session['address'] = form.address.data
        session['phone'] = form.phone.data
        session['name'] = form.phone.data
        address = session['address']
        name = session['name']
        phone =session['phone']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO tbl_customer_info VALUES( \" " + name + "\", \"" + address + "\",\"" + phone + "\")")
        mysql.connection.commit()
        rv = cur.fetchall()
        return redirect(url_for('lookup'))
    return render_template('new_entry.html', form = form)
if __name__=="__main__":
    app.run(debug=True)

