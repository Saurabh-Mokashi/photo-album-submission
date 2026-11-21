# Photo album backend

Cloud Computing and Big Data Systems, Assignment 3.

## Source

- `index-photos/lambda_function.py`: S3 PUT event handler; Rekognition labels and custom S3 metadata are indexed in Elasticsearch.
- `search-photos/lambda_function.py`: Lex keyword extraction, Elasticsearch label search, and presigned S3 image URLs.
- `buildspec.yml`: AWS CodeBuild specification used by the backend CodePipeline.
- `scripts/build.py`: syntax-checks both functions and creates flat ZIP deployment packages.
- `scripts/deploy.sh`: deploys both ZIPs and waits for both Lambda updates to succeed.
- `infrastructure/photo-album.yaml`: separately tested CloudFormation demonstration stack.

## Build locally

Run `python3 scripts/build.py` from the repository root. This creates `dist/index-photos.zip` and `dist/search-photos.zip` without calling AWS. The handler in both packages is `lambda_function.lambda_handler`.

## Deployment targets

The pipeline deploys to the EXISTING working functions `index-photos` and `search-photos` in `us-east-1`, not the separate CloudFormation demonstration functions. CodeBuild requires an AWS managed image supporting Python 3.12 and AWS CLI v2, and a role with Lambda GetFunction, GetFunctionConfiguration, and UpdateFunctionCode permissions on both functions, plus build logging and pipeline artifact-bucket permissions.

Configure CodePipeline with GitHub connection source for this repository's `main` branch, automatic push triggers, and one CodeBuild action reading the root buildspec. Use queued execution to avoid simultaneous updates. The CodeBuild action both builds and deploys; a separate Lambda deployment action is unnecessary. Successful deployments wait for each function's LastUpdateStatus to be Successful. Deployment is sequential and not transactional; if the second update fails, the first can already be deployed. Correct the failure and rerun, or redeploy a previously known-good commit.

Code-only updates keep existing Lambda settings, IAM roles, handlers, environment variables, and layers. The search function needs the existing Python 3.12/x86_64 `photo-search-dependencies:1` layer with elasticsearch and requests-aws4auth dependencies. The indexing function uses the AWS-provided boto3/botocore runtime libraries. Do not remove the search layer or put credentials or the API key in the repository.

## Existing runtime configuration

Both functions require ES_ENDPOINT. Search also requires LEX_BOT_ID, LEX_ALIAS_ID, and PHOTO_BUCKET. Existing service permissions and S3 notifications remain configured in AWS.

## Smoke checks after a pipeline run

1. Confirm the pipeline source commit matches the pushed commit and CodeBuild succeeds.
2. Confirm both functions' code and last-modified timestamps changed.
3. Open the existing frontend at http://cc-s3-b1-36234.s3-website-us-east-1.amazonaws.com and enter the API key locally.
4. Search for `show me cats` and verify image results.
5. Upload a JPEG or PNG with a fresh custom label and search for it after indexing.
6. Check an unmatched query returns no photos and a two-keyword query returns matching photos.
7. Also test an upload without custom labels and search using a Rekognition label.

For trigger evidence, add a harmless version comment to BOTH Lambda source files, commit and push, and verify automatic deployment plus the comments in both functions. Local syntax/package checks do not test live Lex, Elasticsearch, S3, or AWS permissions.

## CloudFormation

The included template creates a separate demonstration stack with two buckets, two Lambda functions, API Gateway, IAM, and a frontend URL output. It reuses the existing Lex, Elasticsearch domain, and dependency layer. Inline code uses `index.lambda_handler` because CloudFormation names inline Python source `index.py`. Supply the layer version ARN as a parameter. Upload frontend files to the new frontend bucket after creation. The working app does not need to be recreated through this stack. Stack creation, public website hosting, and updates to both inline Lambda sources have been verified in the console.
