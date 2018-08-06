import requests
import sys
username=sys.argv[1]
password=sys.argv[2]
email=sys.argv[3]
payload = {'username': username, 'password': password,'email':email}
url = 'https://www.iphr.care/apps/exportRDFAvatar/start_auth'
resutl = requests.post(url, data=payload,verify=False)
text_file = open("/media/data/hatzimin/avatarResults/"+email+".txt", "w")
text_file.write("%s" % resutl.text)
text_file.close()
print resutl.text
