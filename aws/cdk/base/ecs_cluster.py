from aws_cdk import (
    Stack,
    Duration,
    aws_ecs as ecs
)
from constructs import Construct

class ECSClusterStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.cluster = ecs.Cluster(self, "Cluster",
                                   cluster_name=props['stack_name'],
                                   vpc=props['vpc'])
