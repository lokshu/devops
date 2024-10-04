#!/bin/bash

# Check if sshpass is installed, if not, install it
if ! command -v sshpass &> /dev/null
then
    echo "sshpass is not installed. Installing sshpass..."
    # Check if system uses apt (Debian/Ubuntu) or yum (RedHat/CentOS)
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y sshpass
    elif command -v yum &> /dev/null; then
        sudo yum install -y epel-release
        sudo yum install -y sshpass
    else
        echo "Error: Could not determine package manager. Please install sshpass manually."
        exit 1
    fi
else
    echo "sshpass is already installed."
fi

# Variables (replace with your values)
SOURCE_DB="dodomax20"
SOURCE_USER="xxxxxxx"
SOURCE_HOST="xxxxxxxxxx"

TARGET_DB="dodomax20"
TARGET_MYSQL_USER="xxxxxxxxxx"
TARGET_HOST="xxxxxxxxxxxxxxxxxx"
TARGET_SSH_USER="xxxxxxxxxxxxxx"

DUMP_FILE="db_dump.sql"
ZIPPED_FILE="db_dump.sql.gz"

# Step 1: Prompt for the Source MySQL password
echo -n "Enter password for source MySQL user $SOURCE_USER: "
read -s SOURCE_PASS
echo

# Step 2: Prompt for the Target MySQL password
# If no target password is provided, assume it's the same as the source password
echo -n "Enter password for target MySQL user $TARGET_MYSQL_USER (Press Enter if same as source): "
read -s TARGET_MYSQL_PASS
echo
if [ -z "$TARGET_MYSQL_PASS" ]; then
    TARGET_MYSQL_PASS=$SOURCE_PASS
    echo "Target MySQL password not entered, using source password for target."
fi

# Step 3: Prompt for the SSH password for the target server
echo -n "Enter SSH password for user $TARGET_SSH_USER@$TARGET_HOST: "
read -s TARGET_SSH_PASS
echo

# Step 4: Dump the MySQL database from the source server
echo "Dumping MySQL database from source server..."
mysqldump -u $SOURCE_USER -p$SOURCE_PASS -h $SOURCE_HOST $SOURCE_DB > $DUMP_FILE

if [ $? -eq 0 ]; then
    echo "Database dump successful."
else
    echo "Database dump failed!" >&2
    exit 1
fi

# Step 5: Compress the dump file
echo "Compressing the dump file..."
gzip -c $DUMP_FILE > $ZIPPED_FILE

if [ $? -eq 0 ]; then
    echo "File compression successful."
else
    echo "File compression failed!" >&2
    exit 1
fi

# Step 6: Transfer the compressed dump file to the target server using sshpass for SSH
echo "Transferring the compressed dump file to the target server..."
sshpass -p $TARGET_SSH_PASS scp $ZIPPED_FILE $TARGET_SSH_USER@$TARGET_HOST:/tmp/

if [ $? -eq 0 ]; then
    echo "File transfer successful."
else
    echo "File transfer failed!" >&2
    exit 1
fi

# Step 8: Decompress and import the database dump on the target server using sshpass
echo "Importing database dump into the target MySQL server..."
sshpass -p $TARGET_SSH_PASS ssh $TARGET_SSH_USER@$TARGET_HOST "gunzip /tmp/$ZIPPED_FILE && mysql -u $TARGET_MYSQL_USER -p'$TARGET_MYSQL_PASS' $TARGET_DB < /tmp/$DUMP_FILE"

if [ $? -eq 0 ]; then
    echo "Database import successful."
else
    echo "Database import failed!" >&2
    exit 1
fi

# Step 9: Clean up the dump files from both the local and target servers
echo "Cleaning up dump files..."
rm $DUMP_FILE
rm $ZIPPED_FILE
sshpass -p $TARGET_SSH_PASS ssh $TARGET_SSH_USER@$TARGET_HOST "rm /tmp/$DUMP_FILE"

echo "Database transfer complete."
