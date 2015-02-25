import semidbm
import base64
from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectGlobalUD import DistributedObjectGlobalUD
from direct.distributed.PyDatagram import *
from direct.fsm.FSM import FSM
import hashlib
import hmac
import json
from pandac.PandaModules import *
import time
import urllib2
import datetime
from datetime import datetime

from otp.ai.MagicWordGlobal import *
from otp.distributed import OtpDoGlobals
from toontown.makeatoon.NameGenerator import NameGenerator
from toontown.toon.ToonDNA import ToonDNA
from toontown.toonbase import TTLocalizer


# Import from PyCrypto only if we are using a database that requires it. This
# allows local hosted and developer builds of the game to run without it:
accountDBType = simbase.config.GetString('accountdb-type', 'developer')
if accountDBType == 'remote':
    from Crypto.Cipher import AES

if accountDBType == 'mongodb':
    import pymongo
    import bcrypt
    from pymongo import MongoClient

if accountDBType == 'mongodev':
    import pymongo
    from pymongo import MongoClient

if accountDBType == 'mysqldb':
    from passlib.hash import bcrypt
    import mysql.connector

# Sometimes we'll want to force a specific access level, such as on the
# developer server:
minAccessLevel = simbase.config.GetInt('min-access-level', 100)

accountServerEndpoint = simbase.config.GetString(
    'account-server-endpoint', 'https://toontownfellowship.com/api/')
accountServerSecret = simbase.config.GetString(
    'account-server-secret', '6163636f756e7473')


http = HTTPClient()
http.setVerifySsl(0)


def executeHttpRequest(url, **extras):
    print "executeHttpRequest: ", accountDBType, url, extras

    if accountDBType == 'remote':
        timestamp = str(int(time.time()))
        signature = hmac.new(accountServerSecret, timestamp, hashlib.sha256)
        request = urllib2.Request(accountServerEndpoint + url)
        request.add_header('User-Agent', 'TTI-CSM')
        request.add_header('X-CSM-Timestamp', timestamp)
        request.add_header('X-CSM-Signature', signature.hexdigest())
        for k, v in extras.items():
            request.add_header('X-CSM-' + k, v)
        try:
            return urllib2.urlopen(request).read()
        except:
            return None

    return None;

blacklist = executeHttpRequest('names/blacklist.json')
if blacklist:
    blacklist = json.loads(blacklist)

def judgeName(name):
    if not name:
        return False
    if blacklist:
        for namePart in name.split(' '):
            namePart = namePart.lower()
            if len(namePart) < 1:
                return False
            for banned in blacklist.get(namePart[0], []):
                if banned in namePart:
                    return False
    return True


# --- ACCOUNT DATABASES ---
# These classes make up the available account databases for Toontown fellowship.
# Databases with login tokens use the PyCrypto module for decrypting them.
# DeveloperAccountDB is a special database that accepts a username, and assigns
# each user with 600 access automatically upon login.


class AccountDB:
    notify = directNotify.newCategory('AccountDB')

    def __init__(self, csm):
        self.csm = csm

        filename = simbase.config.GetString(
            'account-bridge-filename', 'account-bridge')
        self.dbm = semidbm.open(filename, 'c')

    def addNameRequest(self, avId, name):
        return 'Success'

    def getNameStatus(self, avId):
        return 'APPROVED'

    def removeNameRequest(self, avId):
        return 'Success'

    def lookup(self, username, callback):
        pass  # Inheritors should override this.

    def persistMessage(self, category, description, sender, receiver):
        print ['persistMessage', category, description, sender, receiver]

    def persistChat(self, sender, message, channel):
        pass

    def storeAccountID(self, userId, accountId, callback):
        self.dbm[str(userId)] = str(accountId)  # semidbm only allows strings.
        if getattr(self.dbm, 'sync', None):
            self.dbm.sync()
            callback(True)
        else:
            self.notify.warning('Unable to associate user %s with account %d!' % (userId, accountId))
            callback(False)


class DeveloperAccountDB(AccountDB):
    notify = directNotify.newCategory('DeveloperAccountDB')

    def lookup(self, username, callback):
        # Let's check if this user's ID is in your account database bridge:
        if str(username) not in self.dbm:

            # Nope. Let's associate them with a brand new Account object! We
            # will assign them with 600 access just because they are a
            # developer:
            response = {
                'success': True,
                'userId': username,
                'accountId': 0,
                'accessLevel': max(600, minAccessLevel)
            }
            callback(response)
            return response

        else:

            # We have an account already, let's return what we've got:
            response = {
                'success': True,
                'userId': username,
                'accountId': int(self.dbm[str(username)]),
            }
            callback(response)
            return response


# This is the same as the DeveloperAccountDB, except it doesn't automatically
# give the user an access level of 600. Instead, the first user that is created
# gets 700 access, and every user created afterwards gets 100 access:

class LocalAccountDB(AccountDB):
    notify = directNotify.newCategory('LocalAccountDB')

    def lookup(self, username, callback):
        # Let's check if this user's ID is in your account database bridge:
        if str(username) not in self.dbm:

            # Nope. Let's associate them with a brand new Account object!
            response = {
                'success': True,
                'userId': username,
                'accountId': 0,
                'accessLevel': max((700 if not self.dbm else 100), minAccessLevel)
            }

            callback(response)
            return response

        else:

            # We have an account already, let's return what we've got:
            response = {
                'success': True,
                'userId': username,
                'accountId': int(self.dbm[str(username)])
            }
            callback(response)
            return response
            
class MongoDevAccountDB(AccountDB):
    #This class is used for development, and NOT production.
    # params:
    #    mongodb-url   how to connect to the mongodb
    #    mongodb-name  What db to use
    #
    # dependencies:
    #    pip install PyMongo    

    notify = directNotify.newCategory('MongoAccountDB')

    def __init__(self, csm):
        self.csm = csm

        dburltest = simbase.config.GetString('mongodb-url', 'mongodb://localhost:27017')
        self.client = MongoClient(dburltest)

        dbnametest = simbase.config.GetString('mongodb-name', 'test')
        self.db = self.client[dbnametest]

        self.accounts = self.db.accountdb

    def lookup(self, username, callback):
        if accounts.count() == 0:
            account = { "username": username, "accountId": 0, "accessLevel": 700}
            accounts.insert(account)
            response = {
              'success': True,
              'userId': username,
              'accountId': 0,
              'accessLevel': 700
            }
            callback(response)
            return response

        account = accounts.find_one({"username": username}) 

        if account:
            response = {
              'success': True,
              'userId': username,
              'accountId': int(account["accountId"]),
              'accessLevel': int(account["accessLevel"])
            }
            callback(response)
            return response
            

        account = { "username": username, "accountId": 0, "accessLevel": 600}
        accounts.insert(account)

        response = {
          'success': True,
          'userId': username,
          'accountId': 0,
          'accessLevel': int(account["accessLevel"])
        }

        callback(response)
        return response

    def storeAccountID(self, userId, accountId, callback):
        account = accounts.find_one({"username": userId})
        if account:
            accounts.update({"username": userId}, {"$set": {"accountId": accountId}})
            callback(True)
        else:
            self.notify.warning('Unable to associate user %s with account %d!' % (userId, accountId))
            callback(False)
            
