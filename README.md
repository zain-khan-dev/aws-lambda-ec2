# AWS Lambda EC2 Manage Function


## Project Description

Lambda function provided in this repo is used to manage the EC2 instances.
It queries EC2 instance from every region and checks for its state. 
If the EC2 instance is running it checks for the Name and Environment Tags. 
If any of the tags are missing it alerts the user through email using created_by tag as a recipent. 
It is assumed that the EC2 instance will always have a created_by tag. 
If after 6 hours have elapsed after sending an email to the user if tags are still missing. It informs the user that the EC2 is terminated through email and recepient email address from created_by tag and terminates the EC2 instance.

## Steps to deploy