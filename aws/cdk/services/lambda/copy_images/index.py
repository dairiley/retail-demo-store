import boto3


def handler(event, context):
    print(event)
    try:
        source_bucket_name = event['ResourceProperties']['SourceBucket']
        source_path = event['ResourceProperties']['SourceBucketPath']
        target_bucket_name = event['ResourceProperties']['TargetBucket']
        resource_bucket_path = event['ResourceProperties']['ResourceBucketRelativePath']

        if event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
            # Copy from source to target
            s3 = boto3.resource('s3')
            source_bucket = s3.Bucket(source_bucket_name)
            target_bucket = s3.Bucket(target_bucket_name)

            for obj in source_bucket.objects.filter(Prefix=source_path):
                source = {'Bucket': source_bucket_name, 'Key': obj.key}
                if len(resource_bucket_path) > 0:
                    # need to remove the resource_relative_path for the target images directory
                    target = target_bucket.Object(obj.key[len(resource_bucket_path):])
                else:
                    target = target_bucket.Object(obj.key)
                target.copy(source)

            print("Resource creation succeeded")
        elif event['RequestType'] == 'Delete':
            print("Resource deletion succeeded")

    except Exception as e:
        print("Error: " + str(e))

    return {'RequestType': event['RequestType']}
