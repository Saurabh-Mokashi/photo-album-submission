# Cloud Photo Album — Assignment 3

NYU Cloud Computing and Big Data Systems, Fall 2026.

## Submission layout

- `front-end/`: website, generated API Gateway JavaScript SDK, buildspec, and build script.
- `lambda-functions/`: index-photos and search-photos Lambda code, backend buildspec, packaging and deployment scripts.
- `other-scripts/cloudformation/`: CloudFormation template for the demonstration stack.
- `other-scripts/Submission-checklist.txt`: recording and submission checklist.

## Live application

Website: http://cc-s3-b1-36234.s3-website-us-east-1.amazonaws.com

API: https://s0khdyagpg.execute-api.us-east-1.amazonaws.com/test

Region: us-east-1. GET /search invokes the search Lambda; PUT /photos integrates directly with S3. Both require the same API key, supplied automatically by the deployed frontend. The generated public website contains that key; the repository contains only its build placeholder. Photo objects remain private and are displayed using presigned URLs.

## CI/CD source repository

Repository: https://github.com/Saurabh-Mokashi/photo-album-submission

Branch: main. Both pipelines should use this repository and branch as their source.

- Frontend CodeBuild project: photo-album-frontend-build. Buildspec: front-end/buildspec.yml. Keep PHOTO_API_KEY configured in the project environment. Artifact root: front-end/dist.
- Backend CodeBuild project: photo-album-backend-build. Buildspec: lambda-functions/buildspec.yml. Deploys code to index-photos and search-photos while preserving their configuration.
- P2 deploys BuildArtifact to cc-s3-b1-36234 with extraction enabled.
- CloudFormation template: other-scripts/cloudformation/photo-album.yaml.

Both buildspec files run from the repository root. For local frontend validation, set PHOTO_API_KEY in your environment, then run python3 front-end/scripts/build.py. For backend packaging, run python3 lambda-functions/scripts/build.py.

The earlier separate frontend/backend repositories are historical copies. Pipeline migration must be verified with a fresh main-branch push before claiming CI/CD uses this consolidated repository.

## Verification completed

- GitHub pushes automatically triggered both pipelines and deployed updates.
- A visible frontend wording change appeared on the live S3 website.
- Upload without custom labels and natural-language label search succeeded.
- Independent cat/dog searches, grouped cats-and-dogs search, custom label Milo, and no-result behavior were verified.
- Lex version 2 fixed extraction of the multiword label labrador retriever; the live alias was updated and the website query succeeded.
- CloudFormation created copies of both Lambdas, API Gateway, both buckets, and IAM resources; a template update changed both Lambda code blocks.

The main working application uses the original resources. The CloudFormation stack is an infrastructure demonstration; its frontend SDK uses the original API endpoint. A complete migration to the copied API is not claimed.

## Submission details

Add both team members’ names and NetIDs and the unlisted YouTube video URL to the release description and Brightspace submission. Follow the course submission guidelines. Do not include credentials or API key values in GitHub.
