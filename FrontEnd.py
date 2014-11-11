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

#redirect_link='http://ec2-54-172-56-180.compute-1.amazonaws.com/redirect'
#c_id='1054097336369-epapeu21l22job328u6odukktj8krtho.apps.googleusercontent.com'
#c_sec="G33ZPGvT_HNHxEY0N24puYTq"
c_id='XXXXXXXXX'
c_sec='XXXXXXXXXXXXXXX'
redirect_link='XXXXXXXXXXXXXXXXXXXXXX'
JSon_Secret_path = 'Secret.json'

#declear a global history list for history keywords
history =[]
temp = ['']

history.append(temp)


@route('/')
def home():

	#home is just printing out the history table and a form using HTML form
	
	return_buffer = '''
				<html>
				<div style="position:   absolute;
    							top:20%;
    							right:0;
    							left:20%;">
				<img src = "Google_logo.png" rel="images" style="width:800px;height:300px;"/>
				</div>
			'''



	#check if the user is logged in
	s = bottle.request.environ.get('beaker.session')
	if 'email' not in s.keys():
	#if not logged in, give sign_in button
		return_buffer += '''
				<form action="/sign_in" method="get">
				<input type="image" src = "G_signin.png" rel="images" style = "width:180px;height:50px;" alt = 						"Submit"  ></input><br>
				</form>
				<div style="position:absolute;
						    top:50%;
						    right:0;
						    left:0;">

				<form name="Main_Form" action="/result" method="post" align="center"> <input name="keywords" 						type="text" style="width:650px;"/>
				<select name="myOptions" onchange="document.Main_Form.keywords.value=this.value">
				<option value="">Please Log In To See Your Top 10 Most Recent Words</option>
				</select>
				<input type="image"src = "Search_button.png" rel="images" style = "width:30px;height:30px" alt = 						"Submit"  > </form> 
				</div>
				''' 
	else:
	#if logged in, give sign_out button and the 10 recent words
		return_buffer += '''<form action="/sign_out" method="get">
				<input type="image" src = "G_signout.png" rel="images" style = "width:120px;height:50px" alt = 						"Submit"  ></input><br>
				</form>
				<p>WELCOME, %s</p>''' % s['email'] 

		return_buffer += '''	<div style="position:absolute;
							     top:50%;
							     right:0;
							     left:0;">

					<form name="Main_Form" action="/result" method="post" align="center"> <input name="keywords" 							type="text" style="width:650px;"/>
					<select name="myOptions" onchange="document.Main_Form.keywords.value=this.value">
					<option value="">Your Top 10 Most Recent Words</option>
				'''

		if history[0][0] != '':
	
		# change how to format the string to show 10 recent
			for k in range(len(history)):
				if s['email']  in history[k]:
					if s['email'] == history[k][0]:

						for j in range(len(history[k])):
							if j != 0:
								return_buffer +='''
											<option value="%s">%s</option>
										'''% (history[k][j],history[k][j])

						
				elif history[k] == history[-1]:
					print s['email'], history[k], history
					return_buffer += '''<p>You Have no Search History Yet, Try Searching Sommething!</p>'''
		else:
			return_buffer += '''<p>You Have no Search History Yet, Try Searching Sommething!</p>'''

		return_buffer += '''	</select>
					<input type="image" src = "Search_button.png" rel="images" style = "width:30px;height:30px" alt 						= "Submit"  > </form> 
					</div>'''
					
	#close with the html tage and return
	return_buffer += '''</html>'''
	return return_buffer




@route('/sign_in', method='GET') 
def sign_in():
	flow = flow_from_clientsecrets( JSon_Secret_path,
					scope='https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/userinfo.email',
					redirect_uri=redirect_link)
	url = flow.step1_get_authorize_url()
	bottle.redirect(str(url))




@route('/sign_out', method='GET') 
def sign_out():
	#invalidate the session
	s = bottle.request.environ.get('beaker.session')
	s.invalidate()
	bottle.redirect("/")	




@post('/result') # or @route('/result', method='POST') 
def result(): 
	#ready to update global variable
	global history
	return_buffer =''
	
	
	#BREAK THE INPUT INTO PIECES USING BUILT IN METHOD .split() AND APPEND IT TO A LIST
	broken_string = request.forms.get('keywords').split()
	result_list = []
	for word in broken_string:
		result_list.append(word)


	#CREATE A 2D LIST THAT STORES THE VALUE AND RETURN TO HTML
	#first converting list to set, then back to list to remove dups temporarily in order not to create dups records in the result 		table
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
		
		return_buffer += '''<form action="/sign_out" method="get">
				<input type="image" src = "G_signout.png" rel="images" style = "width:120px;height:50px" alt = 				"Submit"  ></input><br>
				</form>'''

		
		#Create the list to put into the history table
		#print result_table
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
						if len(history[his_i]) == 11:
							#print list_i
							del history[his_i][1]
							history[his_i].append(result_table[list_i][0])
						else:
							history[his_i].append(result_table[list_i][0])
					break
				elif history[his_i][0] != s.get('email') and history[his_i] == history[-1]:
					temp_list=['']
					temp_list[0]=s.get('email')
					for i in range (len(result_table)):
						if i >9:
							break
						temp_list.append(result_table[i][0])
					history.append(temp_list)
	
		#print history
	else:
		return_buffer += '''
				
				<form action="/sign_in" method="get">
				<input type="image" src = "G_signin.png" rel="images" style = 					"width:180px;height:50px;" alt = "Submit"  ></input><br>
				</form>'''
		
		

	#PREPARE BUFFER FOR RESULT USING THE DEEP COPIED RESULT TABLE
	return_buffer += '''
					<form action="/" method="get">
				<input type="image" src = "back.png" rel="images"style = "width:80px;height:80px;"   ></input><br>
				</form>

'''

	
	





	return_buffer += '''
<style type="text/css">
table.example3 {background-color:transparent;border-collapse:collapse;width:100%;}
table.example3 th, table.example3 td {text-align:center;border:1px solid black;padding:5px;}
table.example3 th {background-color:AntiqueWhite;}
table.example3 td:first-child {width:20%;}
</style>
<table id="results" class ="example3">
<tr>
<th colspan="2">Search Result BreakDown</th>
</tr>
<tr>
					<td>Words</td>
					<td>Count In Search String</td>
</tr>
'''
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
		bottle.redirect("/")

	#print 'here before flow.............'

	flow = OAuth2WebServerFlow( 	client_id= c_id,
					client_secret= c_sec,
					scope='https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/userinfo.email',
					redirect_uri= redirect_link)
	credentials = flow.step2_exchange(code)
	token = credentials.id_token['sub']
	#print 'here after flow'
	# Get user email
	http = httplib2.Http()
	http = credentials.authorize(http)
	users_service = build('oauth2', 'v2', http=http)
	user_document = users_service.userinfo().get().execute()
	user_email = user_document['email']

	
	#create a session
	s = bottle.request.environ.get('beaker.session')
	s['unique_user'] = s.id
	s['email'] = user_email
	s.save()
	#print s
	
	


	bottle.redirect("/")

	return return_buffer

@get('/<filename:re:.*\.(jpg|png|gif|ico)>')
def images(filename):
    return static_file(filename, root='img')

session_opts = {
	    'session.type': 'file',
	    'session.cookie_expires': 300,
	    'session.data_dir': './data',
	    'session.auto': True 
	}
app = SessionMiddleware(bottle.app(), session_opts)

run(host='0.0.0.0', port=80, debug=False,app=app)

