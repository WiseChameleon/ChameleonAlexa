Here be the AWS lambda code that Implements the Alexa Smart Home Skill API needed
for integration of Chameleon Wise's /dev device (alexa controlled servo).

Detailed info on the Smart Home Skill API is here:
https://developer.amazon.com/docs/smarthome/understand-the-smart-home-skill-api.html


Deployment:

```
$ cd AlexaSmarthomeAPI_Chameleon
$ pip install requests -t .
$ pip install nodb -t .
```

Now since our alexa skill is python3 and nodb doesn't support python3 make the following changes to `AlexaSmartHomeAPI_Chameleon/nodb/__init__.py`

line 69 ->  bytesIO.write(bytes(serialized, 'utf-8'))
line 241 ->             if index in obj:
line 264 ->             return self.hash_function(bytes(index_value, 'utf-8')).hexdigest()

once the file is modified you are read to deploy to lambda from `AlexaSmarthomeAPI_Chameleon` directory do:

```
$ zip -r python.zip .
```

This will zip everything up, then navigate to the lambda page:
https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions/AlexaSmartHomeAPI_Chameleon?tab=graph

Under `Function Code` select `Upload a Zip File` then select the `python.zip` file upload it and click save.  Now you can test it out.

There are three things to test
1.  Discovery...  navigate to `https://alexa.amazon.com/spa/index.html#appliances` login with 
the chameleonwise user
2.  Forget all device
3. Click discover
A device called moto should appear (if you are using the smart phone app, you will get a device controler for this guy that looks like a power switch).  Your now setup and ready to go

To test out the functionality use the following uterance

Alexa turn moto on
alexa turn moto off
alexa setup power level to 100 on moto

Debugging:

To check whats happening with the lambda, check out the `CloudWatch Logs`:

https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logStream:group=/aws/lambda/AlexaSmartHomeAPI_Chameleon