# Mongo implementation of the AccountDB
#
# This was never used in production and might possibly not work.
# Still, it is a good starting point.  This has a similar behavior to
# DeveloperAccountDB and LocalAccountDB in that it automatically
# registers new users, the first user that is created
# gets 700 access, and every user created afterwards gets 100 access.
#
# params:
#    mongodb-url   how to connect to the mongodb
#    mongodb-name  What db to use
#
# dependencies:
#    pip install py-bcrypt PyMongo

class MongoAccountDB(AccountDB):
    notify = directNotify.newCategory('MongoAccountDB')

    def get_hashed_password(self, plain_text_password):
        return bcrypt.encrypt(plain_text_password)
 
    def check_password(self, plain_text_password, hashed_password):
        return bcrypt.verify(plain_text_password, hashed_password)

    def __init__(self, csm):
        self.csm = csm

        dburl = simbase.config.GetString('mongodb-url', 'mongodb://localhost:21021')
        self.client = MongoClient(dburl)

        dbname = simbase.config.GetString('mongodb-name', 'test')
        self.db = self.client[dbname]

        self.accounts = self.db.accountdb
        self.nameStatus = self.db.nameStatus

    def addNameRequest(self, avId, name):
        self.nameStatus.insert( { "avId": avId, "name": name, "status": "PENDING" } )
        return 'Success'

    def getNameStatus(self, avId):
        stat = self.nameStatus[avId]
        if stat:
            return stat["status"]
        return 'REJECTED'

    def removeNameRequest(self, avId):
        self.nameStatus.remove( { "avId": avId } )
        return 'Success'

    def lookup(self, token, callback):
        try:
            tokenList = token.split(':')
    
            if len(tokenList) != 2:
                response = {
                  'success': False,
                  'reason': "invalid password format"
                }
                callback(response)
                return response

            username = tokenList[0]
            password = tokenList[1]

            # special case for first user
            if accounts.count() == 0:
                account = { "username": username, "password": self.get_hashed_password(password), "accountId": 0, "accessLevel": 700}
                accounts.insert(account)
                response = {
                  'success': True,
                  'userId': username,
                  'accountId': 0,
                  'accessLevel': 700
                }
                callback(response)
                return response

            account = accounts.find_one({"username": username})

            if account:
                if not self.check_password(password, account["password"]):
                    response = {
                      'success': False,
                      'reason': "invalid password"
                    }
                    callback(response)
                    return response

                response = {
                    'success': True,
                    'userId': username,
                    'accountId': int(account["accountId"]),
                    'accessLevel': int(account["accessLevel"])
                }
                callback(response)
                return response

            account = { "username": username, "password": self.get_hashed_password(password), "accountId": 0, "accessLevel": max(100, minAccessLevel)}
            accounts.insert(account)

            response = {
              'success': True,
              'userId': username,
              'accountId': 0,
              'accessLevel': int(account["accessLevel"])
            }

            callback(response)
            return response
                
        except:
            self.notify.warning('Could not decode the provided token!')
            response = {
                'success': False,
                'reason': "Can't decode this token."
            }
            callback(response)
            return response

    def storeAccountID(self, userId, accountId, callback):
        account = accounts.find_one({"username": userId})
        if account:
            accounts.update({"username": userId}, {"$set": {"accountId": accountId}})
            callback(True)
        else:
            self.notify.warning('Unable to associate user %s with account %d!' % (userId, accountId))
            callback(False)

# MySQL implementation of the AccountDB
#
# params:
#        'mysql-username' =>  'toontown'
#        'mysql-password' =>  'password'
#        'mysql-db' =>  'toontown'
#        'mysql-host' =>  '127.0.0.1'
#        'mysql-port' =>  3306
#        'mysql-ssl' =>  False
#        'mysql-ssl-ca' =>  ''
#        'mysql-ssl-cert' =>  ''
#        'mysql-ssl-key' =>  ''
#        'mysql-ssl-verify-cert' =>  False
#        'mysql-auto-new-account' =>  True
#

# dependencies:
#    apt-get install python-mysqldb
#    pip install passlib

