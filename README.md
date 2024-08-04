# imapclone

Clone emails and folder stucture to another imap server or a locally stored sqlite database to be restored from.

```bash
Examples:
    IMAP to IMAP:
        python3 imapclone.py --source mail.example.com example@example.com pa5sw0rd --destination mail.example2.com example2@example2.com pa5sw0rd2
    
    IMAP to Database:
        python3 imapclone.py --source mail.example.com example@example.com pa5sw0rd --destination databasename.sql
    
    Database to IMAP:
        python3 imapclone.py --source databasename.sql --destination mail.example2.com example2@example2.com pa5sw0rd2'''
```



``` python
#IMAP to database
A = ImapClone()
A.imapsource("mail.example.com","example@example.com",'pa5sw0rd')
A.database("database.db")
A.clone()

#IMAP TO IMAP
A = ImapClone()
A.imapsource("mail.example.com","example@example.com",'pa5sw0rd')
A.imapdestination("mail.example2.com","example2@example2.com",'pa5sw0rd2')
A.clone()

#Database to IMAP
A = ImapClone()
A.imapdestination("mail.example2.com","example2@example2.com",'pa5sw0rd2')
A.database("database.db")
A.clone()
```