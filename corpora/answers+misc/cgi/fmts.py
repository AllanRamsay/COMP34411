thanks = '''
<html>
<title>Thanks for Registering for Senseval!</title>
<body bgcolor="#ffffff">
<center>
<h1>Thanks for registering for Senseval!</h1>
</center>

Please check <A HREF="download.cgi">here</a> for your first
download of sample data at your convenience.
</html>
'''

form = '''
<html>
<head><title>Senseval II registration</title>
</head>
<body bgcolor="#ffffff">
%(error)s
<center><h2>Welcome to the Senseval-II Registration page.</h2></center>
<p>
Here, we ask you to inform us of a few things about yourself, choose a username and 
password, and sign up for a given task for the Senseval II word sense disambiguation
regatta.  Once the material becomes available and participants are ready, you can use
your username and password to access the necessary data for the task you choose, and
finally to upload your results.
<p>
All fields marked with (*) are required.  If you have any questions about how this
form works, please contact <A HREF="mailto:cotton@unagi.cis.upenn.edu">Scott Cotton</A>.
<p>
If you plan to participate in more than one task, please fill out this form for
each task you would like to participate in.
<p>
If you have any questions about the nature of the tasks at hand, or senseval itself, please
visit <A HREF="http://www.itri.bton.ac.uk/events/senseval/">The senseval homepage</A>
<p>


<center>
<hr width="70%%">
<form method="POST" action="http://www.cis.upenn.edu/~cotton/cgi-bin/senseval/register.cgi">

<table>
<tr>
    <td>(*) username</td><td><input type="text" size="10" name="username"></td>
</tr>
<tr>
    <td>(*) password</td><td><input type="password" name="password" size="10"></td>

</tr>
<tr>
    <td>(*) verify password</td><td><input type="password" name="password2" size="10"></td>
</tr>
<tr>
    <td>(*) email address</td>
    <td><input type="text" name="email" size="20"></td>
</tr>
<tr>
    <td>Organization</td>
    <td><input type="text" name="organization" size="20"></td>
</tr>
<tr>
    <td>(*) Task </td>
    <td>
        <select name="task">
           %(task_options)s
         </select>
    </td>
</tr>
<tr>
<td> Systems (comma separated)</td>
    <td>
        <input type="text" name="systems"></input>
     </td>
</tr>
<tr columns="1">
<td align="center"><input type="submit" value="Register"></input></td>
</tr>

</table>
</form>
'''

authenticate=''' <html> <head> <title>Senseval Login</title> <body
bgcolor="#ffffff"> <center> <h2>Senseval Login</h2> </center> This login
is for
senseval participants to retrieve or upload their data.  A
<a href="status.cgi">status page</a> shows
available data for each stage of each task. If you
need more information, please see <a href="register.cgi">the registration
page</a>.  If you Have problems or questions please mail <A
HREF="mailto:cotton@unagi.cis.upenn.edu">the maintainer of this program</A>.
<center>%(err)s</center>

<center>
<form action="%(auth_action)s" method="POST">
<hr width="68%%">
<table>
<tr>
<td>Username</td>
<td><input type="text" size="10" name="username"></input></td>
</tr>

<tr>
<td>Password</td>
<td><input type="password" size="10" name="password"></input></td>
</tr>
<tr>
<td colspan="2" align="middle">
<input type="submit" value="Login"></input>
</td>
</tr>
</table>
<hr width="68%%">
</form>
<p>

</center>



<p>

</body>

</html>
'''

stage_unavailable='''
<html>
<head>
<title>Senseval: Data Unavailable</title>
</head>
<center>
<h2>Error with Senseval Download: Data Unavailable</h2>
</center>
<hr>

We're sorry, the <b>%(stage)s</b> data for your task <b>%(task)s</b>
is not yet available.
Please try again in a few days or so.

<body bgcolor="#ffffff">
</body>
<html>
'''

stage_available='''
<html>
<head>
<title>Senseval: Data Download</title>
</head>
<body bgcolor="#ffffff">
<center>
<h2>Welcome to Downloading your senseval data!</h2>
<form action="download.cgi" method="POST">
<input type="hidden" name="user" value="%(user)s">
<input type="hidden" name="stage" value="%(stage)s">
<br>

<hr width="60%%">
<input type="submit" value="Download!"> <b>%(stage)s</b> data for the
<b>%(task)s</b> task.
<hr width="60%%">

</center>
</form>
</body>
 Questions? see <A HREF="http://www.itri.bton.ac.uk/events/senseval">
The Senseval homepage</A>
</html>
'''

timestamped_stage_available='''
<html>
<head>
<title>Senseval: Data Download</title>
</head>
<body bgcolor="#ffffff">
<center>
w<h2>Welcome to Downloading your senseval data!</h2>
<table>
<tr>
<td colspan="2">
When you download this data, we will record a timestamp indicating
that you have completed this action in order to help enforce the
time restraints of the Senseval Bake-off.  If you're certain you are
ready for this, please proceed.  If you'd like to know more about the
contest, please see <A HREF="http://www.itri.bton.ac.uk/events/senseval">
The Senseval homepage</A>
<p>
</td>
</tr>
<tr>
<td>
<form action="download.cgi" method="POST">
<input type="hidden" name="user" value="%(user)s">
<input type="hidden" name="stage" value="%(stage)s">
<p>
Are you ready to download the
<b>%(stage)s</b> data for the
<b>%(task)s</b> task?
</td>
<td>
<br>
<input type="submit" value="Download!">
</td>
</table>
</center>
</form>
</body>
</html>
'''

upload = '''
<html>
<head>
<title>Senseval: Task Answers Upload</title>
</head>
<body bgcolor="#ffffff">
<center>
<h2>
Upload your Senseval 2 answers here.
</h2>
</center>

%(err)s

Once you fill in the form below and submit it, your answers will
be uploaded and ready for scoring.  You are entitled to submit multiple 
sets of answers, but only one set per system.  If you upload multiple answers
per system, only the last one will be stored.
<br>
Thanks!

<center>
<form method="POST" enctype="multipart/form-data" action="upload.cgi">
<table>
<tr>
<td>Username</td>
<td><input type="text" name="username"></td>
</tr>

<tr>
<td>Password</td>
<td><input type="password" name="password"></td>
</tr>

<tr>
<td>File to upload</td>
<td><input type="file" name="answers"></td>
</tr>

<tr>
<td>System Name(optional)</td>
<td><input type="text" name="system"></td>
</tr>

<tr>
<td colspan=2 align="center">
<input type="submit" value="upload">
</td>
</tr>
</table>

</form>
<center>
<a href="http://www.sle.sharp.co.uk/senseval2">return to the senseval website</a>
</center>
'''

upload_thanks='''
<html>
<head>
<title> Thanks for your answers!</title>
</head>
<body bgcolor="#fffff">
<center>
<h2>Thanks for you participation in Senseval-2 !
</h2>
</center>
Your answers have been submitted.  We will process the answers and post or send the scores
to you as soon as possible.

</body>
</html>
'''