class MySQLAccountDB(AccountDB):
    notify = directNotify.newCategory('MySQLAccountDB')

    def get_hashed_password(self, plain_text_password):
        newpass = bcrypt.encrypt(plain_text_password)
        return newpass

    def check_password(self, plain_text_password, hashed_password):
        try:
            return bcrypt.verify(plain_text_password, hashed_password)
        except:
            print ("bad hash: ", (plain_text_password, hashed_password))
            return False

    def create_database(self, cursor):
      try:
          cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(self.db))
      except mysql.connector.Error as err:
          print("Failed creating database: {}".format(err))
          exit(1)

    def auto_migrate_semidbm(self):
        self.cur.execute(self.count_account)
        row = self.cur.fetchone()
        if row[0] != 0:
            return

        filename = simbase.config.GetString(
            'account-bridge-filename', 'account-bridge')
        dbm = semidbm.open(filename, 'c')

        for account in dbm.keys():
            accountid = dbm[account]
            print "%s maps to %s"%(account, accountid)
            self.cur.execute(self.add_account, (account,  "", accountid, 0))
        self.cnx.commit()
        dbm.close()

    def __init__(self, csm):
        self.csm = csm

        # Just a few configuration options
        self.username = simbase.config.GetString('mysql-username', 'toontown')
        self.password = simbase.config.GetString('mysql-password', 'password')
        self.db = simbase.config.GetString('mysql-db', 'toontown')
        self.host = simbase.config.GetString('mysql-host', '127.0.0.1')
        self.port = simbase.config.GetInt('mysql-port', 3306)
        self.ssl = simbase.config.GetBool('mysql-ssl', False)
        self.ssl_ca = simbase.config.GetString('mysql-ssl-ca', '')
        self.ssl_cert = simbase.config.GetString('mysql-ssl-cert', '')
        self.ssl_key = simbase.config.GetString('mysql-ssl-key', '')
        self.ssl_verify_cert = simbase.config.GetBool('mysql-ssl-verify-cert', False)
        self.auto_migrate = True

        # Lets try connection to the db
        if self.ssl:
            self.config = {
              'user': self.username,
              'password': self.password,
              'db': self.db,
              'host': self.host,
              'port': self.port,
              'client_flags': [ClientFlag.SSL],
              'ssl_ca': self.ssl_ca,
              'ssl_cert': self.ssl_cert,
              'ssl_key': self.ssl_key,
              'ssl_verify_cert': self.ssl_verify_cert
            }
        else:
            self.config = {
              'user': self.username,
              'password': self.password,
              'db': self.db,
              'host': self.host,
              'port': self.port,
            }

        self.cnx = mysql.connector.connect(**self.config)
        self.cur = self.cnx.cursor(buffered=True)

        # First we try to change the the particular db using the
        # database property.  If there is an error, we try to
        # create the database and then switch to it.

        try:
            self.cnx.database = self.db
        except mysql.connector.Error as err:
            if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                self.create_database(self.cur)
                self.cnx.database = self.db
            else:
                print(err)
                exit(1)

        self.count_account = ("SELECT COUNT(*) from Accounts")
        self.select_account = ("SELECT password,accountId,accessLevel,status,canPlay,banRelease FROM Accounts where username = %s")
        self.add_account = ("REPLACE INTO Accounts (username, password, accountId, accessLevel) VALUES (%s, %s, %s, %s)")
        self.update_avid = ("UPDATE Accounts SET accountId = %s where username = %s")
        self.count_avid = ("SELECT COUNT(*) from Accounts WHERE username = %s")
        self.insert_avoid = ("INSERT IGNORE Toons SET accountId = %s,toonid=%s")
        self.insert_message = ("INSERT IGNORE Messages SET time=%s,category=%s,description=%s,sender=%s,receiver=%s")
        self.insert_chat = ("INSERT IGNORE ChatAudit SET time=%s,sender=%s,message=%s,channel=%s")

        self.select_name = ("SELECT status FROM NameApprovals where avId = %s")
        self.add_name_request = ("REPLACE INTO NameApprovals (avId, name, status) VALUES (%s, %s, %s)")
        self.delete_name_query = ("DELETE FROM NameApprovals where avId = %s")

        if self.auto_migrate:
            self.auto_migrate_semidbm()

    def __del__(self):
        try:
            this.cur.close()
        except:
            pass

        try:
            this.cnx.close()
        except:
            pass

    def persistMessage(self, category, description, sender, receiver):
        self.cur.execute(self.insert_message, (int(time.time()), str(category), description, sender, receiver))
        self.cnx.commit()

    def persistChat(self, sender, message, channel):
        self.cur.execute(self.insert_chat, (int(time.time()), sender, message, channel))
        self.cnx.commit()

    def addNameRequest(self, avId, name):
       self.cur.execute(self.add_name_request, (avId, name, "PENDING"))
       self.cnx.commit()
       return 'Success'
        
    def getNameStatus(self, avId):
        self.cur.execute(self.select_name, (avId,))
        row = self.cur.fetchone()
        if row:
            return row[0]
        return "REJECTED"

    def removeNameRequest(self, avId):
        self.cur.execute(self.delete_name_query, (avId,))
        return 'Success'

    def __handleRetrieve(self, dclass, fields):
        if dclass != self.csm.air.dclassesByName['AccountUD']:
            return
        self.account = fields
        if self.account:
            self.avList = self.account['ACCOUNT_AV_SET']
            print self.avList
            for avId in self.avList:
                if avId:
                    self.cur.execute(self.insert_avoid, (self.accountid, avId))
                    self.cnx.commit()

    def lookup(self, token, callback):
        try:
            tokenList = token.split(':')

            if len(tokenList) != 2:
                response = {
                  'success': False,
                  'reason': "invalid password format"
                }
                print response
                callback(response)
                return response

            username = tokenList[0]
            password = tokenList[1]

            self.cur.execute(self.select_account, (username,))
            row = self.cur.fetchone()
            self.cnx.commit()

            if row:
                if row[4] == 0 and int(row[5]) > time.time():
                    response = {
                      'success': False,
                      'reason': "banned"
                    }
                    callback(response)
                    return response
                if not self.check_password(password, row[0]):
                    response = {
                      'success': False,
                      'reason': "invalid password"
                    }
                    callback(response)
                    return response

                if row[1] != 0:
                    self.account = None
                    self.accountid = row[1]
                    self.csm.air.dbInterface.queryObject(self.csm.air.dbId,  self.accountid, self.__handleRetrieve)

                response = {
                    'success': True,
                    'userId': username,
                    'accessLevel': int(row[2]),
                    'accountId': row[1]
                }

                print response
                callback(response)
                return response

            response = {
              'success': False,
              'reason': "unknown user"
            }
            print response
            callback(response)
            return response

        except mysql.connector.Error as err:
            print("mysql exception {}".format(err))
            response = {
                'success': False,
                'reason': "Can't decode this token."
            }
            print response
            callback(response)
            return response
#        except:
#            print "exception..."
#            self.notify.warning('Could not decode the provided token!')
#            response = {
#                'success': False,
#                'reason': "Can't decode this token."
#            }
#            print response
#            callback(response)
#            return response

    def storeAccountID(self, userId, accountId, callback):
        self.cur.execute(self.count_avid, (userId,))
        row = self.cur.fetchone()
    
        if row[0] >= 1:
            self.cur.execute(self.update_avid, (accountId, userId))
            self.cnx.commit()
            callback(True)
        else:
            print ("storeAccountId", self.update_avid, (aceountId, userId))
            self.notify.warning('Unable to associate user %s with account %d!' % (userId, accountId))
            callback(False)

