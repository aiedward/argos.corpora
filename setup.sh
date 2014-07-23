# Get ready
sudo apt-get update && sudo apt-get upgrade

sudo apt-get install python3 bzr git python3-pip

# MongoDB
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10
echo "deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen" | sudo tee -a /etc/apt/sources.list
sudo apt-get update && sudo apt-get upgrade
sudo apt-get install mongodb-10gen
sudo service mongodb start

# Virtualenv
pip3 install virtualenv
virtualenv -p python3 /env/argos.corpora --no-site-packages
source /env/argos.corpora/bin/activate
pip install -r requirements.txt