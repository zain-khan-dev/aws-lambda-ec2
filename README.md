# AWS Lambda EC2 Manage Function


## Project Description

Lambda function provided in this repo is used to manage the EC2 instances.
It queries EC2 instance from every region and checks for its state. 
If the EC2 instance is running it checks for the Name and Environment Tags. 
If any of the tags are missing it alerts the user through email using created_by tag as a recipent. 
It is assumed that the EC2 instance will always have a created_by tag. 
If after 6 hours have elapsed after sending an email to the user if tags are still missing. It informs the user that the EC2 is terminated through email and recepient email address from created_by tag and terminates the EC2 instance.

### Services Used
1. Lambda function
2. Event Bridge to scheudle lambda to run every hour
3. SES for sending email
4. EC2 instance to manage
5. DynamoDB to store the last emailed time for each instance id


## Steps to deploy

### Configuration
1. There are three defined parameters we can use to fine tune the 
    1. TABLE_NAME :- The name which will be used to store the last emailed time and instance_id
    2. HOUR_LIMIT :- Which defines the limit after each the EC2 instance will be discontinued
    3. TAGS_TO_SEARCH :- List of tags that should be fined on EC2 instance. If any of these tags are missing then EC2 instance is added to the watchlist

2. Define policy of the lambda function using Policy.json in the repository. This is used to provide lambda function to access other aws services

3. Add Event Bridge as trigger with rate(1 hour) :- This will run the job every hour

4. Deploy the lambda function with the given code.

5. Fine tune the configuration parameters according to the need.