class RemoteAccountDB(AccountDB):
    notify = directNotify.newCategory('RemoteAccountDB')

    def addNameRequest(self, avId, name):
        return executeHttpRequest('names/append', ID=str(avId), Name=name)

    def getNameStatus(self, avId):
        return executeHttpRequest('names/status/?Id=' + str(avId))

    def removeNameRequest(self, avId):
        return executeHttpRequest('names/remove', ID=str(avId))

    def lookup(self, token, callback):
        # First, base64 decode the token:
        try:
            token = base64.b64decode(token)
        except TypeError:
            self.notify.warning('Could not decode the provided token!')
            response = {
                'success': False,
                'reason': "Can't decode this token."
            }
            callback(response)
            return response

        # Ensure this token is a valid size:
        if (not token) or ((len(token) % 16) != 0):
            self.notify.warning('Invalid token length!')
            response = {
                'success': False,
                'reason': 'Invalid token length.'
            }
            callback(response)
            return response

        # Next, decrypt the token using AES-128 in CBC mode:
        accountServerSecret = simbase.config.GetString(
            'account-server-secret', '6163636f756e7473')

        # Ensure that our secret is the correct size:
        if len(accountServerSecret) > AES.block_size:
            self.notify.warning('account-server-secret is too big!')
            accountServerSecret = accountServerSecret[:AES.block_size]
        elif len(accountServerSecret) < AES.block_size:
            self.notify.warning('account-server-secret is too small!')
            accountServerSecret += '\x80'
            while len(accountServerSecret) < AES.block_size:
                accountServerSecret += '\x00'

        # Take the initialization vector off the front of the token:
        iv = token[:AES.block_size]

        # Truncate the token to get our cipher text:
        cipherText = token[AES.block_size:]

        # Decrypt!
        cipher = AES.new(accountServerSecret, mode=AES.MODE_CBC, IV=iv)
        try:
            token = json.loads(cipher.decrypt(cipherText).replace('\x00', ''))
            if ('timestamp' not in token) or (not isinstance(token['timestamp'], int)):
                raise ValueError
            if ('userid' not in token) or (not isinstance(token['userid'], int)):
                raise ValueError
            if ('accesslevel' not in token) or (not isinstance(token['accesslevel'], int)):
                raise ValueError
        except ValueError, e:
            print e
            self.notify.warning('Invalid token.')
            response = {
                'success': False,
                'reason': 'Invalid token.'
            }
            callback(response)
            return response

        # Next, check if this token has expired:
        expiration = simbase.config.GetInt('account-token-expiration', 1800)
        tokenDelta = int(time.time()) - token['timestamp']
        if tokenDelta > expiration:
            response = {
                'success': False,
                'reason': 'This token has expired.'
            }
            callback(response)
            return response

        # This token is valid. That's all we need to know. Next, let's check if
        # this user's ID is in your account database bridge:
        if str(token['userid']) not in self.dbm:

            # Nope. Let's associate them with a brand new Account object!
            response = {
                'success': True,
                'userId': token['userid'],
                'accountId': 0,
                'accessLevel': max(int(token['accesslevel']), minAccessLevel)
            }
            callback(response)
            return response

        else:

            # Yep. Let's return their account ID and access level!
            response = {
                'success': True,
                'userId': token['userid'],
                'accountId': int(self.dbm[str(token['userid'])]),
                'accessLevel': max(int(token['accesslevel']), minAccessLevel)
            }
            callback(response)
            return response


# --- FSMs ---
class OperationFSM(FSM):
    TARGET_CONNECTION = False

    def __init__(self, csm, target):
        self.csm = csm
        self.target = target

        FSM.__init__(self, self.__class__.__name__)

    def enterKill(self, reason=''):
        if self.TARGET_CONNECTION:
            self.csm.killConnection(self.target, reason)
        else:
            self.csm.killAccount(self.target, reason)
        self.demand('Off')

    def enterOff(self):
        if self.TARGET_CONNECTION:
            del self.csm.connection2fsm[self.target]
        else:
            del self.csm.account2fsm[self.target]


class LoginAccountFSM(OperationFSM):
    notify = directNotify.newCategory('LoginAccountFSM')
    TARGET_CONNECTION = True

    def enterStart(self, token):
        self.token = token
        self.demand('QueryAccountDB')

    def enterQueryAccountDB(self):
        self.csm.accountDB.lookup(self.token, self.__handleLookup)

    def __handleLookup(self, result):
        if not result.get('success'):
            self.csm.air.writeServerEvent('tokenRejected', self.target, self.token)
            self.demand('Kill', result.get('reason', 'The account server rejected your token.'))
            return

        self.userId = result.get('userId', 0)
        self.accountId = result.get('accountId', 0)
        self.accessLevel = result.get('accessLevel', 0)
        if self.accountId:
            self.demand('RetrieveAccount')
        else:
            self.demand('CreateAccount')

    def enterRetrieveAccount(self):
        self.csm.air.dbInterface.queryObject(
            self.csm.air.dbId, self.accountId, self.__handleRetrieve)

    def __handleRetrieve(self, dclass, fields):
        if dclass != self.csm.air.dclassesByName['AccountUD']:
            self.demand('Kill', 'Your account object was not found in the database!')
            return

        self.account = fields
        self.demand('SetAccount')

    def enterCreateAccount(self):
        self.account = {
            'ACCOUNT_AV_SET': [0] * 6,
            'ESTATE_ID': 0,
            'ACCOUNT_AV_SET_DEL': [],
            'CREATED': time.ctime(),
            'LAST_LOGIN': time.ctime(),
            'ACCOUNT_ID': str(self.userId),
            'ACCESS_LEVEL': self.accessLevel,
            'MONEY': 0
        }
        self.csm.air.dbInterface.createObject(
            self.csm.air.dbId,
            self.csm.air.dclassesByName['AccountUD'],
            self.account,
            self.__handleCreate)

    def __handleCreate(self, accountId):
        if self.state != 'CreateAccount':
            self.notify.warning('Received a create account response outside of the CreateAccount state.')
            return

        if not accountId:
            self.notify.warning('Database failed to construct an account object!')
            self.demand('Kill', 'Your account object could not be created in the game database.')
            return

        self.accountId = accountId
        self.csm.air.writeServerEvent('accountCreated', accountId)
        self.demand('StoreAccountID')

    def enterStoreAccountID(self):
        self.csm.accountDB.storeAccountID(
            self.userId,
            self.accountId,
            self.__handleStored)

    def __handleStored(self, success=True):
        if not success:
            self.demand('Kill', 'The account server could not save your user ID!')
            return

        self.demand('SetAccount')

    def enterSetAccount(self):
        # If necessary, update their account information:
        if self.accessLevel:
            self.csm.air.dbInterface.updateObject(
                self.csm.air.dbId,
                self.accountId,
                self.csm.air.dclassesByName['AccountUD'],
                {'ACCESS_LEVEL': self.accessLevel})

        # If there's anybody on the account, kill them for redundant login:
        datagram = PyDatagram()
        datagram.addServerHeader(
            self.csm.GetAccountConnectionChannel(self.accountId),
            self.csm.air.ourChannel,
            CLIENTAGENT_EJECT)
        datagram.addUint16(100)
        datagram.addString('This account has been logged in from elsewhere.')
        self.csm.air.send(datagram)

        # Next, add this connection to the account channel.
        datagram = PyDatagram()
        datagram.addServerHeader(
            self.target,
            self.csm.air.ourChannel,
            CLIENTAGENT_OPEN_CHANNEL)
        datagram.addChannel(self.csm.GetAccountConnectionChannel(self.accountId))
        self.csm.air.send(datagram)

        # Add this connection to extra channels which may be useful:
        if self.accessLevel > 100:
            datagram = PyDatagram()
            datagram.addServerHeader(self.target, self.csm.air.ourChannel,
                                     CLIENTAGENT_OPEN_CHANNEL)
            datagram.addChannel(OtpDoGlobals.OTP_STAFF_CHANNEL)
            self.csm.air.send(datagram)

        # Now set their sender channel to represent their account affiliation:
        datagram = PyDatagram()
        datagram.addServerHeader(
            self.target,
            self.csm.air.ourChannel,
            CLIENTAGENT_SET_CLIENT_ID)
        # Account ID in high 32 bits, 0 in low (no avatar):
        datagram.addChannel(self.accountId << 32)
        self.csm.air.send(datagram)

        # Un-sandbox them!
        datagram = PyDatagram()
        datagram.addServerHeader(
            self.target,
            self.csm.air.ourChannel,
            CLIENTAGENT_SET_STATE)
        datagram.addUint16(2)  # ESTABLISHED
        self.csm.air.send(datagram)

        # Update the last login timestamp:
        self.csm.air.dbInterface.updateObject(
            self.csm.air.dbId,
            self.accountId,
            self.csm.air.dclassesByName['AccountUD'],
            {'LAST_LOGIN': time.ctime(),
             'ACCOUNT_ID': str(self.userId)})

        # We're done.
        self.csm.air.writeServerEvent('accountLogin', self.target, self.accountId, self.userId)
        self.csm.sendUpdateToChannel(self.target, 'acceptLogin', [int(time.time())])
        self.demand('Off')

