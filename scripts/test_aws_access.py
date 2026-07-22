"""Quick AWS connectivity check for VaaniSeva services."""
import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

results = {}

# STS (Identity)
try:
    sts = boto3.client("sts", region_name=os.environ["AWS_REGION"])
    identity = sts.get_caller_identity()
    results["Identity"] = f"OK — Account: {identity['Account']} | ARN: {identity['Arn']}"
except Exception as e:
    results["Identity"] = f"FAILED: {e}"

# DynamoDB
try:
    db = boto3.client("dynamodb", region_name=os.environ["AWS_REGION"])
    tables = db.list_tables()["TableNames"]
    results["DynamoDB"] = f"OK — tables: {tables if tables else '(none)'}"
except Exception as e:
    results["DynamoDB"] = f"FAILED: {e}"

# S3
try:
    s3 = boto3.client("s3", region_name=os.environ["AWS_REGION"])
    buckets = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
    results["S3"] = f"OK — buckets: {buckets if buckets else '(none)'}"
except Exception as e:
    results["S3"] = f"FAILED: {e}"

# Bedrock list models
try:
    br = boto3.client("bedrock", region_name=os.environ["AWS_REGION"])
    models = br.list_foundation_models(byOutputModality="TEXT")["modelSummaries"]
    model_ids = [m["modelId"] for m in models[:3]]
    results["Bedrock (list models)"] = f"OK — sample: {model_ids}"
except Exception as e:
    results["Bedrock (list models)"] = f"FAILED: {e}"

# Bedrock Nova Micro inference
try:
    brt = boto3.client("bedrock-runtime", region_name=os.environ["AWS_REGION"])
    resp = brt.invoke_model(
        modelId=os.environ["BEDROCK_MODEL_ID"],
        body=json.dumps({"messages": [{"role": "user", "content": [{"text": "Say: test passed"}]}]}),
        contentType="application/json",
        accept="application/json",
    )
    out = json.loads(resp["body"].read())
    text = out["output"]["message"]["content"][0]["text"]
    results[f"Bedrock ({os.environ['BEDROCK_MODEL_ID']})"] = f"OK — '{text[:80]}'"
except Exception as e:
    results[f"Bedrock ({os.environ.get('BEDROCK_MODEL_ID','?')})"] = f"FAILED: {e}"

# Titan Embeddings
try:
    brt = boto3.client("bedrock-runtime", region_name=os.environ["AWS_REGION"])
    resp = brt.invoke_model(
        modelId=os.environ["BEDROCK_EMBEDDING_MODEL_ID"],
        body=json.dumps({"inputText": "test"}),
        contentType="application/json",
        accept="application/json",
    )
    out = json.loads(resp["body"].read())
    dims = len(out["embedding"])
    results[f"Bedrock ({os.environ['BEDROCK_EMBEDDING_MODEL_ID']})"] = f"OK — {dims} dimensions"
except Exception as e:
    results[f"Bedrock ({os.environ.get('BEDROCK_EMBEDDING_MODEL_ID','?')})"] = f"FAILED: {e}"

print("\n=== VaaniSeva AWS Access Check ===")
for svc, status in results.items():
    icon = "✅" if status.startswith("OK") else "❌"
    print(f"  {icon} {svc}: {status}")
print()
