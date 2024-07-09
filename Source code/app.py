from flask import Flask, render_template ,render_template_string , request ,flash,redirect,url_for,make_response,jsonify,session
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField , IntegerField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from folium import plugins
import matplotlib.pyplot as plt
from sqlalchemy import create_engine ,Column, Integer, ForeignKey ,join
import pandas as pd
import csv, sys
from sqlalchemy.orm import relationship
from routes import paths
from geopy.distance import geodesic 
import random,datetime
from compare import coordinates_allot ,paths_allocated
import jsonpickle
import io
import tilemapbase
import base64 


#setting up  a flask application  
app = Flask(__name__)


app.secret_key='teamtechconnect'

#creating a database for data management 
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SECRET_KEY'] = 'teamtechconnect'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.app_context().push()


#admin pass to access admin page
admin_pass='techconnect'


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))





#creating a model for database 
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    balance = db.Column(db.Float, nullable=False)
    mobnumber= db.Column(db.Integer,nullable=False)
    bills = relationship("Bill", backref="User") 

class Admindata(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    location1 = db.Column(db.String(100), nullable=False)
    location2 = db.Column(db.String(100), nullable=False)
    Bike = db.Column(db.Integer(), nullable=False)
    Car = db.Column(db.Integer(), nullable=False)
    Truck = db.Column(db.Integer(), nullable=False)
    Others = db.Column(db.Integer(), nullable=False)

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    destination1 = db.Column(db.String(100), nullable=False)
    destination2 = db.Column(db.String(100), nullable=False)
    vehicle = db.Column(db.String(100), nullable=False)
    fine = db.Column(db.Float, nullable=False)
    total= db.Column(db.Float, nullable=False)
    distance = db.Column(db.Float, nullable=False)
    tax = db.Column(db.Float, nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))






# creating a registration form using flask form 
class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=40)], render_kw={"placeholder": "Please enter your name."})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    
    balance = IntegerField()
    
    email = StringField("Email",validators=[
                           InputRequired(), Length(min=4, max=60)], render_kw={"placeholder": "Please enter your email address."})
    
    mobnumber = IntegerField(validators=[InputRequired()], render_kw={'placeholder': 'Enter Phone Number'})


    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            return flash("That username already exists.")
            # raise ValidationError(
            #     'That username already exists. Please choose a different one.')




# creating a login form using flask form 
class LoginForm(FlaskForm):
    email = StringField("Email",validators=[
                           InputRequired(), Length(min=4, max=60)], render_kw={"placeholder": "Please enter your email address."})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')




#making a route page for login 
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data): #checking the data of user in database
                login_user(user)
                return redirect(url_for('profile'))
        flash("Username or password is incorrect . please register if you don't have an account")        
    return render_template('login.html', form=form)





#making a route page for profile , if the login of user satisfied
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    balance = round(current_user.balance,2)
    username = current_user.username
    number=current_user.mobnumber
    user=current_user.id
    # bills = Bill.query.all()  # Get all bills
    bills = Bill.query.filter_by(user_id=user).all()  # Get bills for a specific user

    return render_template('profile.html', username=username,balance=balance,number=number,user=bills)




#logout function if user want to logout
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))




#making a route page for registration 
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    form.balance.data = 10000 # 10000Rs is given to user for demo simulation
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data) # encoding the password of user for security
        new_user = User(username=form.username.data, password=hashed_password,balance=form.balance.data,mobnumber=form.mobnumber.data,email=form.email.data)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)






#locations and there coordinates for testing , pseudo entry and exit
locations = {
      "nagpur": ( 21.15235,79.08103),
      "wardha": ( 20.77272,78.59551),
      "karanja": (20.4983, 77.47285)
      }      

# accesssing the  define toll zone from csv file 
file2_path = "paths/zone.csv"

#setting the initial value for fine (the fine changes according to user speed and steps)
fine=120


