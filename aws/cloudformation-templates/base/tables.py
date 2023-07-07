from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb
)
from constructs import Construct

class TablesStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        """
        Products table
        """
        self.products_table = dynamodb.CfnTable(self, "ProductsTable",
                                                key_schema=[dynamodb.CfnTable.KeySchemaProperty(
                                                    attribute_name="id",
                                                    key_type="HASH"
                                                )],
                                                attribute_definitions=[
                                                    dynamodb.CfnTable.AttributeDefinitionProperty(
                                                        attribute_name="id",
                                                        attribute_type="S"
                                                    ),
                                                    dynamodb.CfnTable.AttributeDefinitionProperty(
                                                        attribute_name="category",
                                                        attribute_type="S"
                                                    ),
                                                    dynamodb.CfnTable.AttributeDefinitionProperty(
                                                        attribute_name="featured",
                                                        attribute_type="S"
                                                    )
                                                ],
                                                billing_mode="PAY_PER_REQUEST",
                                                global_secondary_indexes=[
                                                    dynamodb.CfnTable.GlobalSecondaryIndexProperty(
                                                        index_name="category-index",
                                                        key_schema=[dynamodb.CfnTable.KeySchemaProperty(
                                                            attribute_name="category",
                                                            key_type="HASH"
                                                        )],
                                                        projection=dynamodb.CfnTable.ProjectionProperty(
                                                            projection_type="ALL"
                                                      ),
                                                    ),
                                                    dynamodb.CfnTable.GlobalSecondaryIndexProperty(
                                                        index_name="featured-index",
                                                        key_schema=[dynamodb.CfnTable.KeySchemaProperty(
                                                            attribute_name="featured",
                                                            key_type="HASH"
                                                        )],
                                                        projection=dynamodb.CfnTable.ProjectionProperty(
                                                            projection_type="ALL"
                                                        )
                                                    )
                                                ])
        """
        Categories table
        """
        self.categories_table = dynamodb.CfnTable(self, "CategoriesTable",
                                                  key_schema=[dynamodb.CfnTable.KeySchemaProperty(
                                                     attribute_name="id",
                                                     key_type="HASH"
                                                  )],
                                                  attribute_definitions=[
                                                      dynamodb.CfnTable.AttributeDefinitionProperty(
                                                          attribute_name="id",
                                                          attribute_type="S"
                                                      ),
                                                      dynamodb.CfnTable.AttributeDefinitionProperty(
                                                          attribute_name="name",
                                                          attribute_type="S"
                                                      )
                                                  ],
                                                  billing_mode="PAY_PER_REQUEST",
                                                  global_secondary_indexes=[dynamodb.CfnTable.GlobalSecondaryIndexProperty(
                                                      index_name="name-index",
                                                      key_schema=[dynamodb.CfnTable.KeySchemaProperty(
                                                          attribute_name="name",
                                                          key_type="HASH"
                                                      )],
                                                      projection=dynamodb.CfnTable.ProjectionProperty(
                                                          projection_type="ALL"
                                                      ))
                                                  ])
        self.categories_table.add_dependency(self.products_table)

        """
        Experiment strategy table
        """
        self.experiment_strategy_table = dynamodb.CfnTable(self, "ExperimentStrategyTable",
                                                           key_schema=[dynamodb.CfnTable.KeySchemaProperty(
                                                               attribute_name="id",
                                                               key_type="HASH"
                                                            )],
                                                           attribute_definitions=[
                                                               dynamodb.CfnTable.AttributeDefinitionProperty(
                                                                   attribute_name="id",
                                                                   attribute_type="S"
                                                               ),
                                                               dynamodb.CfnTable.AttributeDefinitionProperty(
                                                                   attribute_name="feature",
                                                                   attribute_type="S"
                                                               ),
                                                               dynamodb.CfnTable.AttributeDefinitionProperty(
                                                                   attribute_name="name",
                                                                   attribute_type="S"
                                                               )
                                                           ],
                                                           billing_mode="PAY_PER_REQUEST",
                                                           global_secondary_indexes=[dynamodb.CfnTable.GlobalSecondaryIndexProperty(
                                                               index_name="feature-name-index",
                                                               key_schema=[
                                                                   dynamodb.CfnTable.KeySchemaProperty(
                                                                       attribute_name="feature",
                                                                       key_type="HASH"
                                                                   ),
                                                                   dynamodb.CfnTable.KeySchemaProperty(
                                                                       attribute_name="name",
                                                                       key_type="RANGE"
                                                                   ),
                                                               ],
                                                               projection=dynamodb.CfnTable.ProjectionProperty(
                                                                   projection_type="ALL"
                                                               ))
                                                           ])
        self.experiment_strategy_table.add_dependency(self.products_table)






