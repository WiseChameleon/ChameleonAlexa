import logging
import time
import json
import uuid
import requests
import os
import boto3

# super simple s3 store
from nodb import NoDB

# Imports for v3 validation
from validation import validate_message

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

MOTO_ENDPOINT = {
        "endpointId": "this needs to change for each device",
        "manufacturerName": "Chameleon Wise",
        "modelName": "/dev",
        "version": ".01",
        "friendlyName": "Moto",
        "description": "Smart motor that attaches and turns things",
        "displayCategories": [
                        "SWITCH"
                    ],
        "cookie": {
            "reserved": "for later use",
        },
        "capabilities": []
    }

MOTO_SCENES = [
   {
      "endpointId": "BlindsOpen",
      "manufacturerName": "Chameleon Wise",
      "friendlyName": "Open Blinds",
      "description": "Open blinds scene connected via dev servo",
      "displayCategories": ["SCENE_TRIGGER"],
      "cookie": {
      },
      "capabilities":
      [
        {
          "type": "AlexaInterface",
          "interface": "Alexa.SceneController",
          "version": "3",
          "supportsDeactivation": False,
          "proactivelyReported": True
        }
      ]
   },
   {
      "endpointId": "BlindsClose",
      "manufacturerName": "Chameleon Wise",
      "friendlyName": "Close Blinds",
      "description": "Close blinds scene connected via dev servo",
      "displayCategories": ["SCENE_TRIGGER"],
      "cookie": {
      },
      "capabilities":
      [
        {
          "type": "AlexaInterface",
          "interface": "Alexa.SceneController",
          "version": "3",
          "supportsDeactivation": False,
          "proactivelyReported": True
        }
      ]
   },
]


def lambda_handler(request, context):
    """Main Lambda handler.

    Since you can expect both v2 and v3 directives for a period of time during the migration
    and transition of your existing users, this main Lambda handler must be modified to support
    both v2 and v3 requests.
    """

    try:
        logger.info("Directive:")
        logger.info(json.dumps(request, indent=4, sort_keys=True))

        logger.info("Received v3 directive!")
        if request["directive"]["header"]["name"] == "Discover":
            logger.info("handle discovery_v3")
            response = handle_discovery_v3(request)
        else:
            logger.info("handle regular request _v3")
            response = handle_non_discovery_v3(request)

        logger.info("Response:")
        logger.info(json.dumps(response, indent=4, sort_keys=True))

        logger.info("Validate v3 response")
        validate_message(request, response)

        return response
    except ValueError as error:
        logger.error(error)
        raise


def get_utc_timestamp(seconds=None):
    return time.strftime("%Y-%m-%dT%H:%M:%S.00Z", time.gmtime(seconds))


def get_uuid():
    return str(uuid.uuid4())


def get_user_info_from_token(token):
    logging.info("verify token with amazon")
    from urllib.parse import quote_plus
    resp = requests.get("https://api.amazon.com/auth/o2/tokeninfo?access_token=" +
                        quote_plus(token))
    logging.info(resp)
    verify = resp.json()['aud']
    if verify != os.environ['CLIENT_ID']:
        logging.info("*********** invalid auth token %s" % verify)
        raise Exception("Invalid Token")

    # get user info
    headers = {'Authorization': 'bearer ' + token,
               'Content-Type': 'application/json'}
    user_info = requests.get('https://api.amazon.com/user/profile', headers=headers).json()

    # Save an object!
    store = NoDB()
    store.bucket = "chameleon-moto"
    store.serializer = 'json'
    store.index = "email"

    logger.info("about to query")
    user = store.load(user_info['email'])

    if not user:
        return None

    # update user info if not complete
    update = False
    if not user.get('name'):
        user['name'] = user_info['name']
        update = True
    if not user.get('amzn_userid'):
        user['amzn_userid'] = user_info['name']
        update = True
    print("********** about to store \n" + str(user))
    if update:
        store.save(user)  # True

    return user


# v3 handlers
def handle_discovery_v3(request):
    endpoints = []

    endpoint = MOTO_ENDPOINT.copy()
    endpoint["capabilities"] = get_capabilities()

    # get endpointID from the device from our database
    token = request['directive']['payload']['scope']['token']

    logger.info("******** token is %s" % token)
    # boto3.set_stream_logger(name='botocore')

    user = get_user_info_from_token(token)

    if user:
        # return endpoint to the users device so subsequent messages will be
        # directed to that device
        endpoint['endpointId'] = user['endpointid']
        endpoints.append(endpoint)

        # also add the scene
        for scene in MOTO_SCENES:
            endpoints.append(scene)

    else:
        logger.info("********* no user *********")

    response = {
        "event": {
            "header": {
                "namespace": "Alexa.Discovery",
                "name": "Discover.Response",
                "payloadVersion": "3",
                "messageId": get_uuid()
            },
            "payload": {
                "endpoints": endpoints
            }
        }
    }
    # TODO: add scene discovery here as well, so we can have scenes for
    # stuff like open blinds, etc..

    return response


