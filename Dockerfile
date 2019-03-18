FROM ubuntu:bionic

# Update base container install
RUN apt-get update
RUN apt-get upgrade -y

# Install GDAL dependencies
RUN apt-get install -y python3-pip libgdal-dev locales

# Install dependencies for other packages
RUN apt-get install gcc g++
#RUN apt-get install jpeg-dev zlib-dev

# Ensure locales configured correctly
RUN locale-gen en_US.UTF-8
ENV LC_ALL='en_US.utf8'

# Set python aliases for python3
RUN echo 'alias python=python3' >> ~/.bashrc
RUN echo 'alias pip=pip3' >> ~/.bashrc

# Update C env vars so compiler can find gdal
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# This will install latest version of GDAL
RUN apt-get -y install python3-gdal
RUN apt-get -y install zip
RUN apt-get install ca-certificates 
ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# Copy function to a path
RUN mkdir -p /var/cog_api
COPY . /var/cog_api/

# Work Directory
WORKDIR /var/cog_api/

# Build context
ADD app.py src /

ENV PYTHONUNBUFFERED = '1'

# Upgrading pip
RUN python3 -m pip install pip --upgrade
RUN python3 -m pip install wheel

# Install dependencies for tiling
RUN pip3 install flask && \
    pip3 install numpy && \
    pip3 install requests && \
    pip3 install rio_tiler==1.1.3 && \
    pip3 install flask_compress &&\
    pip3 install flask_cors &&\
    pip3 install gunicorn &&\
    pip3 install gevent &&\
    pip3 install pyproj

EXPOSE 8000

# ENTRYPOINT ["python3"]
# CMD ["app.py" ]    
# ENTRYPOINT ["gunicorn", "-k", "gevent", "-b", "0.0.0.0", "app:app"]
CMD ["gunicorn", "-k", "gevent", "-b", "0.0.0.0", "app:app"]