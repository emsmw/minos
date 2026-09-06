pipeline {
    agent { label 'python-agent' }
    stages {
        stage('Container Alerts: Install deps') {
            when { changeset "scripts/container-service-alerts/**" }
            steps {
                sh '''
                    cd scripts/container-service-alerts
                    pip install -r requirements.txt --break-system-packages
                '''
            }
        }
        stage('Container Alerts: Syntax check') {
            when { changeset "scripts/container-service-alerts/**" }
            steps {
                sh 'python3 -m py_compile scripts/container-service-alerts/check-container-status.py'
            }
        }
        stage('Resource Alerts: Install deps') {
            when { changeset "scripts/cpu-disk-mem-alerts/**" }
            steps {
                sh '''
                    cd scripts/cpu-disk-mem-alerts
                    pip install -r requirements.txt --break-system-packages
                '''
            }
        }
        stage('Resource Alerts: Syntax check') {
            when { changeset "scripts/cpu-disk-mem-alerts/**" }
            steps {
                sh 'python3 -m py_compile scripts/cpu-disk-mem-alerts/main.py'
            }
        }
    }
    post {
        always {
            echo 'Pipeline finished. Only stages matching changed files actually ran.'
        }
    }
}
