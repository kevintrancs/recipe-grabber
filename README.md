# Recipe Builder
Ever find recipes online, but to lazy to write them down? Ever manually write/type 50+ grocery items on a *insert generic* notetaking app to find out you forgot a few ingrediants and now life is miserable?  
Ever actually go to the store, and forget to bring your note... or just can't read that 3rd grade chicken scratch hand writing? 
Well do I have a pseudo solution for you!
No longer are the days you come home after grocery shopping frustrated.
Just paste in a URL to your favorite online recipes and Recipe-Grabber will parse the link
and create a list of items you need, and send it to you in a text so you will always have it!

Built w/ React and Flask.

### Setup
Modify ./server/constants.json to your SMTP(gmail) account for sending text messages. 
```
{
    "smtp_email":"YOURGMAIL@GMAIL.COM",
    "smtp_pass":"PASSWORD"
}
```
NOTE: Free smtp gmail limits to around 150/daily SMS, please use Twilio or other SMS services for more messages, if someone knows a better way for free SMS hmu :)
Seems to drop messages depending on carrier, it is unreliable.

Start server:
```
cd server && python links.py
```
Open index.html

### Demo
<img src="https://j.gifs.com/rR1XQL.gif" />

### Todos:
- Dockerize and host on gitpages
- Allow saving list capabilities
- Expand food.txt for bigger collection
- Error handling