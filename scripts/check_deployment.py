"""Check current VaaniSeva deployment state on AWS."""
import boto3
import os
from dotenv import load_dotenv

load_dotenv()
region = os.environ["AWS_REGION"]

# Check Lambda
lc = boto3.client("lambda", region_name=region)
try:
    fn = lc.get_function(FunctionName="vaaniseva-call-handler")
    cfg = fn["Configuration"]
    print("Lambda: EXISTS")
    print(f"  ARN    : {cfg['FunctionArn']}")
    print(f"  Runtime: {cfg['Runtime']}")
    print(f"  Status : {cfg['State']}")
    print(f"  Updated: {cfg['LastModified']}")
    lambda_exists = True
except lc.exceptions.ResourceNotFoundException:
    print("Lambda: NOT FOUND")
    lambda_exists = False

# Check API Gateway
apigw = boto3.client("apigateway", region_name=region)
apis = apigw.get_rest_apis()["items"]
existing = next((a for a in apis if a["name"] == "vaaniseva-api"), None)
if existing:
    api_id = existing["id"]
    base_url = f"https://{api_id}.execute-api.{region}.amazonaws.com/prod"
    print("API Gateway: EXISTS")
    print(f"  ID      : {api_id}")
    print(f"  Base URL: {base_url}")
    api_exists = True
else:
    print("API Gateway: NOT FOUND")
    base_url = None
    api_exists = False

# Check IAM role
iam = boto3.client("iam", region_name=region)
try:
    role = iam.get_role(RoleName="vaaniseva-lambda-role")
    print(f"IAM Role: EXISTS ({role['Role']['Arn']})")
    role_exists = True
except iam.exceptions.NoSuchEntityException:
    print("IAM Role: NOT FOUND — must create manually in IAM Console before deploying")
    role_exists = False

# Summary
print()
if lambda_exists and api_exists:
    print("==> READY TO MAKE A TEST CALL")
    print(f"    Run: python scripts/test_call.py +916232666180 {base_url}")
elif role_exists:
    print("==> Run deploy: python scripts/deploy.py")
else:
    print("==> Create IAM role 'vaaniseva-lambda-role' first, then run deploy.py")
