#!/usr/bin/env bash
set -euo pipefail

if [[ "${CODEBUILD_BUILD_SUCCEEDING:-0}" != "1" ]]; then
  echo "Build did not succeed; deployment stopped."
  exit 1
fi

# Preflight BOTH targets before changing either function.
for function_name in "$INDEX_FUNCTION_NAME" "$SEARCH_FUNCTION_NAME"; do
  handler=$(aws lambda get-function-configuration --function-name "$function_name" --region "$DEPLOY_REGION" --query Handler --output text)
  if [[ "$handler" != "lambda_function.lambda_handler" ]]; then
    echo "Unexpected handler for $function_name; deployment stopped."
    exit 1
  fi
done

for function_name in "$INDEX_FUNCTION_NAME" "$SEARCH_FUNCTION_NAME"; do
  aws lambda wait function-updated-v2 --function-name "$function_name" --region "$DEPLOY_REGION"
done

aws lambda update-function-code --function-name "$INDEX_FUNCTION_NAME" --region "$DEPLOY_REGION" --zip-file fileb://dist/index-photos.zip --query '[FunctionName,LastUpdateStatus]' --output text
aws lambda wait function-updated-v2 --function-name "$INDEX_FUNCTION_NAME" --region "$DEPLOY_REGION"
aws lambda update-function-code --function-name "$SEARCH_FUNCTION_NAME" --region "$DEPLOY_REGION" --zip-file fileb://dist/search-photos.zip --query '[FunctionName,LastUpdateStatus]' --output text
aws lambda wait function-updated-v2 --function-name "$SEARCH_FUNCTION_NAME" --region "$DEPLOY_REGION"
echo "Both Lambda code updates completed."
