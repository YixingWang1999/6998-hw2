import math
import dateutil.parser
import datetime
import time
import os
import logging
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def get_slots(intent_request):
    return intent_request['currentIntent']['slots']
    
    
def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }
    return response


def search_photos(class_type):
    host = 'search-photos-kd5cnxlec3lynakr3v5amgh3gq.us-east-1.es.amazonaws.com'
    # path = 'photos'
    region = 'us-east-1'

    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

    client = OpenSearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = awsauth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )
        
    q = class_type
    query = {
      'query': {
        'match': {
          'labels': q
        }
      }
    }
    response = client.search(
        body = query,
        index = 'photos'
    )
    
    print('\nSearch results:')
    print(response)
    
    class_data = []
    for item in response['hits']['hits']:
        key, bucket = item['_source']['objectKey'], item['_source']['bucket']
        class_data.append((key, bucket))
    print(class_data)

def dispatch(intent_request):
    
    intent_name = intent_request['currentIntent']['name']
    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_name))
    
    if intent_name == 'SearchIntent':
        # print('currentIntent', intent_request['currentIntent'])
        class_type = get_slots(intent_request)['class']
        # class_type = intent_request['currentIntent']['slots']['class']
        print('class_type', class_type)
        
        search_photos(class_type)
        return close(intent_request['sessionAttributes'], 'Fulfilled',
                    {'contentType': 'PlainText',
                    'content': f'Thanks, your request for photos for {class_type} has been placed.'})
        # response = client.post_text(botName='photo',
        #                         botAlias='pt',
        #                         userId='testuser',
        #                         inputText=str(class_type))
        # print('response', response)
        # return class_type
    
# from botocore.exceptions import ClientError
# Define the client to interact with Lex
# client = boto3.client('lex-runtime')
def lambda_handler(event, context):
    

    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)

    # print(event)
    # try:
    #     response = client.post_text(botName='photo',
    #                             botAlias='pt',
    #                             userId='testuser',
    #                             inputText=str(class_type))
    #     print('response', response)
    # # except botocore.exceptions as e:
    # #     print('error', e.response['Error']['Message'])
    # except:
    #     print('error')
    # return class_type
    
    
# import boto3

# # Define the client to interact with Lex
# client = boto3.client('lex-runtime')


# def lambda_handler(event, context):
#     msg_from_user = event["messages"][0]["unstructured"]["text"]
#     print("msg_from_user is: ", msg_from_user)
#     response = client.post_text(botName='chatbot',
#                                 botAlias='chat',
#                                 userId='testuser',
#                                 inputText=msg_from_user)
    
    
#     print("response is: ", response)
#     intentName = response["intentName"]
#     print("intentName is: ", intentName)
#     msg_from_lex = response["message"]
#     print("response['message'] is: ", response['message'])
#     if msg_from_lex:
#         print(f"Message from Chatbot: {msg_from_lex}")
#         print("response is: ", response)

#         # modify resp to send back the next question Lex would ask from the user

#         # format resp in a way that is understood by the frontend
#         # HINT: refer to function insertMessage() in chat.js that you uploaded
#         # to the S3 bucket
#         resp = {"messages": [{"type": "unstructured", "unstructured": {"text": response['message']}}]}

#         return resp