class CreateAvatarFSM(OperationFSM):
    notify = directNotify.newCategory('CreateAvatarFSM')

    def enterStart(self, dna, index):
        # Basic sanity-checking:
        if index >= 6:
            self.demand('Kill', 'Invalid index specified!')
            return

        if not ToonDNA().isValidNetString(dna):
            self.demand('Kill', 'Invalid DNA specified!')
            return

        self.index = index
        self.dna = dna

        # Okay, we're good to go, let's query their account.
        self.demand('RetrieveAccount')

    def enterRetrieveAccount(self):
        self.csm.air.dbInterface.queryObject(
            self.csm.air.dbId, self.target, self.__handleRetrieve)

    def __handleRetrieve(self, dclass, fields):
        if dclass != self.csm.air.dclassesByName['AccountUD']:
            self.demand('Kill', 'Your account object was not found in the database!')
            return

        self.account = fields

        self.avList = self.account['ACCOUNT_AV_SET']
        # Sanitize:
        self.avList = self.avList[:6]
        self.avList += [0] * (6-len(self.avList))

        # Make sure the index is open:
        if self.avList[self.index]:
            self.demand('Kill', 'This avatar slot is already taken by another avatar!')
            return

        # Okay, there's space. Let's create the avatar!
        self.demand('CreateAvatar')

    def enterCreateAvatar(self):
        dna = ToonDNA()
        dna.makeFromNetString(self.dna)
        colorString = TTLocalizer.NumToColor[dna.headColor]
        animalType = TTLocalizer.AnimalToSpecies[dna.getAnimal()]
        name = ' '.join((colorString, animalType))
        toonFields = {
            'setName': (name,),
            'WishNameState': ('OPEN',),
            'WishName': ('',),
            'setDNAString': (self.dna,),
            'setDISLid': (self.target,)
        }
        self.csm.air.dbInterface.createObject(
            self.csm.air.dbId,
            self.csm.air.dclassesByName['DistributedToonUD'],
            toonFields,
            self.__handleCreate)

    def __handleCreate(self, avId):
        if not avId:
            self.demand('Kill', 'Database failed to create the new avatar object!')
            return

        self.avId = avId
        self.demand('StoreAvatar')

    def enterStoreAvatar(self):
        # Associate the avatar with the account...
        self.avList[self.index] = self.avId
        self.csm.air.dbInterface.updateObject(
            self.csm.air.dbId,
            self.target,
            self.csm.air.dclassesByName['AccountUD'],
            {'ACCOUNT_AV_SET': self.avList},
            {'ACCOUNT_AV_SET': self.account['ACCOUNT_AV_SET']},
            self.__handleStoreAvatar)

    def __handleStoreAvatar(self, fields):
        if fields:
            self.demand('Kill', 'Database failed to associate the new avatar to your account!')
            return

        # Otherwise, we're done!
        self.csm.air.writeServerEvent('avatarCreated', self.avId, self.target, self.dna.encode('hex'), self.index)
        self.csm.sendUpdateToAccountId(self.target, 'createAvatarResp', [self.avId])
        self.demand('Off')


class AvatarOperationFSM(OperationFSM):
    POST_ACCOUNT_STATE = 'Off'  # This needs to be overridden.

    def enterRetrieveAccount(self):
        # Query the account:
        self.csm.air.dbInterface.queryObject(
            self.csm.air.dbId, self.target, self.__handleRetrieve)

    def __handleRetrieve(self, dclass, fields):
        if dclass != self.csm.air.dclassesByName['AccountUD']:
            self.demand('Kill', 'Your account object was not found in the database!')
            return

        self.account = fields

        self.avList = self.account['ACCOUNT_AV_SET']
        # Sanitize:
        self.avList = self.avList[:6]
        self.avList += [0] * (6-len(self.avList))

        self.demand(self.POST_ACCOUNT_STATE)


