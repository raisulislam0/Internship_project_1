Access Jenkins Dashboard

Navigate to your Jenkins dashboard.

Click New Item.

Enter an item name.

Select Pipeline as the item type.

Click OK.

NodeJS Setup

Navigate to your Jenkins dashboard.

Click Manage Jenkins

Click Tools

Scroll down and find NodeJS installations

Enter Name (The name should match with the tools name in the pipeline)



pipeline {
    agent any
    tools {
        nodejs 'NodeJs'  
    }
Select Version (NodeJS 22.13.1)

Apply and Save

Configure Triggers

Choose one of the following triggers:

Build when a change is pushed to Bitbucket

Poll SCM (set the schedule as needed) using cron schedule

Pipeline Definition

Choose Pipeline script or Pipeline script from SCM.

If using Pipeline script, copy and paste the contents of the Jenkinsfile.

If using Pipeline script from SCM, ensure the Jenkinsfile is located in the project root directory.

Modify the Checkout Stage in Jenkinsfile

Update the url, credentialsId, and branch in the checkout stage to match your project repository.

Modify CSP

Donwload Startup Trigger and Groovy Plugins

New Item > Freestyle project > Build Triggers (Build when job nodes start) > Build steps (Execute system Groovy script) > Groovy command and the following script.

 csp_resolution_script.txt 

Build the Item and Approve the script from Manage Jenkins > Script Approval

Ensure viewing apidoc index.html from artifacts



System.setProperty("hudson.model.DirectoryBrowserSupport.CSP", "default-src * 'unsafe-inline' 'unsafe-eval'; img-src * data:; style-src * 'unsafe-inline'; font-src * data:; connect-src *;")
println "CSP set to: ${System.getProperty('hudson.model.DirectoryBrowserSupport.CSP')}"
Generating API Documentation

When the Jenkins pipeline runs successfully:

The docs/docjs/ directory will contain apiDocJS-generated documentation. (can be modified)

_apidoc_generator.py generates _apidoc.js in the root dir which maintains different versions.

The index.html inside docs/docjs displays the documentation.

The apidoc.json file contains:

Project name

Version (automatically updated by _apidoc_generator.py)

Project description

Template for comparing different API versions

url and sample url for api testing

apidoc -i <src> -o <public-private> --private
apidoc -i <src> -o <private> 
