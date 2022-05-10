$URLPROTOCOL = 'http';
$URLHOST = 'localhost';
$URLPORT = '8081';
$URLPROJECT = 'calendar_lab';
$TOKEN = 'part13';

$URL = "${URLPROTOCOL}://${URLHOST}:${URLPORT}/${URLPROJECT}";
$URL_TOKEN_STR = "${URLHOST}_${URLPORT}_${URLPROJECT}_-_${TOKEN}";
echo "$URL";


# login
C:\Users\friedrich\Downloads\curl-7.83.0-win64-mingw\bin\curl.exe -G "${URL}/special/login.html?zofar_token=${TOKEN}" --cookie-jar "cookie_${URL_TOKEN_STR}.txt"

# GET index
C:\Users\friedrich\Downloads\curl-7.83.0-win64-mingw\bin\curl.exe -G "${URL}/index.html" --cookie "cookie_${URL_TOKEN_STR}.txt"

# GET set_episode_data
C:\Users\friedrich\Downloads\curl-7.83.0-win64-mingw\bin\curl.exe -G "${URL}/set_episode_data.html" --cookie "cookie_${URL_TOKEN_STR}.txt"

# GET set_episode_data
C:\Users\friedrich\Downloads\curl-7.83.0-win64-mingw\bin\curl.exe -X POST "${URL}/set_episode_index.html" --cookie "cookie_${URL_TOKEN_STR}.txt" -H "Content-Type: application/x-www-form-urlencoded" -d "form=form&form%3Aset_episode_index%3Amqsc%3Aresponsedomain%3Aresponse%3Aoq=4&form%3AbtPanel%3Aforward%3AforwardBt=Weiter&javax.faces.ViewState=3115895413173022806%3A-7253142254580868967"
C:\Users\friedrich\Downloads\curl-7.83.0-win64-mingw\bin\curl.exe -G "${URL}/set_episode_index.html" --cookie "cookie_${URL_TOKEN_STR}.txt"
""" </div><input type="hidden" name="javax.faces.ViewState" id="j_id1:javax.faces.ViewState:0" value="-4517536138707100036:-1377909533976042332" autocomplete="off" />"""


C:\Users\friedrich\Downloads\curl-7.83.0-win64-mingw\bin\curl.exe -w "@C:\Users\friedrich\Downloads\curl-7.83.0-win64-mingw\curl-format.txt" -X POST "${URL}/set_episode_data.html" --cookie "cookie_${URL_TOKEN_STR}.txt" -H "Content-Type: application/x-www-form-urlencoded" #TODO: add generator for form data

C:\Users\friedrich\Downloads\curl-7.83.0-win64-mingw\bin\curl.exe -G "${URL}/j_spring_security_logout"

rm  "cookie_localhost_8081_calendar_lab_-_part5.txt"