class GetAvatarsFSM(AvatarOperationFSM):
    notify = directNotify.newCategory('GetAvatarsFSM')
    POST_ACCOUNT_STATE = 'QueryAvatars'

    def enterStart(self):
        self.demand('RetrieveAccount')

    def enterQueryAvatars(self):
        self.pendingAvatars = set()
        self.avatarFields = {}
        for avId in self.avList:
            if avId:
                self.pendingAvatars.add(avId)

                def response(dclass, fields, avId=avId):
                    if self.state != 'QueryAvatars':
                        return
                    if dclass != self.csm.air.dclassesByName['DistributedToonUD']:
                        self.demand('Kill', "One of the account's avatars is invalid!")
                        return
                    self.avatarFields[avId] = fields
                    self.pendingAvatars.remove(avId)
                    if not self.pendingAvatars:
                        self.demand('SendAvatars')

                self.csm.air.dbInterface.queryObject(
                    self.csm.air.dbId,
                    avId,
                    response)

        if not self.pendingAvatars:
            self.demand('SendAvatars')

    def enterSendAvatars(self):
        potentialAvs = []

        for avId, fields in self.avatarFields.items():
            index = self.avList.index(avId)
            wishNameState = fields.get('WishNameState', [''])[0]
            name = fields['setName'][0]
            nameState = 0

            if wishNameState == 'OPEN':
                nameState = 1
            elif wishNameState == 'PENDING':
                actualNameState = self.csm.accountDB.getNameStatus(avId)
                self.csm.air.dbInterface.updateObject(
                    self.csm.air.dbId,
                    avId,
                    self.csm.air.dclassesByName['DistributedToonUD'],
                    {'WishNameState': [actualNameState]}
                )
                if actualNameState == 'PENDING':
                    nameState = 2
                if actualNameState == 'APPROVED':
                    nameState = 3
                    name = fields['WishName'][0]
                elif actualNameState == 'REJECTED':
                    nameState = 4
            elif wishNameState == 'APPROVED':
                nameState = 3
            elif wishNameState == 'REJECTED':
                nameState = 4

            potentialAvs.append([avId, name, fields['setDNAString'][0],
                                 index, nameState])

        self.csm.sendUpdateToAccountId(self.target, 'setAvatars', [potentialAvs])
        self.demand('Off')

# This inherits from GetAvatarsFSM, because the delete operation ends in a
# setAvatars message being sent to the client.
class DeleteAvatarFSM(GetAvatarsFSM):
    notify = directNotify.newCategory('DeleteAvatarFSM')
    POST_ACCOUNT_STATE = 'ProcessDelete'

    def enterStart(self, avId):
        self.avId = avId
        GetAvatarsFSM.enterStart(self)

    def enterProcessDelete(self):
        if self.avId not in self.avList:
            self.demand('Kill', 'Tried to delete an avatar not in the account!')
            return

        index = self.avList.index(self.avId)
        self.avList[index] = 0

        avsDeleted = list(self.account.get('ACCOUNT_AV_SET_DEL', []))
        avsDeleted.append([self.avId, int(time.time())])

        estateId = self.account.get('ESTATE_ID', 0)

        if estateId != 0:
            # This assumes that the house already exists, but it shouldn't
            # be a problem if it doesn't.
            self.csm.air.dbInterface.updateObject(
                self.csm.air.dbId,
                estateId,
                self.csm.air.dclassesByName['DistributedEstateAI'],
                {'setSlot%dToonId' % index: [0],
                 'setSlot%dItems' % index: [[]]}
            )

        self.csm.air.dbInterface.updateObject(
            self.csm.air.dbId,
            self.target,
            self.csm.air.dclassesByName['AccountUD'],
            {'ACCOUNT_AV_SET': self.avList,
             'ACCOUNT_AV_SET_DEL': avsDeleted},
            {'ACCOUNT_AV_SET': self.account['ACCOUNT_AV_SET'],
             'ACCOUNT_AV_SET_DEL': self.account['ACCOUNT_AV_SET_DEL']},
            self.__handleDelete)
        self.csm.accountDB.removeNameRequest(self.avId)

    def __handleDelete(self, fields):
        if fields:
            self.demand('Kill', 'Database failed to mark the avatar as deleted!')
            return

        self.csm.air.friendsManager.clearList(self.avId)
        self.csm.air.writeServerEvent('avatarDeleted', self.avId, self.target)
        self.demand('QueryAvatars')

class SetNameTypedFSM(AvatarOperationFSM):
    notify = directNotify.newCategory('SetNameTypedFSM')
    POST_ACCOUNT_STATE = 'RetrieveAvatar'

    def enterStart(self, avId, name):
        self.avId = avId
        self.name = name

        if self.avId:
            self.demand('RetrieveAccount')
            return

        # Hmm, self.avId was 0. Okay, let's just cut to the judging:
        self.demand('JudgeName')

    def enterRetrieveAvatar(self):
        if self.avId and self.avId not in self.avList:
            self.demand('Kill', 'Tried to name an avatar not in the account!')
            return

        self.csm.air.dbInterface.queryObject(self.csm.air.dbId, self.avId,
                                             self.__handleAvatar)

    def __handleAvatar(self, dclass, fields):
        if dclass != self.csm.air.dclassesByName['DistributedToonUD']:
            self.demand('Kill', "One of the account's avatars is invalid!")
            return

        if fields['WishNameState'][0] != 'OPEN':
            self.demand('Kill', 'Avatar is not in a namable state!')
            return

        self.demand('JudgeName')

    def enterJudgeName(self):
        # Let's see if the name is valid:
        status = judgeName(self.name)

        if self.avId and status:
            resp = self.csm.accountDB.addNameRequest(self.avId, self.name)
            if resp != 'Success':
                status = False
            else:
                self.csm.air.dbInterface.updateObject(
                    self.csm.air.dbId,
                    self.avId,
                    self.csm.air.dclassesByName['DistributedToonUD'],
                    {'WishNameState': ('PENDING',),
                     'WishName': (self.name,)})

        if self.avId:
            self.csm.air.writeServerEvent('avatarWishname', self.avId, self.name)

        self.csm.sendUpdateToAccountId(self.target, 'setNameTypedResp', [self.avId, status])
        self.demand('Off')

class SetNamePatternFSM(AvatarOperationFSM):
    notify = directNotify.newCategory('SetNamePatternFSM')
    POST_ACCOUNT_STATE = 'RetrieveAvatar'

    def enterStart(self, avId, pattern):
        self.avId = avId
        self.pattern = pattern

        self.demand('RetrieveAccount')

    def enterRetrieveAvatar(self):
        if self.avId and self.avId not in self.avList:
            self.demand('Kill', 'Tried to name an avatar not in the account!')
            return

        self.csm.air.dbInterface.queryObject(self.csm.air.dbId, self.avId,
                                             self.__handleAvatar)

    def __handleAvatar(self, dclass, fields):
        if dclass != self.csm.air.dclassesByName['DistributedToonUD']:
            self.demand('Kill', "One of the account's avatars is invalid!")
            return

        if fields['WishNameState'][0] != 'OPEN':
            self.demand('Kill', 'Avatar is not in a namable state!')
            return

        self.demand('SetName')

    def enterSetName(self):
        # Render the pattern into a string:
        parts = []
        for p, f in self.pattern:
            part = self.csm.nameGenerator.nameDictionary.get(p, ('', ''))[1]
            if f:
                part = part[:1].upper() + part[1:]
            else:
                part = part.lower()
            parts.append(part)

        parts[2] += parts.pop(3) # Merge 2&3 (the last name) as there should be no space.
        while '' in parts:
            parts.remove('')
        name = ' '.join(parts)

        self.csm.air.dbInterface.updateObject(
            self.csm.air.dbId,
            self.avId,
            self.csm.air.dclassesByName['DistributedToonUD'],
            {'WishNameState': ('',),
             'WishName': ('',),
             'setName': (name,)})

        self.csm.air.writeServerEvent('avatarNamed', self.avId, name)
        self.csm.sendUpdateToAccountId(self.target, 'setNamePatternResp', [self.avId, 1])
        self.demand('Off')


