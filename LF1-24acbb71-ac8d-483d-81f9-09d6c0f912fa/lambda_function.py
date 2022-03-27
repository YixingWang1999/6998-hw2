import json
import urllib.parse
import boto3
# from RekognitionImage import usage_demo
from RekognitionImage import RekognitionImage
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
# print('Loading function')
import time
# print(time.time())


 
def lambda_handler(event, context):
    #print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    # usage_demo()
    s3 = boto3.client('s3')
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
     
    try:
        # response = s3.get_object(Bucket=bucket, Key=key)
        # print("CONTENT TYPE: " + response['ContentType'])
        rekognition_client = boto3.client('rekognition')
        detect_object = boto3.resource('s3').Object(bucket, key)
    
        detect_image = RekognitionImage.from_bucket(detect_object, rekognition_client)
        labels = detect_image.detect_labels()
        
        label_data = []
        for label in labels:
            label_data.append(str(label.to_dict()['name']))
        
        head_object = s3.head_object(Bucket=bucket, Key=key)
        print(head_object)
        meta_data = head_object['Metadata']
        if meta_data:
            custom_labels = meta_data['customlabels'].split(',')
            print(custom_labels)
            label_data.extend(custom_labels)
        
        label_data = [d.lower() for d in label_data]
        data_to_opensearch = {
            'objectKey': str(key),
            'bucket': str(bucket),
            'createdTimestamp': str(time.time()),
            'labels': label_data
        }
        print(data_to_opensearch)
        # return response['ContentType']
        host = 'search-photos-kd5cnxlec3lynakr3v5amgh3gq.us-east-1.es.amazonaws.com'
        # path = 'photos'
        region = 'us-east-1'
    
        service = 'es'
        credentials = boto3.Session().get_credentials()
        awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
        search = OpenSearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )
        search.index(index="photos", doc_type="_doc", id=data_to_opensearch['createdTimestamp'], body=data_to_opensearch)

        print(search.get(index="photos", doc_type="_doc", id=data_to_opensearch['createdTimestamp']))
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e
    
