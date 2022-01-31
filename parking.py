from hashlib import pbkdf2_hmac
from os import urandom
import shelve
import datetime
from getpass import getpass
## getpass will give a warning on IDLE and IDLE will show the password
## getpass works correctly on Windows Command Prompt


hash_rounds = 100000  ## number of hash iterations for password hashing
hash_name = 'sha512'  ## name of hash algorithm for password hashing

## db is a shelve with three dictionaries, 'stundets', 'parking' and 'users'.
## db['students'] is a dictionary of stundets with the key set to Student ID
## db['parking'] is a two-dimensional dictionary for each level and spaces where the key is the
## level number and space number respectively. db['parking'] must be fully initialised before.
## Check bottom of file for initialising process
## db['users'] is a dictionary of users with key set to User ID
db = shelve.open('parkingdb', writeback=True)

parking_levels = 3   ## number of total parking level
parking_spaces = 15  ## number of parking spaces in each level

def get_spaceid(studentid):
    """Search for the Parking Space ID of macthing Student ID"""
    spaceid = ''
    for level in range(1, parking_levels + 1):
            for space in range(1, parking_spaces + 1):
                if (db['parking'][level][space]['studentid'] == studentid) and (db['parking'][level][space]['status'] == 'assigned'):
                    spaceid = 'L' + str(level) + '0' + str(space)
                    break
            if spaceid != '':
                break
    return spaceid


def login():
    """Show the login screen, show menu if login successful"""
    userid = input('Enter username: ')
    pswd = getpass('Enter password: ')

    if userid in db['users']:
        user = db['users'][userid]
        ## user['pswd'] is the value returned by pbkdf2_hmac() during new user creation (new_user())
        if user['pswd'] == pbkdf2_hmac(hash_name, pswd.encode(), user['salt'], hash_rounds):
            print('Welcome ' + user['fname'] + ' ' + user['lname'] + '.')
            menu()
        else:
            print('Incorrect username or password!')
            login()
    else:
        print('Incorrect username or password!')
        login()

def menu():
    print('')
    print('1. Register new Student')
    print('2. Cancel a student')
    print('3. Update student details')
    print('4. Display report')
    print('5. Display student details')
    print('6. Students by expiry date')
    print('7. Display grid')
    print('8. User menu')
    print('9. Logout')      
    print('0. Exit')

    try:
        choice = int(input())
    except:
        print('Enter a valid number!')
        menu()
    else:
        if choice == 1: new_student()
        elif choice == 2: cancel_student()
        elif choice == 3: update_student()
        elif choice == 4: print_report()
        elif choice == 5: student_details()
        elif choice == 6: students_by_expiry()
        elif choice == 7: print_grid()
        elif choice == 8:
            print('1. List registered UserIDs')
            print('2. Register new UserID')
            print('3. Delete UserID')
            print('4. Change password')
            choice = int(input())
            if choice == 1: list_users()
            elif choice == 2: new_user()
            elif choice == 3: del_user()
            elif choice == 4: change_pass()
            else:
                print('Enter a valid number!')
                menu()
        elif choice == 9: login()
        elif choice == 0: save_and_exit()
        else:
            print('Enter a valid number!')
            menu()

def new_student():
    """Register a new student, assign a free parking space and store in db"""
    print('Enter student details')
    studentid = input('Enter StudentID: ')
    fname = input('Enter First Name: ')
    lname= input('Enter Last Name: ')
    contact = input('Enter mobile number: ')
    email = input('Enter e-mail address: ')
    carnumber = input('Enter car number: ')
    regdate = datetime.date.today()

    if (studentid in db['students']):
        print('Error: StudentID ' + studentid + ' already registered')
    else:
        spaceid = ''  ## search for an available parking space
        for level in db['parking']:
            for space in db['parking'][level]:
                if db['parking'][level][space]['status'] == 'available':
                    db['parking'][level][space]['status'] = 'assigned'
                    db['parking'][level][space]['studentid'] = studentid
                    spaceid = 'L' + str(level) + '0' + str(space)
                    break
            if spaceid != '':
                break
        if spaceid == '':
            print('Sorry, parking full')
        else:  ## save stundent information only if there is an available parking space
            db['students'][studentid] = {'fname':fname, 'lname':lname, 'contact':contact, 'email':email, 'carnumber':carnumber, 'regdate':regdate}
            db.sync()
            print('New student ' + studentid + ' registered successfully with parking space ' + spaceid)
    menu()

