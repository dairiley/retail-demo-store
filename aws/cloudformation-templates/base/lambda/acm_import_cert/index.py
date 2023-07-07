import boto3
import cfnresponse
from botocore.exceptions import ClientError

response_data = {}

acm_client = boto3.client('acm')
ssm_client = boto3.client('ssm')


def handler(event, context):
    response_status = cfnresponse.SUCCESS
    acmarn_param_name = '/retaildemostore/acm-arn';

    try:

        if event['RequestType'] == 'Create':

            # Get Self-Signed Certificate from retail-demo-store-code S3 bucket.

            s3 = boto3.resource('s3')
            obj = s3.Object('retail-demo-store-code', 'keys/test.cert')
            certifictate_pem = obj.get()['Body'].read()

            obj = s3.Object('retail-demo-store-code', 'keys/test.key')
            private_key_pem = obj.get()['Body'].read()

            my_response = acm_client.import_certificate(
                Certificate=certifictate_pem,
                PrivateKey=private_key_pem,
                Tags=[
                    {
                        'Key': 'ACM',
                        'Value': 'retailDemoStore'
                    },
                ]
            )

            # Overwrite Certificate ARN value in SSM Parameter
            acmarn_parameter = ssm_client.put_parameter(
                Name=acmarn_param_name,
                Value=my_response['CertificateArn'],
                Type='String',
                Overwrite=True)

            response_data['certificate_arn'] = my_response['CertificateArn']
            response_data['Message'] = "Resource creation succeeded"
        elif event['RequestType'] == 'Update':
            response_data['Message'] = "Resource update succeeded"
        elif event['RequestType'] == 'Delete':
            # Delete the cert from ACM, assumes all attachments are already removed.

            # Retrieve ACM ARN from Parameter store
            acmarn_parameter = ssm_client.get_parameter(Name=acmarn_param_name)

            # Delete ACM
            my_response = acm_client.delete_certificate(
                CertificateArn=acmarn_parameter['Parameter']['Value']
            )

            response_data['Message'] = "Resource deletion succeeded"
    except ClientError as e:
        print("Error: " + str(e))
        response_status = cfnresponse.FAILED
        response_data['Message'] = "Resource {} failed: {}".format(event['RequestType'], e)
    cfnresponse.send(event, context, response_status, response_data)