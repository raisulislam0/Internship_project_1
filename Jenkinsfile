pipeline {
    agent any

    tools {
        nodejs 'NodeJs'  
    }

    environment {
        PYTHON_CMD = 'python3' 
    }

    stages {
        stage('Checkout') {
            steps {
                git(
                    url: 'https://bitbucket.org/ftd-smm/intern.git',
                    credentialsId: 'bitbucket-creds', 
                    branch: 'apidoc2'
                )
            }
        }

        stage('Check and Install Dependencies') {
            steps {
                script {
                    def pythonInstalled = sh(script: 'which python3 || which python', returnStatus: true) == 0
                    if (!pythonInstalled) {
                        echo 'Python not found, installing Python...'
                        sh 'sudo apt update && sudo apt install -y python3'
                    } else {
                        echo 'Python is already installed'
                    }
                    
                    def pythonCmdCheck = sh(script: '''
                        if command -v python3 &> /dev/null; then
                            echo "python3"
                        elif command -v python &> /dev/null; then
                            echo "python"
                        else
                            echo "not_found"
                        fi
                    ''', returnStdout: true).trim()
                    
                    if (pythonCmdCheck == "not_found") {
                        error 'Unable to find Python executable even after installation'
                    }
                    
                    env.PYTHON_CMD = pythonCmdCheck
                    echo "Using Python command: ${env.PYTHON_CMD}"
                    
                    def apidocInstalled = sh(script: 'which apidoc', returnStatus: true) == 0
                    if (!apidocInstalled) {
                        echo 'apiDoc not found, installing apiDoc...'
                        sh 'npm install -g apidoc'
                    } else {
                        echo 'apiDoc is already installed'
                    }
                }
            }
        }

        stage('Conditional Execution and Version Processing') {
            steps {
                script {
                    sh '''
                        # Create destination directory if it doesn't exist
                        mkdir -p src_versions
                        
                        # Get only the most recent commit hash that affected the src/ directory
                        latestCommit=$(git log -n 1 --format="%H" -- src/)
                        
                        echo "Checking out latest commit: $latestCommit"
                        
                        # Checkout the 'src' directory from the latest commit
                        git checkout $latestCommit -- src/
                        
                        # Create destination folder
                        destination="src_versions/src_$latestCommit"
                        mkdir -p "$destination"
                        
                        # Copy all files from the 'src' directory to the destination
                        if [ -d "src" ]; then
                            # Copy only files directly in the src directory (not subdirectories)
                            find src -maxdepth 1 -type f -exec cp {} "$destination" \\;
                            
                            # Check if any files were copied
                            fileCount=$(find "$destination" -type f | wc -l)
                            echo "Total files copied: $fileCount"
                        else
                            echo "Error: src directory not found after checkout"
                        fi
                    '''
                    
                    sh "${env.PYTHON_CMD} _apidoc_generator.py -r"
                    
                    sh '''
                        if [ -d "src" ]; then rm -rf src; fi
                        if [ -d "src_versions" ]; then rm -rf src_versions; fi
                    '''
                }
            }
        }

        stage('Generate apiDoc Docs') {
            steps {
                sh 'apidoc -i . -f "_apidoc.js" -o docs/docjs'
            }
        }


        stage('Archive Docs') {
            steps {
                archiveArtifacts artifacts: 'docs/docjs/**', allowEmptyArchive: true
            }
        }
    }

    post {
        always {
            echo 'Pipeline completed and cleaning the workspace!'
        }
        success {
            echo 'RESTful API Docs generated successfully.'
        }
        failure {
            echo 'Pipeline failed. Check logs.'
        }
    }
}