def cancel_student():
    """remove student details from db['students'] and set the parking space to available"""
    studentid = input('Enter studentid to cancel: ')
    spaceid = ''
    
    if (studentid in db['students']):
        del db['students'][studentid]
        for level in db['parking']:
            for space in db['parking'][level]:
                if db['parking'][level][space]['studentid'] == studentid:
                    spaceid = 'L' + str(level) + '0' + str(space)
                    db['parking'][level][space]['status'] = 'available'
                    db['parking'][level][space]['studentid'] = ''
                    db.sync()
                    print('Student ' + studentid + ' cancelled. Parking space ' + spaceid + ' set to available')
                    break
            if spaceid != '':
                break
        if spaceid == '':
            print('Error: Student ' + studentid + ' does not have parking space')
    else:
        print('Error: Student ' + studentid + ' not registered')
    menu()

def update_student():
    """Update information of a registered student"""
    studentid = input('Enter studentid to update: ')
    if studentid not in db['students']:
        print('Error: Student ' + studentid + ' not registered')
    else:
        student = db['students'][studentid]
        print(student['fname'] + ' ' + student['lname'] + '(' + studentid + ')')
        print("1. Update car number")
        print("2. Update contact number")
        print("3. Update email address")
        print("4. Update registration date to today")

        choice = int(input())
        if choice == 1:
            carnumber = input('Enter new car number: ')
            db['students'][studentid]['carnumber'] = carnumber
            db.sync()
            print('Car number of student ' + studentid + ' changed to ' + carnumber)
        elif choice == 2:
            contact = input('Enter new mobile number: ')
            db['students'][studentid]['contact'] = contact
            db.sync()
            print('Mobile number of student ' + studentid + ' changed to ' + contact)
        elif choice == 3:
            email = input('Enter new e-mail address: ')
            db['students'][studentid]['email'] = email
            db.sync()
            print('E-mail address of student ' + studentid + ' changed to ' + email)
        elif choice == 4:
            db['students'][studentid]['regdate'] = datetime.date.today()
            db.sync()
            print("Registration date updated to today's date")
        else:
            print('Error: Please enter correct number')
    menu()

def print_report():
    """Print a report of all registered users"""
    print('StudentID | Car No. | Parking | Registerd |  Expiry')
    print('==========|=========|=========|===========|=========')
    for studentid in db['students']:
        student = db['students'][studentid]
        spaceid = get_spaceid(studentid)
        
        if spaceid == '': ## this should not happen in a correct db
            print("Error: No parking space found for student " + studentid)

        print('{:^10.10}|{:^9.9}|{:^9.9}|{:^11.11}|{:^10.10}'.format(studentid, student['carnumber'], spaceid, str(student['regdate']), str(student['regdate'] + datetime.timedelta(days=120))))
    input("Press enter to return to menu")
    menu()

def student_details():
    """Print all the details of a student"""
    studentid = input('Enter studentid: ')
    if studentid in db['students']:
        student = db['students'][studentid]
        exp_date = student['regdate'] + datetime.timedelta(days=120)
        days_left = (exp_date - datetime.date.today()).days
        spaceid = get_spaceid(studentid)
        student = db['students'][studentid]
        print('Student ID: ' + studentid)
        print('First Name: ' + student['fname'])
        print('Last Name: ' + student['lname'])
        print('Contact No.: ' + student['contact'])
        print('E-mail: ' + student['email'])
        print('Car Number: ' + student['carnumber'])
        print('Parking: ' + spaceid)
        print('Registerd on: ' + str(student['regdate']))
        print('Expire on: ' + str(exp_date))
        print('Days left: ' + str(days_left) + ' days')
        if (days_left < 0):
            print("Warning: This student's registration has expired!")

        input('Press enter to continue...')
    else:
        print('Error: Student ' + studentid + ' not registered')
    menu()


def students_by_expiry():
    """Find the students who are going to expire in a certain amount of days"""
    try:
        min_days = int(input('Students who have less than how many days? Enter a number: '))
    except:
        print('Enter a valid number')
        menu()
    else:
        print('StudentID |  Expiry   | Days | SpaceID | Student Name')
        print('=======================================================')
        for studentid in db['students']:
            student = db['students'][studentid]
            exp_date = student['regdate'] + datetime.timedelta(days=120)
            days_left = (exp_date - datetime.date.today()).days
            if (days_left < min_days):
                print('{:9.9} | {:9.9} | {:4.4} | {:7.7} | {} {}'.format(studentid, str(exp_date), str(days_left), get_spaceid(studentid), student['fname'], student['lname']))
    input("Press enter to continue...")
    menu()

