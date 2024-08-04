"""
    Clone IMAP emails and folder stucture
"""

import imaplib
import time
import sqlite3
import logging

class ImapClone():
    """
    Clone IMAP folder structure, emails and flags to a SQLite database or another IMAP server.\n
    imap = Imapclone()\n
    imap.imapsource("mail.example.com","example@example.com",'pa5sw0rd')\n
    imap.imapdestination("mail.example2.com","example2@example2.com",'pa5sw0rd2')\n
    imap.database("database.db")\n
    imap.clone()
    """

    def __init__(self,debug=False) -> None:
        """
            Initialize logger and variables
        """
        if debug is True:
            logging.basicConfig(level=logging.DEBUG)
        elif debug is False:
            logging.basicConfig(level=logging.INFO)

        self.sourceimap = None
        self.sourceuser = None
        self.sourcepass = None
        self.sourcessl = True
        self.desimap = None
        self.desuser = None
        self.despass = None
        self.desssl = True
        self.dbfile = None
        self.folder = None
        self.destination = None
        self.flags = None
        self.internaldate = None
        self.body = None
        self.source = None
        self.sourcefolderlist = None
        self.des = None

    def imapsource(self,imap:str,user:str,password:str,ssl:bool=True) -> None:
        """
            imap = imap.example.com\n
            user = exampleuser\n
            password = pa5sw0rd\n
            ssl = imap server supports SSL
        """
        self.sourceimap = imap
        self.sourceuser = user
        self.sourcepass = password
        self.sourcessl = ssl

    def imapdestination(self,imap:str,user:str,password:str,ssl:bool=True) -> None:
        """
            imap = imap.example.com\n
            user = exampleuser\n
            password = pa5sw0rd\n
            ssl = imap server supports SSL
        """
        self.desimap = imap
        self.desuser = user
        self.despass = password
        self.desssl = ssl

    def database(self,dbfile:str) -> None:
        """
            Creates a database if it doesnt exists already already
            otherwise sets the database file name as source
        """
        self.dbfile = dbfile
        with sqlite3.connect(self.dbfile) as database:
            database.execute('CREATE TABLE IF NOT EXISTS emails(folder TEXT NOT NULL, flags BLOB NOT NULL, internaldate INTEGER NOT NULL, message BLOB NOT NULL, UNIQUE(folder,internaldate,message))')
            database.commit()

    def clone(self) -> None:
        """
            Starts the cloning progress.
            Requires two of these to be set first:\n
                imap.imapsource("mail.example.com","example@example.com",'pa5sw0rd')\n
                imap.imapdestination("mail.example2.com","example2@example2.com",'pa5sw0rd2')\n
                imap.database("database.db")

        """
        if self.sourceimap:
            if self.desimap:
                self.destination = True
                self._startimaptoimap()

            elif self.dbfile:
                self.destination = False
                self._startimaptodb()
            else:
                raise ValueError("Destination not set")
        elif self.dbfile:
            if self.desimap:
                self.destination = True
                self._startdbtoimap()
            else:
                raise ValueError("IMAP Destination not set")
        else:
            raise ValueError("Source not set")

    def _startimaptodb(self) -> None:
        self._imapsourcelogin()
        self._imapsourcegetemail()

    def _startimaptoimap(self) -> None:
        self._imapsourcelogin()
        self._imapdeslogin()
        self._imapsourcegetemail()

    def _startdbtoimap(self) -> None:
        self._imapdeslogin()
        self._dbtoimap()

    def _dbtoimap(self):
        with sqlite3.connect(self.dbfile) as database:
            folderlist = database.execute("SELECT folder from emails GROUP BY folder")
            for folder in folderlist:
                self._writetoimap(folder=folder[0])
            total = database.execute("SELECT count(*) from emails").fetchone()[0]
            for count, data in enumerate(database.execute("SELECT * from emails")):
                self.folder = data[0]
                self.flags = data[1]
                self.internaldate = imaplib.Time2Internaldate(data[2])
                self.body = data[3]
                logging.debug(f"{count+1} / {total} {data}")
                self._writetoimap(count+1,total)

    def _imapsourcelogin(self):
        logging.info(f"Connecting to source {self.sourceimap}")
        if self.sourcessl:
            self.source = imaplib.IMAP4_SSL(self.sourceimap)
        else:
            self.source = imaplib.IMAP4(self.sourceimap)
        self.source.login(self.sourceuser, self.sourcepass)
        self.sourcefolderlist = self.source.list(directory='""', pattern='*')
        if self.folder:
            self.source.select(self.folder,readonly=True)

    def _imapsourcegetemail(self):
        for folder in self.sourcefolderlist[1]:
            foldersplit = folder.decode().replace('"."','"/"').split('"/"')

            if 'Noselect' not in foldersplit[0]:
                self.folder = foldersplit[1].strip()
                self.source.select(self.folder,readonly=True)

                if self.destination is True:
                        self._writetoimap(folder=self.folder)

                # make sure the folder isnt empty
                _, data = self.source.search(None, 'ALL')

                if data[0] != b'':
                    _, uidlist = self.source.fetch('1:*','UID')
                    uidlist = [i.decode().strip(")").split(" ")[-1] for i in uidlist]
                    emailsinfolder = len(uidlist)

                    for count, uid in enumerate(uidlist):
                        count += 1
                        while True:
                            try:
                                typ, message = self.source.uid('FETCH',uid,'(FLAGS INTERNALDATE BODY[])')
                                break
                            except Exception as e:
                                logging.warning(e)
                                time.sleep(10)
                                try:
                                    self._imapsourcelogin()
                                except Exception as x:
                                    logging.warning(x)

                        if message != [None]:
                            self.flags = ' '.join(flags.decode() for flags in imaplib.ParseFlags(message[0][0]))
                            self.internaldate = imaplib.Internaldate2tuple(message[0][0])
                            self.body = message[0][1]
                            logging.debug(self.flags)
                            logging.debug(self.internaldate)
                            logging.info(f"Fetched: {typ}, Folder: {self.folder} - {count} / {emailsinfolder} Flags:{self.flags}")
                            if self.destination is True:
                                self._writetoimap(count,emailsinfolder)
                            elif self.destination is False:
                                self._writetodb()

    def _writetodb(self):
        with sqlite3.connect(self.dbfile) as database:
            try:
                database.execute('INSERT INTO emails VALUES(?,?,?,?)',
                (self.folder,self.flags,int(time.mktime(self.internaldate)),self.body))
                database.commit()
            except sqlite3.Error as e:
                if "UNIQUE constraint failed" in str(e):
                    logging.info("Duplicate email, skipping")
                else:
                    logging.error(e)

    def _imapdeslogin(self):
        logging.info(f"Connecting to destination {self.desimap}")
        
        if self.desssl:
            self.des = imaplib.IMAP4_SSL(self.desimap)
        else:
            self.des = imaplib.IMAP4(self.desimap)
        self.des.login(self.desuser, self.despass)

    def _cleanflags(self):
        """
            Removes problematic flags
        """
        return self.flags.replace("\\Recent","").replace("\\Indexed","").strip()

    def _writetoimap(self,cur=None,total=None,folder=None):
        while True:
            try:
                if folder:
                    res = self.des.create(folder)
                else:
                    res = self.des.append(
                        self.folder,self._cleanflags(),
                        imaplib.Time2Internaldate(self.internaldate),
                        self.body)
                break
            except Exception as e:
                if "flag" in str(e):
                    logging.warning("Message flag error, removing flags for message")
                    self.flags = ""
                else:
                    logging.warning(e)
                time.sleep(10)
                try:
                    self._imapdeslogin()
                except Exception as x:
                    logging.warning(x)
        if folder:
            logging.info(f"Folder: {res}, {folder}")
        else:
            logging.info(f"Posted: {res}, Folder: {self.folder} - {cur} / {total} Flags: {self.flags}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        prog='IMAP Cloner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''Clone mailbox via imap to database or target imap
        Examples:
            IMAP to IMAP:
                imapclone.py --source mail.example.com example@example.com pa5sw0rd --destination mail.example2.com example2@example2.com pa5sw0rd2
            
            IMAP to Database:
                imapclone.py --source mail.example.com example@example.com pa5sw0rd --destination databasename.sql
            
            Database to IMAP:
                imapclone.py --source databasename.sql --destination mail.example2.com example2@example2.com pa5sw0rd2''')
        
    parser.add_argument('-v',action='store_true',default=False)
    parser.add_argument('--source','-s',nargs='+')
    parser.add_argument('--destination','-d',nargs='+')
    a = parser.parse_args()
    imap = ImapClone(debug=a.v)
    if len(a.source) == 3:
        imap.imapsource(a.source[0],a.source[1],a.source[2])
    else:
        imap.database(a.source[0])

    if len(a.destination) == 3:
        imap.imapdestination(a.destination[0],a.destination[1],a.destination[2])
    else:
        imap.database(a.destination[0])
    imap.clone()