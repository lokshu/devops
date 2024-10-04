#!/bin/bash

DATE=$(date +%d-%m-%Y)
BACKUP_DIR="/data/backup"
MYSQL_USER="xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
MYSQL_PASSWORD="xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
MYSQL=mysql
MYSQLDUMP=mysqldump

mkdir -p $BACKUP_DIR/$DATE

databases=`$MYSQL -u$MYSQL_USER -p$MYSQL_PASSWORD -e "SHOW DATABASES;" | grep -Ev "(Database|information_schema)"`

for db in $databases; do
  echo $db
  $MYSQLDUMP --force --opt --user=$MYSQL_USER -p$MYSQL_PASSWORD --databases $db | gzip > "$BACKUP_DIR/$DATE/$db.sql.gz"
done

find $BACKUP_DIR/* -mtime +5 -exec rm {} \;