def print_grid():
    """Print each level with all the parking spaces as a grid"""
    spaces_per_row = 5
    tlc = '┌────'
    tmc = '────╥────'
    trc = '────┐'
    mlc = '╞════'
    mmc = '════╬════'
    mrc = '════╡'
    blc = '└────'
    bmc = '────╨────'
    brc = '────┘'
    for level in range(1, parking_levels + 1):
        print('Level: ' + str(level))
        print(tlc + tmc*(spaces_per_row-1) + trc) ## top border
        
        for row in range(parking_spaces//spaces_per_row):
            print('│', end='') ## spaceid row left border
            ## space id
            for space in range(row * spaces_per_row + 1, min((row+1) * spaces_per_row, parking_spaces)+1):
                print('  L{:1}{:02}  '.format(level,space), end='')
                if (space % spaces_per_row > 0): ## between each spaceid
                    print('║', end='')
            print('│') ## spaceid row right border
            
            if (row < parking_spaces//spaces_per_row ): ## studentid row left border
                print('│', end='')
            ## student id
            for space in range(row * spaces_per_row + 1, min((row+1) * spaces_per_row, parking_spaces)+1):
                print('{:^8.8}'.format(db['parking'][level][space]['studentid']), end='')
                if (space % spaces_per_row > 0): ## between each studentid 
                    print('║', end='')
            print('│') ## studentid row right border
            if (row < parking_spaces//spaces_per_row - 1): ## between each row (middle border)
                print(mlc + mmc*(spaces_per_row-1) + mrc)
                
        print(blc + bmc*(spaces_per_row-1) + brc) ## bottom border
    input()
    menu()

def new_user():
    """Register a new user"""
    fname = input('Enter First Name: ')
    lname = input('Enter Last Name: ')
    userid = input('Enter UserID: ')
    pswd = getpass('Enter Password: ')

    if userid in db['users']:
        print('Error: User already exists')
    else:
        salt = urandom(parking_spaces + 1)
        pswd_hash = pbkdf2_hmac(hash_name, pswd.encode(), salt, hash_rounds)

        db['users'][userid] = {'fname':fname, 'lname':lname, 'pswd':pswd_hash, 'salt':salt}
        db.sync()
        print('new user ' + userid + ' registered successfully')
    menu()

def list_users():
    """List all the registered users with their full name and User ID"""
    for userid in db['users']:
        user = db['users'][userid]
        print(user['fname'] + ' ' + user['lname'] + ' (' + userid + ')')
    input('Press enter to display menu')
    menu()


def del_user():
    """Delete a user from the db"""
    userid = input('Enter UserID: ')
    if userid in db['users']:
        del db['users'][userid]
        db.sync()
        print('User ' + userid + ' deleted successfully ')
    else:
        print('Error: User not found')
    menu()

def change_pass():
    """Change the password of an exisitng user"""
    userid = input('Enter UserID: ')
    pswd = getpass('Enter current Password: ')

    if userid in db['users']:
        user = db['users'][userid]
        if user['pswd'] == pbkdf2_hmac(hash_name, pswd.encode(), user['salt'], hash_rounds):
            salt = urandom(parking_spaces + 1)
            new_pswd = getpass('Enter new Password: ')
            new_pswd_hash = pbkdf2_hmac(hash_name, new_pswd.encode(), salt, hash_rounds)
            user['salt'] = salt
            user['pswd'] = new_pswd_hash
            db['users'][userid] = user
            db.sync()
            print('Password of ' + ' changed successfully ')
        else:
            print('Error: Incorrect username or password')
    else:
        print('Error: Incorrect username or password')
    menu()

def save_and_exit():
    """Sync the database one last time and close it before exiting the program"""
    db.sync()
    db.close()
    exit

## All functions defined above, the program starts after here

## Initialise the db if it has not been initialised before. If users or students dictionary is not
## yet defined, set it as an empty dictionary
## If db['parking'] is not defined, create the two-dimenstional dictionary for it for each parking
## space in each level and set the status of it to available
if 'users' not in db:
    db['users'] = {}
if 'students' not in db:
    db['students'] = {}
if 'parking' not in db:
    db['parking'] = {}
    for level in range(1, parking_levels + 1):
        db['parking'][level] = {}
        for space in range(1, parking_spaces + 1):
            db['parking'][level][space] = {'status': 'available', 'studentid' : ''}
db.sync()
        
## if there are no resitered users allow a new user to be registered before showing the login screen
if len(db['users']) == 0:
    print('No existing users found, enter user details')
    new_user()
else:
    login()
