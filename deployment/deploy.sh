#!/bin/sh

source /home/docker-data/aadc-underway-email-processing/git/deployment/variables.sh

build_images () {
	echo -e '\n----------------------------------------------------------'
	echo -e 'Building the aadc/underway-email-processing image'
	echo -e '----------------------------------------------------------'
	docker build -t aadc/underway-email-processing .
}

# Function to deploy the metadata conversion container.
deploy_application () {
	# Stop and remove the container
	docker stop aadc-underway-email-processing
	docker rm aadc-underway-email-processing

	echo -e '\n----------------------------------------------------------'
	echo -e 'Running the aadc-underway-email-processing container with persistent storage on the host'
	echo -e '----------------------------------------------------------'
	docker run \
		-v /home/docker-data/aadc-underway-email-processing/git:/srv/git \
		-v /home/docker-data/aadc-underway-email-processing/data:/srv/data \
		-e EMAIL_SERVER=$EMAIL_SERVER \
		-e EMAIL_USERNAME=$EMAIL_USERNAME \
		-e EMAIL_PASSWORD=$EMAIL_PASSWORD \
		-w /srv/git \
		--name aadc-underway-email-processing \
		aadc/underway-email-processing
}

# Build the Docker image
build_images

echo -e '\n----------------------------------------------------------'
echo -e 'Creating directory'
echo -e '----------------------------------------------------------'
mkdir -p /home/docker-data/aadc-underway-email-processing

# Call the function to deploy the application
deploy_application

# List the Docker containers
docker ps