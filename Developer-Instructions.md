# Developer Instructions

If you would like to contribute enhancements or features to the Retail Demo Store, please read on for instructions on how to develop and test your changes. Thanks for considering working with this project.

## Step 1: Fork this Repo

To submit changes for review, you will need to create a fork of the Retail Demo Store respository in your own GitHub account.

## Step 2: Create a GitHub Personal Access Token

Create a [GitHub Personal Access Token](https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line) in your GitHub account.

Make sure that your token has the "repo", "repo:status", and "admin:repo_hook" permission scopes.

Save your access token in a secure location.

## Step 3: Decide on Deployment Options

The Retail Demo Store provides several options for managing deployments.  Here are the most common ones:

### Option 3.1 Deploy via an S3 Staging Bucket

If you want to manage the whole deployment process yourself, you will need to configure an S3 bucket for staging Retail Demo Store resources prior to deployment in your own AWS account.  This bucket must be in the region in which you plan to deploy.

***These instructions only apply if you wish to stage your own Retail Demo Store deployment resources. These instructions are not necessary for the typical deployment scenarios described in the main [README](./README.md).***

The launch options described in the main [README](./README.md) use AWS CDK to deploy the stack and is designed to support deployments of what is in the upstream master branch. If you want to test changes to the stack or launch a custom variation of this project, you can do so by forking the repository and editing the cdk files located in `./aws/cdk`, and overriding the `resource_bucket` and `resource_bucket_relative_path` parameters in `./aws/cdk/cdk.json` to refer to your bucket and path. These parameters are used to load the resources from your bucket rather than the default shared bucket.

#### Bucket Region

Your staging bucket must be in the region in which you plan to deploy the Retail Demo Store.

#### Bucket Permissions

The default stage script requires the ability to set the resources it uploads to your bucket as public read.  Note that you do not need to set the bucket up to allow public listing of the resources in the bucket (this is not recommended).

If you plan to enable the automated Personalize campaign creation process at deployment time, you must allow access for Amazon Personalize to your bucket. Add the following bucket policy to your staging bucket.

```json
{
    "Version": "2012-10-17",
    "Id": "PersonalizeS3BucketAccessPolicy",
    "Statement": [
        {
            "Sid": "PersonalizeS3BucketAccessPolicy",
            "Effect": "Allow",
            "Principal": {
                "Service": "personalize.amazonaws.com"
            },
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::<your bucket name>",
                "arn:aws:s3:::<your bucket name>/*"
            ]
        }
    ]
}
```

#### Staging for Deployment

It is advisable to use a Python 3 virtual environment to do this and the scripts assume that the executable pip is the Python 3 version of pip so if necessary you may need to install pip into that virtual environment (if your system defaults to a Python 2 version of pip).

The [stage.sh](stage.sh) script at the root of the repository must be used to upload the deployment resources to your staging S3 bucket if you use this option. The shell uses the local AWS credentials to build and push resources to your custom bucket. 

Example on how to stage your project to a custom bucket and path (note the path is optional but, if specified, must end with '/'):

```bash
./stage.sh MY_CUSTOM_BUCKET S3_PATH/
```

### Option 3.2 Deploy Infrastructure from the Main Repo, Deploy Application and Services via GitHub

If you only want to modify the web user interface, or the Retail Demo Store backend services, you can deploy Retail Demo Store using the options below, and issue commits in your own fork via GitHub and trigger a re-deploy. This will allow you to push changes to the Retail Demo Store services and web user interface using a CodeDeploy pipeline.

To do that, configure your `cdk.json` to use `Github` as the deployment type. 

**All GitHub related template parameters are required.** Set `github_repo`, `github_branch`, `github_user` and optionally `github_token` and execute the below command from the cdk directory ([./aws/cdk]()) to deploy.
```bash
cdk deploy --all
```
*For additional information on deploying with CDK, refer to **Step 3** in the [README](./README.md).*

The CloudFormation deployment will take around 40 minutes to complete. If you chose to have the Amazon Personalize campaigns automatically built post-deployment, this process will take an additional 2-2.5 hours. This process happens in the background so you don't have to wait for it to complete before exploring the Retail Demo Store application and architecture. Once the Personalize campaigns are created, they will be automatically activated in the Web UI and Recommendations service. You can monitor the progress in CloudWatch under the `/aws/lambda/RetailDemoStorePersonalizePreCreateCampaigns` log group.
### Developing Services Locally

The Retail Demo Store also supports running the web user interface and backend services in a local container on your machine.  This may be a handy option while testing a fix or enhancement.

[Detailed instructions](./src) are available on how to get going with local development.  Note that you will still need to set up one of the development options described above, and have a working deployment in your AWS account as some of the services will need to access cloud-based services as part of deployment.

### Integration tests

Integration tests can be run on either

1. Local development (via Docker Compose)
2. Actual (deployed) AWS environment

You can find more information about the running the integration tests in `src/run-tests/README.md`.