class AcknowledgeNameFSM(AvatarOperationFSM):
    notify = directNotify.newCategory('AcknowledgeNameFSM')
    POST_ACCOUNT_STATE = 'GetTargetAvatar'

    def enterStart(self, avId):
        self.avId = avId
        self.demand('RetrieveAccount')

    def enterGetTargetAvatar(self):
        # Make sure the target avatar is part of the account:
        if self.avId not in self.avList:
            self.demand('Kill', 'Tried to acknowledge name on an avatar not in the account!')
            return

        self.csm.air.dbInterface.queryObject(self.csm.air.dbId, self.avId,
                                             self.__handleAvatar)

    def __handleAvatar(self, dclass, fields):
        if dclass != self.csm.air.dclassesByName['DistributedToonUD']:
            self.demand('Kill', "One of the account's avatars is invalid!")
            return

        # Process the WishNameState change.
        wishNameState = fields['WishNameState'][0]
        wishName = fields['WishName'][0]
        name = fields['setName'][0]

        if wishNameState == 'APPROVED':
            wishNameState = ''
            name = wishName
            wishName = ''
            self.csm.accountDB.removeNameRequest(self.avId)
        elif wishNameState == 'REJECTED':
            wishNameState = 'OPEN'
            wishName = ''
            self.csm.accountDB.removeNameRequest(self.avId)
        else:
            self.demand('Kill', "Tried to acknowledge name on an avatar in %s state!" % wishNameState)
            return

        # Push the change back through:
        self.csm.air.dbInterface.updateObject(
            self.csm.air.dbId,
            self.avId,
            self.csm.air.dclassesByName['DistributedToonUD'],
            {'WishNameState': (wishNameState,),
             'WishName': (wishName,),
             'setName': (name,)},
            {'WishNameState': fields['WishNameState'],
             'WishName': fields['WishName'],
             'setName': fields['setName']})

        self.csm.sendUpdateToAccountId(self.target, 'acknowledgeAvatarNameResp', [])
        self.demand('Off')


class LoadAvatarFSM(AvatarOperationFSM):
    notify = directNotify.newCategory('LoadAvatarFSM')
    POST_ACCOUNT_STATE = 'GetTargetAvatar'

    def enterStart(self, avId):
        self.avId = avId
        self.demand('RetrieveAccount')

    def enterGetTargetAvatar(self):
        # Make sure the target avatar is part of the account:
        if self.avId not in self.avList:
            self.demand('Kill', 'Tried to play an avatar not in the account!')
            return

        self.csm.air.dbInterface.queryObject(self.csm.air.dbId, self.avId,
                                             self.__handleAvatar)

    def __handleAvatar(self, dclass, fields):
        if dclass != self.csm.air.dclassesByName['DistributedToonUD']:
            self.demand('Kill', "One of the account's avatars is invalid!")
            return

        self.avatar = fields
        self.demand('SetAvatar')

    def enterSetAvatarTask(self, channel, task):
        # Finally, grant ownership and shut down.
        datagram = PyDatagram()
        datagram.addServerHeader(
            self.avId,
            self.csm.air.ourChannel,
            STATESERVER_OBJECT_SET_OWNER)
        datagram.addChannel(self.target<<32 | self.avId)
        self.csm.air.send(datagram)

        # Tell the GlobalPartyManager as well:
        self.csm.air.globalPartyMgr.avatarJoined(self.avId)

        self.csm.air.writeServerEvent('avatarChosen', self.avId, self.target)
        self.demand('Off')
        return task.done

    def enterSetAvatar(self):
        channel = self.csm.GetAccountConnectionChannel(self.target)

        # First, give them a POSTREMOVE to unload the avatar, just in case they
        # disconnect while we're working.
        datagramCleanup = PyDatagram()
        datagramCleanup.addServerHeader(
            self.avId,
            channel,
            STATESERVER_OBJECT_DELETE_RAM)
        datagramCleanup.addUint32(self.avId)
        datagram = PyDatagram()
        datagram.addServerHeader(
            channel,
            self.csm.air.ourChannel,
            CLIENTAGENT_ADD_POST_REMOVE)
        datagram.addString(datagramCleanup.getMessage())
        self.csm.air.send(datagram)

        # Activate the avatar on the DBSS:
        self.csm.air.sendActivate(
            self.avId, 0, 0, self.csm.air.dclassesByName['DistributedToonUD'],
            {'setAdminAccess': [self.account.get('ACCESS_LEVEL', 100)],
             'setBankMoney': [self.account.get('MONEY', 0)]})

        # Next, add them to the avatar channel:
        datagram = PyDatagram()
        datagram.addServerHeader(
            channel,
            self.csm.air.ourChannel,
            CLIENTAGENT_OPEN_CHANNEL)
        datagram.addChannel(self.csm.GetPuppetConnectionChannel(self.avId))
        self.csm.air.send(datagram)

        # Now set their sender channel to represent their account affiliation:
        datagram = PyDatagram()
        datagram.addServerHeader(
            channel,
            self.csm.air.ourChannel,
            CLIENTAGENT_SET_CLIENT_ID)
        datagram.addChannel(self.target<<32 | self.avId)
        self.csm.air.send(datagram)

        # Eliminate race conditions.
        taskMgr.doMethodLater(0.2, self.enterSetAvatarTask,
                              'avatarTask-%s' % self.avId, extraArgs=[channel],
                              appendTask=True)

