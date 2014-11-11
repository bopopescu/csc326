from bottle import *
import bottle as bottle 
import os
import sys
import string
import copy
import httplib2
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import flow_from_clientsecrets
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from beaker.middleware import SessionMiddleware
import beaker as beaker




#declear a global history list for history keywords
history =[]
temp = ['']

history.append(temp)


@route('/')
def home():

#home is just printing out the history table and a form using HTML form
	
	

	return_buffer = '''

<form action="/result" method="post" align="center"> Enter Keywords: <input name="keywords" type="text"/> <input 		value="Search" type="submit" /> </form> 

'''
	#check if the user is logged in
	s = bottle.request.environ.get('beaker.session')
	print s
	#TODO, check to see if user is logged in
	if 'email' not in s.keys():
		return_buffer += '''<form action="/sign_in" method="post">
				<button type="submit">Google+ Login</button><br>
				</form>''' 
	else:
		return_buffer += '''<form action="/sign_out" method="post">
				<button type="submit">Sign Out</button><br>
				</form>
				<p>WELCOME, %s</p>''' % s['email'] 

		if history[0][0] != '':
			return_buffer +='''<table id="history" align = "center" border="1">'''

	
		# change how to format the string to show 10 recent
			for k in range(len(history)):
				return_buffer +='''
						<tr>
						'''
				for j in range(len(history[k])):
					return_buffer +='''
							<td>%s</td>
							'''% history[k][j]

				return_buffer += '''</tr>'''

		return_buffer += '''</table>'''
	


	
	


	return_buffer += ''''''
	return return_buffer

@route('/sign_in', method='POST') # or @route('/result', method='POST')
def sign_in():
	flow = flow_from_clientsecrets("Secret.json",
					scope='https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/userinfo.email',
					redirect_uri="http://localhost:8080/redirect")
	url = flow.step1_get_authorize_url()
	bottle.redirect(str(url))

@route('/sign_out', method='POST') # or @route('/result', method='POST')
def sign_out():
	s = bottle.request.environ.get('beaker.session')
	s.delete()
	bottle.redirect("http://localhost:8080/")	

@post('/result') # or @route('/result', method='POST') 
def result(): 
	#ready to update global variable
	global history
	#use html get to get the keywords that user input, also check if the input is nothing or all spaces, if so, return none
	if request.forms.get('keywords') == '' or request.forms.get('keywords').isspace():
		return None
	
	#BREAK THE INPUT INTO PIECES USING BUILT IN METHOD .split() AND APPEND IT TO A LIST
	broken_string = request.forms.get('keywords').split()
	result_list = []
	for word in broken_string:
		result_list.append(word)


	#CREATE A 2D LIST THAT STORES THE VALUE AND RETURN TO HTML
	#first converting list to set, then back to list to remove dups temporarily in order not to create dups records in the result table
	result_table =[]
	result_set_tmp = set(result_list)
	result_set = sorted(list(result_set_tmp))
	
	for i in range (len(result_set)):
		new = []
		for j in (0, 2): 
			if j == 0 :
				new.append(result_set[i])
			else:
				new.append(result_list.count(result_set[i]))
		result_table.append(new)

	#TEMP_RESULT IS FINISHED, DEEP COPY IT TO AVOID ACCIENT MODIFICATION!
	result_static = copy.deepcopy(result_table)

	#See if the User is logged in, then use FIFO to put the most recent words in for the user
	#TODO, write the logic for putting the 10 most recent into history table
	s = bottle.request.environ.get('beaker.session')
	if 'email' in s.keys():
		example = [['tyler', '1' , 'A', 'C'], ['leo', 'A','B']]
		#Create the list to put into the history table
		print result_table
		if history[0][0] == '':
			history[0][0]= s.get('email')
			for i in range (len(result_table)):
				if i >9:
					break
				history[0].append(result_table[i][0])
		else:
			for his_i in range(len(history)):
				#print his_i
				if history[his_i][0] == s.get('email'):
					for list_i in range(len(result_table)):
						print list_i
						del history[his_i][1]
						history[his_i].append(result_table[list_i][0])
		
	
		print history

	#PREPARE BUFFER FOR RESULT USING THE DEEP COPIED RESULT TABLE
	return_buffer = '''<table id="results" align = "Center" border="1">'''
	for k in range(len(result_static)):
		return_buffer +='''
				<tr>
					<td>%s</td>
					<td>%d</td>
				</tr>'''% (result_static[k][0], result_static[k][1])

	return_buffer += '''</table>'''


	return return_buffer




@route('/redirect', method='GET') 
def redirect(): 

	

	#redirected page, this means the user has successfully signed in
	code = request.query.get('code', 'denied')
	if code == "denied":
		bottle.redirect("http://localhost:8080/")

	

	flow = OAuth2WebServerFlow( 	client_id="1054097336369-epapeu21l22job328u6odukktj8krtho.apps.googleusercontent.com",
					client_secret="G33ZPGvT_HNHxEY0N24puYTq",
					scope='https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/userinfo.email',
					redirect_uri="http://localhost:8080/redirect")
	credentials = flow.step2_exchange(code)
	token = credentials.id_token['sub']

	# Get user email
	http = httplib2.Http()
	http = credentials.authorize(http)
	users_service = build('oauth2', 'v2', http=http)
	user_document = users_service.userinfo().get().execute()
	user_email = user_document['email']
	
	#create a session
	s = bottle.request.environ.get('beaker.session')
	s['unique_user'] = code
	s['email'] = user_email
	s.save()
	print s
	
	


	bottle.redirect("http://localhost:8080/")

	return return_buffer



session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 300,
    'session.data_dir': './data',
    'session.auto': True
}
app = SessionMiddleware(bottle.app(), session_opts)
run(host='localhost', port=8080, debug=True,app=app)

