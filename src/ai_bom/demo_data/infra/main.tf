# AWS Bedrock Agent
resource "aws_bedrockagent_agent" "support_agent" {
  agent_name              = "customer-support"
  foundation_model        = "anthropic.claude-3-sonnet-20240229-v1:0"
  instruction             = "You are a helpful customer support agent."
  idle_session_ttl_in_seconds = 600
}

# SageMaker Endpoint for custom model
resource "aws_sagemaker_endpoint" "llm_endpoint" {
  name                 = "production-llm"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.llm_config.name
}

resource "aws_sagemaker_endpoint_configuration" "llm_config" {
  name = "production-llm-config"

  production_variants {
    variant_name           = "primary"
    model_name             = aws_sagemaker_model.llm_model.name
    initial_instance_count = 1
    instance_type          = "ml.g5.2xlarge"
  }
}

resource "aws_sagemaker_model" "llm_model" {
  name               = "custom-fine-tuned-llm"
  execution_role_arn = "arn:aws:iam::123456789012:role/SageMakerRole"

  primary_container {
    image          = "763104351884.dkr.ecr.us-east-1.amazonaws.com/huggingface-pytorch-inference:latest"
    model_data_url = "s3://my-bucket/models/fine-tuned-model.tar.gz"
  }
}
