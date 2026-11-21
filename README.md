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

## CI/CD source repositories

These existing repositories remain the source for the working pipelines:

- Frontend: https://github.com/Saurabh-Mokashi/photo-album-frontend
- Backend: https://github.com/Saurabh-Mokashi/photo-album-backend

This submission repository consolidates their source into the required three-folder layout. It does not replace either pipeline source. Frontend CodeBuild runs from the front-end source root and needs PHOTO_API_KEY in its environment. Backend CodeBuild runs from the lambda-functions source root. See the component README files for build details. The CloudFormation template is located under other-scripts/cloudformation in this consolidated package.

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
