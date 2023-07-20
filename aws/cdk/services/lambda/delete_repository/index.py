import boto3


def handler(event, context):
    print(event)
    try:
        registryId = event['ResourceProperties']['RegistryId']
        repositoryName = event['ResourceProperties']['RepositoryName']

        if event['RequestType'] == 'Create':
            print("Repository creation succeeded")
        elif event['RequestType'] == 'Update':
            print("Repository update succeeded")
        elif event['RequestType'] == 'Delete':
            # Delete the registry
            ecr = boto3.client('ecr')
            ecr.delete_repository(
                registryId=registryId,
                repositoryName=repositoryName,
                force=True
            )
            print("Repository deletion succeeded")

    except Exception as e:
        print("Error: " + str(e))

    return {'RequestType': event['RequestType']}
