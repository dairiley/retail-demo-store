from aws_cdk import (
    Stack,
    Duration,
    aws_servicediscovery as cloudmap
)
from constructs import Construct

class ServiceDiscoveryStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.name="retaildemostore.local"
        cloudmap.PrivateDnsNamespace(self, "test-ServiceDiscoveryNamespace",
                                     vpc=props['vpc'],
                                     name=self.name,
                                     description="Cloud Map private DNS namespace for resources for the Retail Demo Store")
