# Timecard Application
## This timecard application was developed for small/non-profit businesses to monitor and easily log clock ins and clock outs. The application is meant to run on a local computer (such as a RaspberryPi). You must set up a MongoDB.

### Setup
Clone the repository onto your computer.
`git clone https://github.com/cpkurotori/timecard`

Go to the repository
`cd [PATH-TO-DIRECTORY]/timecard`

Run pip to install requirements
`pip install -r requirements`

For the application to work, you must set up Environment Variabels `DB_NAME` and `DB_URI`. This is how Flask can communicate with your MongoDB.

I created a shell file to do this:

`### setup.sh
export DB_NAME=[database_name]
export DB_URI=mongodb://[username:password@]host1[:port1][,host2[:port2],...[,hostN[:portN]]][/[database_name][?options]]
python2 app.py
`

Then run the the program (or the shell file):
`python2 app.py`

The application works on Python 2.7


### Working example
For a working example got to https://timecard-cpk.herokuapp.com/

Here you can login with the following information:
*employee id # / password*
0438828/ck0438828
0438829/zo0438829

### Things to do
- Register Employee
- Admin Management