def activate_scene(sceneId, token, time_as_string):
    user = get_user_info_from_token(token)
    endpoint = user['endpointid']
    scene_code = os.environ.get(sceneId)
    if scene_code is None:
        raise Exception("Unknown Scene")

    update_adafruit(endpoint, 'servo', scene_code, time_as_string)
    return endpoint


def get_stats_from_adafruit(endpointid):
    servo = make_af_request('feeds/%s-servo' % endpointid).json()
    pos = make_af_request('feeds/%s-servo-pos' % endpointid).json()
    power = servo.get('last_value')
    speed = pos.get('last_value')

    # if I got both values he's avaliable otherwise something
    # probably ain't right
    health = (power is not None and speed is not None)

    health_enum = ['ENDPOINT_UNREACHABLE', 'OK']

    res = {'power': power,
           'speed': int(speed),
           'health': health_enum[int(health)]}

    logger.info(str(res))
    return res


def update_adafruit(endpointId, feed_key, new_state, time_as_string):
    endpoint = 'feeds/' + endpointId + '-' + feed_key + '/data'
    data = {'value': new_state,
            'created_at': time_as_string
            }
    return make_af_request(endpoint, post=data)


def make_af_request(endpoint, post=None):
    headers = {'X-AIO-Key': os.environ.get("AIO_KEY"),
               'Content-Type': 'application/json'}
    url = "http://io.adafruit.com/api/v2/%s/" % os.environ.get("AIO_USER")

    if post:
        data = post
        return requests.post(url + endpoint, headers=headers, data=json.dumps(data))
    else:
        return requests.get(url + endpoint, headers=headers)


def get_event(request, namespace="Alexa", name="Response", endpointId=None):
    if endpointId is None:
        endpointId = request["directive"]["endpoint"]["endpointId"]
    return {
        "header": {
            "namespace": namespace,
            "name": name,
            "payloadVersion": "3",
            "messageId": get_uuid(),
            "correlationToken": request["directive"]["header"]["correlationToken"]
        },
        "endpoint": {
            "scope": {
                "type": "BearerToken",
                "token":  request['directive']['endpoint']['scope']['token']
            },
            "endpointId": endpointId
        },
        "payload": {}
      }


