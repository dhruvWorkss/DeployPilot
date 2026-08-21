pipeline {
  agent any
  options { timestamps(); disableConcurrentBuilds(); timeout(time: 30, unit: 'MINUTES'); buildDiscarder(logRotator(numToKeepStr: '30')) }
  environment {
    PROJECT_ID = credentials('gcp-project-id')
    REGION = 'us-central1'
    REPOSITORY = 'deploypilot'
    IMAGE_NAME = 'control-plane'
    NAMESPACE = 'deploypilot'
    DEPLOYMENT = 'deploypilot-api'
    CONTAINER = 'api'
  }
  stages {
    stage('Validate') {
      parallel {
        stage('Backend') { steps { sh 'docker build --target builder -t deploypilot-api-test services/control-plane'; sh 'docker run --rm deploypilot-api-test pytest' } }
        stage('Frontend') { steps { dir('apps/web') { sh 'npm ci'; sh 'npm run lint'; sh 'npm run build' } } }
        stage('Terraform') { steps { sh 'terraform -chdir=infra/terraform fmt -check -recursive'; sh 'terraform -chdir=infra/terraform init -backend=false'; sh 'terraform -chdir=infra/terraform validate' } }
      }
    }
    stage('Build and scan') {
      steps {
        sh 'docker build --pull -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${GIT_COMMIT} services/control-plane'
        sh 'trivy image --exit-code 1 --severity HIGH,CRITICAL --ignore-unfixed ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${GIT_COMMIT}'
      }
    }
    stage('Publish immutable image') {
      when { branch 'main' }
      steps {
        sh 'gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet'
        sh 'docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${GIT_COMMIT}'
        script { env.IMAGE_DIGEST = sh(script: 'docker inspect --format="{{index .RepoDigests 0}}" ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${GIT_COMMIT}', returnStdout: true).trim() }
      }
    }
    stage('Deploy and verify') {
      when { branch 'main' }
      steps { sh 'IMAGE=${IMAGE_DIGEST} bash scripts/release.sh' }
    }
  }
  post { failure { archiveArtifacts artifacts: 'deployment.log', allowEmptyArchive: true; echo 'Release failed or was automatically rolled back.' } }
}
