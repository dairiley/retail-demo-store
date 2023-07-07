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
                                                description=f"{props['stack_name']}-alb")
        self.security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443))
        self.security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80))

        self.load_balancer = elbv2.CfnLoadBalancer(self, "LoadBalancer",
                                                   load_balancer_attributes=[
                                                       elbv2.CfnLoadBalancer.LoadBalancerAttributeProperty(
                                                           key="routing.http.drop_invalid_header_fields.enabled",
                                                           value="true"
                                                       )],
                                                   subnets=[props['subnet1'].subnet_id, props['subnet2'].subnet_id],
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
                                                 protocol="HTTP",
                                                 target_group_attributes=[
                                                     elbv2.CfnTargetGroup.TargetGroupAttributeProperty(
                                                         key="deregistration_delay.timeout_seconds",
                                                         value="30")
                                                 ],
                                                 target_type="ip",
                                                 vpc_id=props['vpc'].vpc_id)
        self.target_group.add_dependency(self.load_balancer)

        listener_http = elbv2.CfnListener(self, "LoadBalancerListener",
                                          default_actions=[elbv2.CfnListener.ActionProperty(
                                              type="forward",
                                              forward_config=elbv2.CfnListener.ForwardConfigProperty(
                                                  target_groups=[elbv2.CfnListener.TargetGroupTupleProperty(
                                                      target_group_arn=self.target_group.attr_target_group_arn,
                                                      weight=123
                                                  )]
                                              )
                                          )],
                                          load_balancer_arn=self.load_balancer.ref,
                                          port=80,
                                          protocol="HTTP")

        listener_https = elbv2.CfnListener(self, "LoadBalancerHTTPSListener",
                                           default_actions=[elbv2.CfnListener.ActionProperty(
                                               type="forward",
                                               forward_config=elbv2.CfnListener.ForwardConfigProperty(
                                                   target_groups=[elbv2.CfnListener.TargetGroupTupleProperty(
                                                       target_group_arn=self.target_group.attr_target_group_arn,
                                                       weight=123
                                                   )]
                                               )
                                           )],
                                           certificates=[elbv2.CfnListener.CertificateProperty(
                                               certificate_arn=props['acm_cert_arn']
                                           )],
                                           load_balancer_arn=self.load_balancer.ref,
                                           port=443,
                                           protocol="HTTPS")

        elbv2.CfnListenerRule(self, "ListenerRule",
                              listener_arn=listener_http.attr_listener_arn,
                              priority=2,
                              conditions=[elbv2.CfnListenerRule.RuleConditionProperty(
                                  field="path-pattern",
                                  values=["/"]
                              )],
                              actions=[elbv2.CfnListenerRule.ActionProperty(
                                  type="forward",
                                  target_group_arn=self.target_group.ref,
                              )])

        elbv2.CfnListenerRule(self, "ListenerHTTPSRule",
                              listener_arn=listener_https.attr_listener_arn,
                              priority=2,
                              conditions=[elbv2.CfnListenerRule.RuleConditionProperty(
                                  field="path-pattern",
                                  values=["/"]
                              )],
                              actions=[elbv2.CfnListenerRule.ActionProperty(
                                  type="forward",
                                  target_group_arn=self.target_group.ref,
                              )])

        self.service_url = f"http://{self.load_balancer.attr_dns_name}"
        ssm.StringParameter(self, "ServicesLoadBalancerSSMParameter",
                            parameter_name=f"/retaildemostore/services_load_balancers/{props['service_name']}",
                            string_value=self.service_url,
                            description=f"Load balancer URL for the Retail Demo Store {props['service_name']} service")
