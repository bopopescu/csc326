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
import sqlite3 as lite




#declear a global history list for history keywords
history =[]
temp = ['']

history.append(temp)


@route('/')
def home():

	#home is just printing out the history table and a form using HTML form
	
	
	return_buffer = '''
				<html>
				<div style="position:absolute;
				    top:20%;
				    right:0;
				    left:20%;">
				<img src = "Google_logo.png" rel="images" style="width:800px;height:300px;"/>
				</div>
			'''



	#check if the user is logged in
	s = bottle.request.environ.get('beaker.session')
	print s
	#check to see if user is logged in
	if 'email' not in s.keys():
		return_buffer += '''
				
				<form action="/sign_in" method="get">
				<input type="image" src="G_signin.png" rel="images" style = 					"	     	width:180px;height:50px;
						position:absolute;
					    	top:3%;
					    	right:0;
					    	left:85%;" alt = "Submit"  ></input><br>
				</form>
				<div style="position:absolute;
					    top:50%;
					    right:0;
					    left:0;">
					<form name="Main_Form" action="/result" method="post" align="center"> <input name="keywords" 							type="text"style="width:650px;"/>
					<select name="myOptions" onchange="document.Main_Form.keywords.value=this.value">
					<option value="">Please Log In To See Your Top 10 Most Recent Words</option>
					</select>
					<input type="image" src = "Search_button.png" rel="images" style = "width:30px;height:30px;" alt = "Submit"  > </form> 
				</div>
				''' 
	else:
		return_buffer += '''<form action="/sign_out" method="get">
				<input type="image" src="G_signout.png" rel="images" style = "
						width:120px;height:50px;
						position:absolute;
					    	top:3%%;
					    	right:0;
					    	left:85%%;" alt = 						"Submit"  ></input><br>
				</form>
				<p style = "
						width:120px;height:50px;
						position:absolute;
					    	top:7%%;
					    	right:0;
					    	left:85%%;">WELCOME, %s</p>''' % s['email'] 



		return_buffer += '''<div style="position:absolute;
							 top:50%;
							 right:0;
							 left:0;">
					<form name="Main_Form" action="/result" method="post" align="center"> <input name="keywords" type="text" style="width:650px;"/>
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

		return_buffer += '''</select>
				   <input type="image" src = "Search_button.png" rel="images" style = "width:30px;height:30px" alt = "Submit"  > </form> 
				</div>'''
	

	return_buffer += '''</html>'''
	return return_buffer






@route('/sign_in', method='GET') 
def sign_in():
	flow = flow_from_clientsecrets("Secret.json",
					scope='https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/userinfo.email',
					redirect_uri="http://localhost:8080/redirect")
	url = flow.step1_get_authorize_url()
	bottle.redirect(str(url))






@route('/sign_out', method='GET') 
def sign_out():
	s = bottle.request.environ.get('beaker.session')
	s.invalidate()
	bottle.redirect("/")	






@post('/result') # or @route('/result', method='POST') 
def result(): 
	#ready to update global variable
	global history
	return_buffer = ''''''
	#use html get to get the keywords that user input, also check if the input is nothing or all spaces, if so, return none
	
	



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
	#write the logic for putting the 10 most recent into history table
	s = bottle.request.environ.get('beaker.session')
	if 'email' in s.keys():
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
						if len(history[his_i]) == 11:
							print list_i
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
	
		print history

	#PREPARE BUFFER FOR RESULT USING THE DEEP COPIED RESULT TABLE
	return_buffer += '''
				<form action="/" method="get">
				<input type="image" src = "Google_logo.png" rel="images"style = "width:170px;height:70px;position:relative;
					    	top:6%; "   ></input><br>
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

	
	word_id = []
	#GET WORD_ID FROM LEXICON TABLE

	con = lite.connect("dbFile.db")
	cur = con.cursor()
	cur.execute("SELECT wordid, docid, url, rank FROM Lexicon NATURAL JOIN inverted_index NATURAL JOIN DocId_url NATURAL JOIN PageRank WHERE word = '%s' ORDER BY rank DESC;" % (result_static[0][0]))
	word_id += cur.fetchall()
	print word_id 







	return_buffer += '''
				<table id="Lexicon" class ="example3">
				<tr>
				<th colspan="3">PageRank</th>
				</tr>
				<tr>
									<td>Word_id</td>
									<td>URL</td>
									<td>Score</td>
				</tr>
			'''

	for row in word_id:
		return_buffer +='''
				<tr>
					<td>%s</td>
					<td>%s</td>
					<td>%s</td>
				</tr>'''% (row[0], row[2], row[3])
	
	return_buffer += '''</table>'''




	s = bottle.request.environ.get('beaker.session')
	print s
	#check to see if user is logged in
	if 'email' not in s.keys():
		return_buffer += '''
					
					<div style="position:absolute;
						    top:3%;
						    right:0;
						    left:10%;">
						<form name="Main_Form" action="/result" method="post" align="center"> <input 								name="keywords" type="text"style="width:650px;"/>
						<select name="myOptions" onchange="document.Main_Form.keywords.value=this.value">
						<option value="">Please Log In To See Your Top 10 Most Recent Words</option>
						</select>
						<input type="image" src = "Search_button.png" rel="images" style = "width:30px;height:30px" 							alt = "Submit"  > </form> 
					</div>
					''' 
	else:
		return_buffer += '''

					<div style="position:absolute;
						    top:3%;
						    right:0;
						    left:10%;">
						<form name="Main_Form" action="/result" method="post" align="center"> <input 							name="keywords" type="text" style="width:650px;"/>
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

		return_buffer += '''</select>
				   <input type="image" src = "Search_button.png" rel="images" style = "width:30px;height:30px" alt = "Submit"  > </form> 
				</div>'''



	return return_buffer






@route('/redirect', method='GET') 
def redirect(): 
	#redirected page, this means the user has successfully signed in
	code = request.query.get('code', 'denied')
	if code == "denied":
		bottle.redirect("/")

	

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
	s['unique_user'] = s.id
	s['email'] = user_email
	s.save()
	print s

	bottle.redirect("/")

	return return_buffer


@error(404)
def custom404(error):
    return '''<html>


<body background="woody-404.jpg" rel="images" style = "background-size : 100% auto;">

				<div style="position:absolute;
				    top:70%;
				    right:0;
				    left:47%;">
				<form action="/" method="get">
				<input type="image" src = "back.png" rel="images" style = "width:80px;height:80px;"   ></input><br>
				</form></div></body>'''



@get('/<filename:re:.*\.(jpg|png|gif|ico)>')
def images(filename):
    return static_file(filename, root='img')

session_opts = {
	    'session.type': 'file',
	    'session.cookie_expires': 300,
	    'session.data_dir': './data',
	    'session.auto': False
	}
app = SessionMiddleware(bottle.app(), session_opts)

run(host='localhost', port=8080, debug=False,app=app)

