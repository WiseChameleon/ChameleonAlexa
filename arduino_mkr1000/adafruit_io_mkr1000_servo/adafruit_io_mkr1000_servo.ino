#include "config.h"
#include <Servo.h>

// pin used to control the servo
#define SERVO_PIN 5
#define SERVO_STOP 90
#define SERVO_LEFT 180
#define SERVO_RIGHT 0

// create an instance of the servo class
Servo servo;
const int servoPin = 5;
const int button1Pin = 4;
const int button2Pin = 3;
int spd = 90;    // variable to store the servo speed
int old_buttonState1;
int old_buttonState2;

// set up the 'servo' feed
String servo_switch_feed;
String servo_pos_feed;
AdafruitIO_Feed *servo_switch;
AdafruitIO_Feed *servo_pos;

void setup() {
   // start the serial connection
  Serial.begin(115200);
  while(! Serial);

  servo_switch_feed = String(UUID) + "-servo";
  servo_pos_feed = String(UUID) + "-servo_pos";
  Serial.println(servo_switch_feed);
  Serial.println(servo_pos_feed);
  servo_switch = io.feed(servo_switch_feed.c_str());
  servo_pos = io.feed(servo_pos_feed.c_str());

  servo.attach(SERVO_PIN);
  pinMode(button1Pin, INPUT_PULLUP);
  pinMode(button2Pin, INPUT_PULLUP);
  old_buttonState1 = digitalRead(button1Pin);
  old_buttonState2 = digitalRead(button2Pin);
  servo.write(SERVO_STOP);

  // connect to io.adafruit.com
  Serial.print("Connecting to Adafruit IO");
  io.connect();
  servo_switch->onMessage(handleOnOff);
  servo_pos->onMessage(handlePos);

  // wait for a connection
  while(io.status() < AIO_CONNECTED) {
    //Serial.print(".");
    Serial.println(io.statusText());
    delay(500);
  }

  // we are connected
  Serial.println();
  Serial.println(io.statusText());

  //reset servo pos to 90
  servo_pos->save(SERVO_STOP);
  servo_switch->save("ON");
}


void loop() {

 int buttonState1;
 int buttonState2;
 buttonState1 = digitalRead(button1Pin);
 buttonState2 = digitalRead(button2Pin);

 if (buttonState1 == LOW) {
  Serial.println("button one pressed");
   spd = 180;
   servo.write(spd);
   delay(250);
   old_buttonState1 = buttonState1;
 }
 else if (buttonState2 == LOW) {
   Serial.println("button two pressed");
   spd = 0;
   servo.write(spd);
   delay(250);
   old_buttonState2 = buttonState2;
 }
 if (old_buttonState1 != buttonState1) {
  old_buttonState1 = buttonState1;
  servo.write(SERVO_STOP);
 }
 if (old_buttonState2 != buttonState2) {
  old_buttonState2 = buttonState2;
  servo.write(SERVO_STOP);
 }
  // io.run(); is required for all sketches.
  // it should always be present at the top of your loop
  // function. it keeps the client connected to
  // io.adafruit.com, and processes any incoming data.
  io.run();

}


void handleOnOff(AdafruitIO_Data *data) {

  char* on_off = data->toChar();
  Serial.println(on_off);
 

  if (strcmp(on_off, "ON") == 0)
    Serial.print("turned on");
  else if (strcmp(on_off, "OFF") == 0) {
    Serial.print("turned off");
    servo.write(SERVO_STOP);
    servo_pos->save(SERVO_STOP);
  }
  else if ((strncmp(on_off, "S", 1) == 0 ) || (strncmp(on_off, "T", 1) == 0)){
    //This is a command in the form S20:T2:S90 ...
    // where S sets the speed and T waits
    Serial.print("We got a command string");
    char *cmd;
    cmd = strtok (on_off,":");
    while (cmd != NULL) {
      if (strncmp(cmd, "S", 1) == 0 ) {
        //set speedk
        cmd++;
        int cmd_int = atoi(cmd);
        servo_pos->save(cmd_int);
        startServo(cmd_int);
      } else if (strncmp(cmd, "T", 1) == 0) {
        cmd++;
        int cmd_int = atoi(cmd) * 1000;
        delay(cmd_int);
      }
      cmd = strtok(NULL, ":");
    }
  }
}

void handlePos(AdafruitIO_Data *data) {

  // convert the data to integer
  int angle = data->toInt();

  startServo(angle);
}

void startServo(int angle) {
 
 // make sure we don't exceed the limit
  // of the servo. the range is from 0
  // to 180.
  if(angle < 0)
    angle = 0;
  else if(angle > 180)
    angle = 180;

  servo.write(angle);

}
