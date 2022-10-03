# imapclone

Clone emails and folder stucture to another imap server or a locally stored sqlite database to be restored from.

``` python
#IMAP to database
A = Imapclone()
A.imapsource("mail.example.com","example@example.com",'pa5sw0rd')
A.database("database.db")
A.clone()

#IMAP TO IMAP
A = Imapclone()
A.imapsource("mail.example.com","example@example.com",'pa5sw0rd')
A.imapdestination("mail.example2.com","example2@example2.com",'pa5sw0rd2')
A.clone()

#Database to IMAP
A = Imapclone()
A.imapdestination("mail.example2.com","example2@example2.com",'pa5sw0rd2')
A.database("database.db")
A.clone()
```