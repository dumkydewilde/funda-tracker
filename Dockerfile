
# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables for the database
ENV HOST=<your_host>
ENV USER=<your_user>
ENV PASSWORD=<your_password>

RUN apt-get update &&  apt-get -y install libpq-dev gcc

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt --no-cache-dir 

ENV POSTAL_CODES="1063 3511 2511 5613 6512 6221 8025"
ENV PUBLICATION_DATE="now-1d"

# Define the command to run the application
CMD ["sh", "-c", "for postal_code in $POSTAL_CODES; do python fundatracker --postal_code $postal_code --km_radius 10 --publication_date='$PUBLICATION_DATE'; done"]
