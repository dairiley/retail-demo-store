from aws_cdk import (
    Stack,
    aws_codecommit as codecommit
)
from constructs import Construct

class CodeCommitStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        if props['source_deployment_type'] == "CodeCommit":
            repo = codecommit.Repository(self, "SourceRepository",
                                  repository_name="retaildemostore-src",
                                  description="CodeCommit Repo for the Retail Demo Store source code")

            # Use escape hatch to add S3 code source as S3 is currently only supported by L1 constructs
            cfn_repo = repo.node.default_child
            cfn_repo.CodeProperty(
                s3=codecommit.CfnRepository.S3Property(
                    bucket=props['resource_bucket'],
                    key=f"{props['resource_bucket'].bucket_name}source/retaildemostore-source.zip"
                )
            )
