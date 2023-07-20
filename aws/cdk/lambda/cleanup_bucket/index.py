import boto3
import cfnresponse


def handler(event, context):
    print(event)

    responseData = {}
    responseStatus = cfnresponse.SUCCESS

    try:
        bucketName = event['ResourceProperties']['BucketName']

        if event['RequestType'] == 'Create':
            responseData['Message'] = "Resource creation succeeded"
        elif event['RequestType'] == 'Update':
            responseData['Message'] = "Resource update succeeded"
        elif event['RequestType'] == 'Delete':
            # Empty the S3 bucket
            s3 = boto3.resource('s3')
            bucket = s3.Bucket(bucketName)
            bucket.object_versions.delete()  # delete all versions of objects
            responseData['Message'] = "Resource deletion succeeded"

    except Exception as e:
        print("Error: " + str(e))
        responseStatus = cfnresponse.FAILED
        responseData['Message'] = "Resource {} failed: {}".format(event['RequestType'], e)

    cfnresponse.send(event, context, responseStatus, responseData)