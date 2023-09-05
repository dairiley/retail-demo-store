from aws_cdk import (
    Stack,
    Duration,
    aws_servicediscovery as cloudmap,
    aws_ec2 as ec2,
    Fn
)
from constructs import Construct

class ServiceDiscoveryStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        namespace = cloudmap.PrivateDnsNamespace(self, "test-ServiceDiscoveryNamespace",
                                                 vpc=props['vpc'],
                                                 name="retaildemostore.local",
                                                 description="Cloud Map private DNS namespace for resources for the Retail Demo Store")

        self.namespace_id = namespace.namespace_id
