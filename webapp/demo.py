from subprocess import Popen, PIPE
user="-u"+"root"
passWord="-p"+"password"

filepath = "/Users/Adhira/Desktop/From desktop/Cloud/Assignment1/csye6225/dev/ccwebapp/webapp/createScripts.sql"

process = Popen(['mysql', user, passWord," < ", filepath],
                stdout=PIPE, stdin=PIPE)
#output = process.communicate('<' + filepath)[0]
#print("output is: ", output)
