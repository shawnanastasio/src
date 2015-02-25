CREATE TABLE `Accounts` (
  `id` int(10) NOT NULL AUTO_INCREMENT,
  `username` varchar(20) NOT NULL,
  `password` varchar(255) NOT NULL,
  `rawPassword` tinyint(4) NOT NULL,
  `email` varchar(255) NOT NULL,
  `accountid` int(11) NOT NULL,
  `accesslevel` int(11) NOT NULL,
  `canPlay` int(10) DEFAULT '1',
  `ipBanned` int(10) DEFAULT '0',
  `banReason` varchar(255) NOT NULL,
  `banRelease` varchar(30) NOT NULL,
  `bannedTime` varchar(30) NOT NULL,
  `banBy` varchar(20) NOT NULL,
  `isMod` tinyint(10) NOT NULL,
  `status` text NOT NULL,
  `name` varchar(25) NOT NULL,
  `newsname` varchar(25) NOT NULL,
  `registrationdate` varchar(40) NOT NULL,
  `allowemails` tinyint(10) NOT NULL DEFAULT '1',
  `registrationip` varchar(50) NOT NULL,
  `lastloggedinip` varchar(50) NOT NULL,
  `rpwkey` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

CREATE TABLE `NameApprovals` (
  `id` int(10) NOT NULL AUTO_INCREMENT,
  `avid` int(11) NOT NULL,
  `name` varchar(40) NOT NULL,
  `status` varchar(10) NOT NULL,
  `reviewedby` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

CREATE TABLE `Messages` (
  `id`          int(10) NOT NULL AUTO_INCREMENT,
  `time`        int(11) NOT NULL,
  `category`    varchar(40) NOT NULL,
  `description` varchar(40) NOT NULL,
  `sender`      varchar(10) NOT NULL,
  `receiver`    varchar(10) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

CREATE TABLE `ChatAudit` (
  `id`          int(10) NOT NULL AUTO_INCREMENT,
  `time`        int(11) NOT NULL,
  `sender`      varchar(40) NOT NULL,
  `message`     varchar(255) NOT NULL,
  `channel`     varchar(10) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

CREATE TABLE `Toons` (
  `id`          int(10) NOT NULL AUTO_INCREMENT,
  `accountid`   int(11) NOT NULL,
  `toonid`      int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `toonid` (`toonid`)
) ENGINE=InnoDB;
