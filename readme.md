### MOTIVATION/PERSPECTIVE

Let's do something cool about smart home!
Let's see if we can get it to a kick-startable level!

After some discussion on various topics, we pinned down the our starting project definition to
**"Smart device controlled modular actuators"**

We would like to produce a ready-to-use device which will have a servo/motor head that can accept adapters (3D-printed or molded) and triggered by an app or smart hub.

This will leverage on couple of things, first the modularity that will be very exiting for growing makers community and 3d printer owners, and also the growing smart home DIY electronics. This will be helpful in transforming non-smart devices (blinds, etc) and also come up with new applications (Watering Plants) through various adapters.

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
6) Alexa skill integration

### INITIAL IMPLEMENTATION

We use arduino MKR1000 board connected to the `Adafruit.IO` device cloud.  And Alexa skills is developed as an AWS Lambda function that implements amazons Smart Home Skill Kit Inteface.  In particular it implements the PowerController and PowerLevelController as well as custom scenes.

Used components:
* AWS lambda -
* cloudwatch logs, to debug alexa req / resp mss
* Amazon Developer Account (where lambda definition and publish abilities lie) -
* Adafruit.io the device cloud to control our arduinos
* Test echo virtual device (just sign in as chameleon wise developer account) - https://echosim.io/

Useful documentation URLS:
* How Skill Kit Dev docs -https://developer.amazon.com/docs/smarthome/understand-the-smart-home-skill-api.htm://developer.amazon.com/docs/smarthome/understand-the-smart-home-skill-api.html
* custom scenes - https://developer.amazon.com/docs/smarthome/provide-scenes-in-a-smart-home-skill.html
* Adafruit.io (v2) REST API Docs - https://io.adafruit.com/api/docs/#section/Authentication  
* Adafruit IO tutorial (we use REST from lambda and MQTT from MKR1000) - https://learn.adafruit.com/adafruit-io-basics-servo