def handle_non_discovery_v3(request):
    '''
    This is main function that handles all the Alexa requests
    request are unique identified by namespace and name like
    '''
    request_namespace = request["directive"]["header"]["namespace"]
    request_name = request["directive"]["header"]["name"]
    endpointId = request["directive"]["endpoint"]["endpointId"]
    payload = request['directive']['payload']
    logger.info(request)
    uncertain = 200
    sample_time = get_utc_timestamp()

    # state request
    # TODO: this should like bearer-token to user account in our system
    # and thus the UUID on the ardunio which will translate into the 
    # endpointId as far as alexa is returned, and used to name
    # the queuse in adafruit so each device gets it's own queue
    # user NoDB to store that succer on s3
    if request_namespace == "Alexa.Authorization":
        if request_name == "AcceptGrant":
            response = {
                "event": {
                    "header": {
                        "namespace": "Alexa.Authorization",
                        "name": "AcceptGrant.Response",
                        "payloadVersion": "3",
                        "messageId": "5f8a426e-01e4-4cc9-8b79-65f8bd0fd8a4"
                    },
                    "payload": {}
                }
            }
            return response

    if request_namespace == "Alexa":
        if request_name == "ReportState":
            # got info about device from Adafruit.io
            stats = get_stats_from_adafruit(endpointId)
            health = stats['health']
            powerState = stats['power']
            powerLevel = stats['speed']

            response = {
              "context": {
                "properties": [
                    {"namespace": "Alexa.EndpointHealth",
                        "name": "connectivity",
                        "value": {
                            "value": health,
                        },
                        "timeOfSample": sample_time,
                        "uncertaintyInMilliseconds": uncertain
                     },
                    {
                        "namespace": "Alexa.PowerController",
                        "name": "powerState",
                        "value": powerState,
                        "timeOfSample":  sample_time,
                        "uncertaintyInMilliseconds": uncertain
                    },
                    {
                        "namespace": "Alexa.PowerLevelController",
                        "name": "powerLevel",
                        "value": powerLevel,
                        "timeOfSample": sample_time,
                        "uncertaintyInMilliseconds": uncertain
                    },
                ]
              },
              "event": get_event(request)
            }
        return response
    elif request_namespace == "Alexa.PowerController":
        if request_name == "TurnOn":
            state = 'ON'
            update_adafruit(endpointId, 'servo-pos', 180, sample_time)
        elif request_name == "TurnOff":
            state = 'OFF'
            update_adafruit(endpointId, 'servo-pos', 90, sample_time)
        response = {
            "context": {
                "properties": [
                    {
                        "namespace": "Alexa.PowerController",
                        "name": "powerState",
                        "value": state,
                        "timeOfSample": sample_time,
                        "uncertaintyInMilliseconds": uncertain
                    },
                    {
                        "namespace": "Alexa.EndpointHealth",
                        "name": "connectivity",
                        "value": {
                            "value": "OK"
                        },
                        "timeOfSample": sample_time,
                        "uncertaintyInMilliseconds": uncertain
                    }
                ]
            },
            "event": get_event(request)
        }

        return response
    elif request_namespace == "Alexa.PowerLevelController":
        if request_name == "SetPowerLevel":
            pwr_lvl = payload['powerLevel']
            update_adafruit(endpointId, 'servo-pos', pwr_lvl, sample_time)
            response = {
              "context": {
                "properties": [
                    {
                        "namespace": "Alexa.PowerLevelController",
                        "name": "powerLevel",
                        "value": pwr_lvl,
                        "timeOfSample": sample_time,
                        "uncertaintyInMilliseconds": uncertain
                    },
                    {
                        "namespace": "Alexa.EndpointHealth",
                        "name": "connectivity",
                        "value": {
                            "value": "OK"
                        },
                        "timeOfSample": sample_time,
                        "uncertaintyInMilliseconds": uncertain
                    }
                ]
              },
              "event": get_event(request)
            }

        return response
    elif request_namespace == "Alexa.SceneController":
        if request_name == "Activate":
            token = request['directive']['endpoint']['scope']['token']
            app_id = activate_scene(endpointId, token, sample_time)
            event = get_event(request, namespace='Alexa.SceneController',
                              name='ActivationStarted', endpointId=app_id)
            event['payload'] = {
                               "cause": {
                                    "type": "VOICE_INTERACTION"
                                  },
                               "timestamp": sample_time,
                                }

            return {
              "context": {},
              "event": event,
            }


# v3 utility functions
def get_endpoint_from_v2_appliance(appliance):
    endpoint = {
        "endpointId": appliance["applianceId"],
        "manufacturerName": appliance["manufacturerName"],
        "friendlyName": appliance["friendlyName"],
        "description": appliance["friendlyDescription"],
        "displayCategories": appliance['displayCategories'],
        "cookie": appliance["additionalApplianceDetails"],
        "capabilities": []
    }
    endpoint["capabilities"] = get_capabilities()
    return endpoint


def get_directive_version(request):
    try:
        return request["directive"]["header"]["payloadVersion"]
    except:
        try:
            return request["header"]["payloadVersion"]
        except:
            return "-1"


def get_capabilities():
    print("****** we got our capabilities")
    capabilities = [
        {
            "type": "AlexaInterface",
            "interface": "Alexa.PowerController",
            "version": "3",
            "properties": {
                "supported": [
                    {"name": "powerState"}
                ],
                "proactivelyReported": False,
                "retrievable": True
            }
        },
        {
            "type": "AlexaInterface",
            "interface": "Alexa.PowerLevelController",
            "version": "3",
            "properties": {
                "supported": [
                    {"name": "powerLevel"}
                ],
                "proactivelyReported": False,
                "retrievable": True
            }
        },
    ]

    # additional capabilities that are required for each endpoint
    endpoint_health_capability = {
        "type": "AlexaInterface",
        "interface": "Alexa.EndpointHealth",
        "version": "3",
        "properties": {
            "supported":[
                { "name":"connectivity" }
            ],
            "proactivelyReported": True,
            "retrievable": True
        }
    }
    alexa_interface_capability = {
        "type": "AlexaInterface",
        "interface": "Alexa",
        "version": "3"
    }
    capabilities.append(endpoint_health_capability)
    capabilities.append(alexa_interface_capability)
    return capabilities


if __name__ == "__main__":
    sample_time = get_utc_timestamp()
    # print(get_stats_from_adafruit(1))
    print(update_adafruit('test', 'servo-pos', 0, sample_time))
    time.sleep(.25)
    sample_time = get_utc_timestamp()
    print(update_adafruit('test', 'servo-pos', 90, sample_time))