class UnloadAvatarFSM(OperationFSM):
    notify = directNotify.newCategory('UnloadAvatarFSM')

    def enterStart(self, avId):
        self.avId = avId

        # We don't even need to query the account, we know the avatar is being played!
        self.demand('UnloadAvatar')

    def enterUnloadAvatar(self):
        channel = self.csm.GetAccountConnectionChannel(self.target)

        # Tell TTIFriendsManager somebody is logging off:
        self.csm.air.friendsManager.toonOffline(self.avId)

        # Clear off POSTREMOVE:
        datagram = PyDatagram()
        datagram.addServerHeader(
            channel,
            self.csm.air.ourChannel,
            CLIENTAGENT_CLEAR_POST_REMOVES)
        self.csm.air.send(datagram)

        # Remove avatar channel:
        datagram = PyDatagram()
        datagram.addServerHeader(
            channel,
            self.csm.air.ourChannel,
            CLIENTAGENT_CLOSE_CHANNEL)
        datagram.addChannel(self.csm.GetPuppetConnectionChannel(self.avId))
        self.csm.air.send(datagram)

        # Reset sender channel:
        datagram = PyDatagram()
        datagram.addServerHeader(
            channel,
            self.csm.air.ourChannel,
            CLIENTAGENT_SET_CLIENT_ID)
        datagram.addChannel(self.target<<32)
        self.csm.air.send(datagram)

        # Unload avatar object:
        datagram = PyDatagram()
        datagram.addServerHeader(
            self.avId,
            channel,
            STATESERVER_OBJECT_DELETE_RAM)
        datagram.addUint32(self.avId)
        self.csm.air.send(datagram)

        # Done!
        self.csm.air.writeServerEvent('avatarUnload', self.avId)
        self.demand('Off')


# --- CLIENT SERVICES MANAGER UBERDOG ---
class ClientServicesManagerUD(DistributedObjectGlobalUD):
    notify = directNotify.newCategory('ClientServicesManagerUD')

    def announceGenerate(self):
        DistributedObjectGlobalUD.announceGenerate(self)

        # These keep track of the connection/account IDs currently undergoing an
        # operation on the CSM. This is to prevent (hacked) clients from firing up more
        # than one operation at a time, which could potentially lead to exploitation
        # of race conditions.
        self.connection2fsm = {}
        self.account2fsm = {}

        # For processing name patterns.
        self.nameGenerator = NameGenerator()

        # Temporary HMAC key:
        self.key = 'bG9sLndlLmNoYW5nZS50aGlzLnRvby5tdWNo'

        # Instantiate our account DB interface:
        if accountDBType == 'developer':
            self.accountDB = DeveloperAccountDB(self)
        elif accountDBType == 'local':
            self.accountDB = LocalAccountDB(self)
        elif accountDBType == 'mongodb':
            self.accountDB = MongoAccountDB(self)
        elif accountDBType == 'mongodev':
            self.accountDB = MongoDevAccountDB(self)
        elif accountDBType == 'mysqldb':
            self.accountDB = MySQLAccountDB(self)
        elif accountDBType == 'remote':
            self.accountDB = RemoteAccountDB(self)
        else:
            self.notify.error('Invalid accountdb-type: ' + accountDBType)

    def killConnection(self, connId, reason):
        datagram = PyDatagram()
        datagram.addServerHeader(
            connId,
            self.air.ourChannel,
            CLIENTAGENT_EJECT)
        datagram.addUint16(122)
        datagram.addString(reason)
        self.air.send(datagram)

    def killConnectionFSM(self, connId):
        fsm = self.connection2fsm.get(connId)

        if not fsm:
            self.notify.warning('Tried to kill connection %d for duplicate FSM, but none exists!' % connId)
            return

        self.killConnection(connId, 'An operation is already underway: ' + fsm.name)

    def killAccount(self, accountId, reason):
        self.killConnection(self.GetAccountConnectionChannel(accountId), reason)

    def killAccountFSM(self, accountId):
        fsm = self.account2fsm.get(accountId)
        if not fsm:

            self.notify.warning('Tried to kill account %d for duplicate FSM, but none exists!' % accountId)
            return

        self.killAccount(accountId, 'An operation is already underway: ' + fsm.name)

    def runAccountFSM(self, fsmtype, *args):
        sender = self.air.getAccountIdFromSender()

        if not sender:
            self.killAccount(sender, 'Client is not logged in.')

        if sender in self.account2fsm:
            self.killAccountFSM(sender)
            return

        self.account2fsm[sender] = fsmtype(self, sender)
        self.account2fsm[sender].request('Start', *args)

    def login(self, cookie, authKey):
        self.notify.debug('Received login cookie %r from %d' % (cookie, self.air.getMsgSender()))

        sender = self.air.getMsgSender()

        # Time to check this login to see if its authentic
        digest_maker = hmac.new(self.key)
        digest_maker.update(cookie)
        serverKey = digest_maker.hexdigest()
        if serverKey == authKey:
            # This login is authentic!
            pass
        else:
            # This login is not authentic.
            self.killConnection(sender, ' ')

        if sender >> 32:
            self.killConnection(sender, 'Client is already logged in.')
            return

        if sender in self.connection2fsm:
            self.killConnectionFSM(sender)
            return

        self.connection2fsm[sender] = LoginAccountFSM(self, sender)
        self.connection2fsm[sender].request('Start', cookie)

    def requestAvatars(self):
        self.notify.debug('Received avatar list request from %d' % (self.air.getMsgSender()))
        self.runAccountFSM(GetAvatarsFSM)

    def createAvatar(self, dna, index):
        self.runAccountFSM(CreateAvatarFSM, dna, index)

    def deleteAvatar(self, avId):
        self.runAccountFSM(DeleteAvatarFSM, avId)

    def setNameTyped(self, avId, name):
        self.runAccountFSM(SetNameTypedFSM, avId, name)

    def setNamePattern(self, avId, p1, f1, p2, f2, p3, f3, p4, f4):
        self.runAccountFSM(SetNamePatternFSM, avId, [(p1, f1), (p2, f2),
                                                     (p3, f3), (p4, f4)])

    def acknowledgeAvatarName(self, avId):
        self.runAccountFSM(AcknowledgeNameFSM, avId)

    def chooseAvatar(self, avId):
        currentAvId = self.air.getAvatarIdFromSender()
        accountId = self.air.getAccountIdFromSender()
        if currentAvId and avId:
            self.killAccount(accountId, 'A Toon is already chosen!')
            return
        elif not currentAvId and not avId:
            # This isn't really an error, the client is probably just making sure
            # none of its Toons are active.
            return

        if avId:
            self.runAccountFSM(LoadAvatarFSM, avId)
        else:
            self.runAccountFSM(UnloadAvatarFSM, currentAvId)