# making a simulation process
@app.route('/simulation', methods=['GET', 'POST'])
@login_required
def simulation():
  # To access current date for bill generation 
  date_today = datetime.date.today()

  #setting the starting and ending value for simulation 
  if request.method == 'POST':
    starting_coordinates = request.form['DecimalInput']
    ending_coordinates = request.form['DecimalInput1']
    vehicle_type = request.form['Vehicle_type']
    # weather_condition = request.form['weather']
    
    
    #allocating the coordinates to start and end ,to check wether the coordinates are same or not  
    start=coordinates_allot(starting_coordinates)
    end=coordinates_allot(ending_coordinates)

    #the pseudo entry and exit is in the form of csv , allocating the csv file into file1_path for further simulation  
    file1_path=paths_allocated(starting_coordinates,ending_coordinates)
    
    # generating  avg speed for simulation , changes every time 
    speed_limits = [10, 20, 30,40,50,60,70,80,90,100,110,120]  # List of speed limits
    num_steps = random.randint(6,len(speed_limits)) 
    steps = [random.randrange(10) for _ in range(num_steps)]  # Generate random steps

    # Add random steps to each speed limit
    modified_limits = [limit + step for limit, step in zip(speed_limits, steps)]
    avg_speed=round((sum(modified_limits)/12))
    
    
    # checking boths the entry and exit are same or not
    if start==end:
        flash("both the location are same")
        return render_template('simulate.html')
    else:
        #reading csv file and storing in to variable
        df1 = pd.read_csv(file1_path) # car simulation data
        df2 = pd.read_csv(file2_path) # zone data

        #checking the coordinates are in the zone or not 
        def compare_coordinates(df1_row, df2_row):

  
             threshold = 0.01  
             x_diff = abs(df1_row["latitude"] - df2_row["latitude"])
             y_diff = abs(df1_row["longitude"] - df2_row["longitude"])
             return x_diff <= threshold and y_diff <= threshold

        # Iterating through rows in df1 and comparing with all rows in df2
        matches = []
        for index1, row1 in df1.iterrows():
            for index2, row2 in df2.iterrows():
                if compare_coordinates(row1, row2): 
                    matches.append((index1, index2))
        # if the data matches , fetch the matching  stating coordinate and  ending coordinate 
        if matches:
            start_lat=df1.loc[matches[0][0], 'latitude']
            start_lon=df1.loc[matches[0][0], 'longitude']
            end_lon=df2.loc[matches[-1][1], 'longitude']
            end_lat=df2.loc[matches[-1][1], 'latitude']
            
        
            
            # reading csv file of vehicle simulation to generate the paths/route the vehicle traveled during trip.
            df = pd.read_csv(file1_path)
            selected_columns = df[["longitude", "latitude"]]
            tilemapbase.init(create=True)

            expand = 0.002
            extent = tilemapbase.Extent.from_lonlat(
                        selected_columns.longitude.min() - expand,
                        selected_columns.longitude.max() + expand,
                        selected_columns.latitude.min() - expand,
                        selected_columns.latitude.max() + expand,
                         )

            map_projected = selected_columns.apply(
            lambda x: tilemapbase.project(x.longitude, x.latitude), axis=1
            ).apply(pd.Series)
            map_projected.columns = ["x", "y"]

            tiles = tilemapbase.tiles.build_OSM()

            fig, ax = plt.subplots(figsize=(8, 8), dpi=300)
            ax.xaxis.set_visible(False)
            ax.yaxis.set_visible(False)
            plotter = tilemapbase.Plotter(extent, tiles, height=600)
            plotter.plot(ax, tiles, alpha=0.8)
            ax.plot(map_projected.x, map_projected.y, color="red", linewidth=1)
            plt.axis("off")

            # Creating buffer for image data
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0, dpi=300)
            buf.seek(0)

            # Encoding the image data to base64 to emmbeded it into html file
            image_data = base64.b64encode(buf.read()).decode("utf-8") 
            
            #fetching the data from admindata to apply the current price of tax for each vehicle according to admin
            data1 = Admindata.query.filter_by(location1=starting_coordinates, location2=ending_coordinates).all()
            data2 = Admindata.query.filter_by(location1=ending_coordinates, location2=starting_coordinates).all()
            if data1:
                for data in data1: 
                   vh1=data.Bike
                   vh2=data.Car
                   vh3=data.Truck
                   vh4=data.Others
                rate=vh4
                # print(vh1,vh2,vh3,vh4,vehicle_type) 
            elif data2:
                for data in data2: 
                   vh1=data.Bike
                   vh2=data.Car
                   vh3=data.Truck
                   vh4=data.Others
                rate=vh4           
 
            #Allocating the rates according to the vehicle type 
            rate=vehicle_allocate(vehicle_type,vh1,vh2,vh3,vh4)        
            rates=rate 

            #calculating the  distance between staring and ending coordinates
            distance_rest= geodesic((start_lon,start_lat), (end_lon,end_lat)).km
            distance=round(distance_rest,3)

            #calculating the time
            time_hr=distance/avg_speed
            time=round(time_hr*60)

            #calculating the  tax
            tax=round((distance)*(rates),2)
            
            #total amount calculation, including fine    
            total_fine=calculate_fine(avg_speed,50) #if the vehicle is overspeeding the fine is charged
            total_tax=total_fine+tax
            

            #modifying the balance of current user
            balance = current_user.balance
            id=current_user.id

            if balance <tax:
                flash("insufficent amount")

            else:

                #checking is fine is charged for the simulation 
                if total_fine>0:
                    user = User.query.get(id)
                    user.balance= user.balance-tax-total_fine
                    db.session.commit()
                    flash("Amount is deducted ! please check account for more")
                    flash("fine is charge!!")
                    
                else:   
                    deduct_tax(tax,id)    
                    flash("Amount is deducted ! please check account for more")
            
            #generated bill is added to user profile 
            user1=current_user.email
            user = User.query.get(id)
            bill1=Bill(destination1=starting_coordinates,
                       destination2=ending_coordinates,
                       fine=total_fine ,
                       total=total_tax,
                       distance=distance,
                       tax=tax,
                       user_id=id,
                       vehicle=vehicle_type)
            user.bills.append(bill1)
            db.session.add(user)
            db.session.commit()
           
        else:
            render_template('simulate.html')          

    
    

    # if sumulation success then the result page is displayed ,else reload the simulation page
    return render_template('result.html',
                           distance=distance,
                           vehicle=vehicle_type,
                           speed=avg_speed,
                           tax=tax,
                           username=current_user.username,
                           number=current_user.mobnumber,
                           id=current_user.id,
                           destination1=starting_coordinates.upper(),
                           destination2=ending_coordinates.upper(),
                           date=date_today,
                           email=current_user.email,
                           time=time,
                           fine=total_fine,
                           total=total_tax,
                           image=image_data,
                           bike=vh1,
                           car=vh2,
                           truck=vh3,
                           other=vh4,
                           )

  #if any of the condition unsatisfied , return the to simulation page  
  else:
    return render_template('simulate.html')





