from aws_cdk import (
    Stack,
    Duration,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    aws_ssm as ssm,
    CfnTag
)
from constructs import Construct

class LoadBalancerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, props, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.security_group = ec2.SecurityGroup(self, "SecurityGroup",
                                                vpc=props['vpc'],
                                                allow_all_outbound=True,
                                                description=f"{props['stack_name']}/ECS/{props['service_name']}/SecurityGroup")
        self.security_group.add_ingress_rule(ec2.Peer.ipv4(props['cidr']), ec2.Port.tcp(80), "Allow from within the VPC for port 80")

        self.load_balancer = elbv2.CfnLoadBalancer(self, "LoadBalancer",
                                                   load_balancer_attributes=[
                                                       elbv2.CfnLoadBalancer.LoadBalancerAttributeProperty(
                                                           key="deletion_protection.enabled",
                                                           value="false"
                                                       )],
                                                   subnets=[props['subnet1'].subnet_id, props['subnet2'].subnet_id],
                                                   scheme="internal",
                                                   type="network",
                                                   tags=[CfnTag(
                                                       key="RetailDemoStoreServiceName",
                                                       value=props['service_name']
                                                   )])

        self.target_group = elbv2.CfnTargetGroup(self, "TargetGroup",
                                                 health_check_interval_seconds=10,
                                                 health_check_path="/",
                                                 health_check_protocol="HTTP",
                                                 health_check_timeout_seconds=5,
                                                 healthy_threshold_count=2,
                                                 matcher=elbv2.CfnTargetGroup.MatcherProperty(http_code="200-299"),
                                                 port=80,
                                                 protocol="TCP",
                                                 target_group_attributes=[
                                                     elbv2.CfnTargetGroup.TargetGroupAttributeProperty(
                                                         key="deregistration_delay.timeout_seconds",
                                                         value="30")
                                                 ],
                                                 target_type="ip",
                                                 vpc_id=props['vpc'].vpc_id)
        self.target_group.add_dependency(self.load_balancer)

        self.listener = elbv2.CfnListener(self, "LoadBalancerListener",
                                          default_actions=[elbv2.CfnListener.ActionProperty(
                                              type="forward",
                                              forward_config=elbv2.CfnListener.ForwardConfigProperty(
                                                  target_groups=[elbv2.CfnListener.TargetGroupTupleProperty(target_group_arn=self.target_group.attr_target_group_arn)]
                                              )
                                          )],
                                          load_balancer_arn=self.load_balancer.ref,
                                          port=80,
                                          protocol="TCP")

        self.service_url = f"https://{self.load_balancer.attr_dns_name}"
        ssm.StringParameter(self, "ServicesLoadBalancerSSMParameter",
                            parameter_name=f"/retaildemostore/services_load_balancers/{props['service_name']}",
                            string_value=self.service_url,
                            description=f"Load balancer URL for the Retail Demo Store {props['service_name']} service")
