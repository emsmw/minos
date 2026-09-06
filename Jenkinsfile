pipeline {
    agent { label 'python-agent' }
    stages {
        stage('Install deps') {
            steps {
                sh '''
                    cd scripts/container-service-alerts
                    pip install -r requirements.txt --break-system-packages
                    cd ../cpu-disk-mem-alerts
                    pip install -r requirements.txt --break-system-packages
                '''
            }
        }
        stage('Syntax check') {
            steps {
                sh '''
                    python3 -m py_compile scripts/container-service-alerts/check-container-status.py
                    python3 -m py_compile scripts/cpu-disk-mem-alerts/main.py
                '''
            }
        }
    }
}
