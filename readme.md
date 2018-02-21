### MOTIVATION/PERSPECTIVE

Let's do something cool about smart home!
Let's see if we can get it to a kick-startable level!

After some discussion on various topics, we pinned down the our starting project definition to (roughly)
**"Smart device controlled modular actuators"**

We would like to produce a ready-to-use device which will have a servo/motor head that can accept adapters (3D-printed or molded) and triggered by an app or smart hub.

This will leverage on couple of things, first the modularity that will be very exiting for growing makers community and 3d printer owners, and also the exponentially growing smart home market. This will be helpful in transforming non-smart devices (blinds) and also come up with new applications (iPlant/WaterMe) through various adapters.

#### Components
1) A board capable of
    - Running a motor/servo
    - WiFi communication with Alexa/Google/Smart Hub
    - Power management for handling battery/solar/dc Power
    -
2) Servo/motor
3) Power source
4) Use case defined attachments
5) website - ios/android app
6) Alexa skill / Google home integration

### INITIAL IMPLEMENTATION

We use arduino MKR1000 board connected to the `Adafruit.IO` device cloud.  And Alexa skills is developed as an AWS Lambda function that implements amazons Smart Home Skill Kit Inteface.  In particular it implements the PowerController and PowerLevelController as well as custom scenes.

Useful URLS:
* the lambda - https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/AlexaSmartHomeAPI_Chameleon?tab=graph
* cloudwatch logs, to debug alexa req / resp mss - https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logStream:group=/aws/lambda/AlexaSmartHomeAPI_Chameleon;streamFilter=typeLogStreamPrefix
* Amazon Developer Account (where lambda definition and publish abilities lie) - https://developer.amazon.com
* Page to Publish the skill - https://developer.amazon.com/edw/home.html#/skill/amzn1.ask.skill.69f8fca5-d0a9-41b2-824b-1dad7394dcb8/en_US/publishingInfo
* Adafruit.io the device cloud to control our arduinos - https://io.adafruit.com/chameleonwise/feeds
* Alexa Account for Skill Developer (Note mobile app provides more functionality) - https://alexa.amazon.com/spa/index.html#cards
* Test echo virtual device (just sign in as chameleon wise developer account) - https://echosim.io/
* Github repo - https://github.com/Softworks-Consultancy/hack_all_the_things.git

Useful documentation URLS:
* How Skill Kit Dev docs -https://developer.amazon.com/docs/smarthome/understand-the-smart-home-skill-api.htm://developer.amazon.com/docs/smarthome/understand-the-smart-home-skill-api.html
* custom scenes - https://developer.amazon.com/docs/smarthome/provide-scenes-in-a-smart-home-skill.html
* Adafruit.io (v2) REST API Docs - https://io.adafruit.com/api/docs/#section/Authentication  
* Adafruit IO tutorial (we use REST from lambda and MQTT from MKR1000) - https://learn.adafruit.com/adafruit-io-basics-servo



### TO-DO LIST

For the following 2 weeks, our task will be to do research on hardware/software that is already out and available. A second task can be to accumulate list of possible applications according to different power sources.

* solar
    - automated blinds
    - plant watering
    -
* battery
    - turn on/off the switch
    -
* dc
    - open the door
    - turn existing security cams (Andy)
    - Cat feeder (Andy)