#method to debit tax amount from current user account
def deduct_tax(tax_amount, user_id):
    user = User.query.get(user_id)
    user.balance -=tax_amount
    db.session.commit() 





# method to alloct the rate of vehicle 
def vehicle_allocate(vehicle_type,vh1,vh2,vh3,vh4):
  if vehicle_type=="Truck": 
        rate=vh3 
        return rate 
  elif vehicle_type=="Bike":
        rate=vh1 
        return rate  
  elif vehicle_type=="Car":
        rate=vh2 
        return rate 
  else :
        rate=vh4
        return rate 



def vehicle_types(select,rates):
    if select=="Truck":
        rate=rates
        print("2")
    elif select=="Bike":
        rate=rates
        print("3")
    elif select=="Car":
        rate=rates
        print("4")
    elif select=="Others":
        rate=rates
        print("1")
    return rate    


#method to calculate the fine for the vehicle (if Avg.speed > 50)
def calculate_fine(speed, speed_limit):
  # Checking if driver is over speeding
  if speed >= speed_limit:
     base_fine = 100 # No fine if under speed limit
     excess_speed = speed - speed_limit
     surcharge_per_mph = 5  # Hypothetical surcharge
     speeding_surcharge = excess_speed * surcharge_per_mph
     total_fine = base_fine + speeding_surcharge 
  
  else:
      total_fine=0
  
  return total_fine






#login page for admin 
@app.route('/admin_login',methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        admin_password = request.form['pwd1']

        user = User.query.filter_by(email=email).first()
        
        #if the password and the admin password is matched give access
        if user and bcrypt.check_password_hash(user.password, password):
            if (admin_pass == admin_password):
               session['email'] = user.email
               return redirect('/admin')
            else:
                 flash("Username or password is incorrect . please register if you don't have an account")
                 return render_template('admin_login.html',error='Invalid user')
    flash("Username or password is incorrect ")
    return render_template('admin_login.html')





#admin page to make changes in  the rate of the vehicle 
@app.route('/admin',methods=['GET','POST'])
def admin():
    if request.method == 'POST':
        location1 = request.form['loc1']
        location2 = request.form['loc2']
        Bike = int(request.form['bike'])
        Car = int(request.form['car'])
        Truck = int(request.form['truck'])
        Others = int(request.form['others'])
        
        #checking is the loaction are same or not
        if (location1==location2):
           return redirect('/admin')
        existing_data = Admindata.query.filter_by(location1=location1, location2=location2).first()
        
        #checking is the data entered by the admin is same as the previous one or new 
        if existing_data:
            # Update existing data (if locations match)
            existing_data.Bike = Bike
            existing_data.Car = Car
            existing_data.Truck = Truck
            existing_data.Others = Others
            db.session.commit()
            return redirect('/price')  # Redirect to price page
        else:         
          new_data = Admindata(
            location1=location1,
            location2=location2,
            Bike=Bike,
            Car=Car,
            Truck=Truck,
            Others=Others,
        )       
        db.session.add(new_data)
        db.session.commit()
        return redirect('/price' )
      
    return render_template('admin.html')




#function for admin to logout form the admin page
@app.route('/logout_ad', methods=['GET', 'POST'])
@login_required
def logout_ad():
    logout_user()
    return redirect(url_for('admin_login'))




#default page 
@app.route('/')
def home():
    return render_template('home.html')




#page to display the current prices of the toll zone according to vehicle type   
@app.route('/price')
def price():
   new_data = Admindata.query.all()  # Fetch all users
   return render_template('price.html', new_data=new_data)




#user can see the zone under toll plaza
@app.route('/map')
def map():
 return paths()




#page for payment to user account 
@app.route ('/recharge', methods=['GET' ,'POST'])
@login_required
def recharge():
 return render_template('pay.html')


#page to show all the user data 
@app.route('/user_data')
@login_required
def userdata():
    bills=Bill.query.all()
    return render_template('user_data.html',bills=bills)


#page to show about us  
@app.route('/About_us')
def about():
    return render_template('about_us.html')



if __name__ == "__main__":
  app.run(debug=True)