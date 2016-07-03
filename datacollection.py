#import the necessary modules

from twython import Twython

import RPi.GPIO as GPIO #for DHT22 and LEDs
import time,datetime
import MySQLdb #Database
import pigpio #for DHT22
import DHT22 #temp/humidity
import Adafruit_BMP.BMP085 as BMP085 #temp/pressure
from picamera import PiCamera #PiCamera (duh!)

#Enable Functions
enable_tweets = 0
enable_photos = 0
enable_db = 1
enable_readings = 1

#setup the various modules

#GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(21,GPIO.OUT)
GPIO.setup(23,GPIO.OUT)

#PiCamera
camera = PiCamera()
camera.rotation = 180
img_root = ("/var/www/html/imgs/")
img_name = ("")

#Twitter API Access
APP_KEY = 'ixpQnJKQk42fpoFOWECns6rUJ'
APP_SECRET = 'Jr1Gt8VWZAHXHpE4SkGqsuGGLIenajxAJqCsETN7jzOIzoHYqn'
OAUTH_TOKEN='746829970958352384-ojCbCYb2iLGUMFbUEqV7WfdNYRNEBF6'
OAUTH_TOKEN_SECRET='YtDYC2ztRVwCmVJ1mUT5liBjE6dHibnE8CWwlI9kjH9US'
twitter =  Twython(APP_KEY,APP_SECRET,OAUTH_TOKEN,OAUTH_TOKEN_SECRET)

#DB Connection
dbserver = "localhost"
dbuser = "weatherstn"
dbpw = "22murraysbrae!"
dbname = "weather"
dbtable = "data"

conn = MySQLdb.connect(host = dbserver,user = dbuser,passwd = dbpw,db = dbname)
x = conn.cursor()

#Setup Temp & Humidity Sensor (DHT22)
pi = pigpio.pi()
dht22 = DHT22.sensor(pi,12) #sensor on GPIO pin 12
dht22.trigger()
sleepTime = 3

#Define Function to trigger DHT22
def ReadDHT22():
        print ("Reading DHT22")
        #Get new Reading
        dht22.trigger()
        #Save values
        dht_humidity = '%.2f' % (dht22.humidity())
        dht_temperature = '%.2f' % (dht22.temperature())
        return (dht_humidity,dht_temperature)

#Setup Temp & Pressure sensor (BMP085)
bmp_sensor = BMP085.BMP085()

#Definte Function to read from BMP085
def ReadBMP085():
        print ('Reading BMP085')
        bmp_pressure = (bmp_sensor.read_pressure()*0.01) #reads pressure and converts from pa to HPa
        bmp_temperature = bmp_sensor.read_temperature()
        return(bmp_pressure,bmp_temperature)

#Get sensor information

#Read DHT (Temperature & humidity)
dht_humidity,dht_temperature = ReadDHT22()

while dht_temperature == '-999.00' or dht_humidity == '-999.00':
        time.sleep(sleepTime)
        print ("Waiting on DHT reading")
        dht_humidity,dht_temperature = ReadDHT22()

bmp_pressure,bmp_temperature = ReadBMP085()

#Collection Timestamp
db_time = time.time()
db_time_str = str(db_time)
friendly_time=datetime.datetime.fromtimestamp(db_time).strftime('%Y-%m-%d %H:%M:%S')
friendly_time_str = str(friendly_time)

#Capture photo from PiCamera
img_path = img_root+db_time_str+".jpg"
if enable_photos == 1:
        img_name = (db_time_str+".jpg")
        print ("Starting image capture")
        print ("Image path will be: "+img_path)
        camera.start_preview()
        time.sleep(5)
        camera.capture(img_path)
        camera.stop_preview()
        print ("Image capture complete")
        photo = open(img_path, 'rb')
else:
        print "***Photos disabled***"

#Post Photo to Twitter
if enable_tweets == 1:
        print ("Uploading Photo to Twitter...")
        media_status = twitter.upload_media(media=photo)
#Tweet Current Conditions
dht_temperature=str(dht_temperature)
dht_humidity=str(dht_humidity)
bmp_temperature=str(bmp_temperature)
bmp_pressure=str(bmp_pressure)

if enable_readings ==1:
        print ("Humidity: "+dht_humidity+"%")
        print ("Temperature: "+bmp_temperature+"C")
        print ("Pressure: "+bmp_pressure+"mb")
else:
        print "***Readings Display Disabled***"

if enable_tweets == 1:
        tweet_message = "CURRENT CONDITIONS:"+friendly_time_str+". Temp: "+bmp_temperature+"C. Pressure: "+bmp_pressure+"mb. Humidity: "+dht_humidity+"% #edinburgh #weather"
        twitter.update_status(media_ids=[media_status['media_id']],status=tweet_message)
        tweet_media_id = str([media_status['media_id']])
        print "Tweet sent"
else:
        print "***Tweets Disabled***"
#Insert Data into DB

if enable_db == 1:
        sqlcmd = "INSERT INTO `"+dbtable+"` (`id`,`timestamp`,`temp`,`humidity`,`pressure`,`image`) VALUES (NULL,\'"+db_time_str+"\',\""+bmp_temperature+"\",\""+dht_humidity+"\",\""+bmp_pressure+"\",\""+img_name+"\");"
        print sqlcmd
        x.execute(sqlcmd)
        conn.commit()
        conn.close()
        print "SQL insert complete"
else:
        print "***Database Activity Disabled***"
GPIO.cleanup()

