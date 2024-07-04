-- Users table--
DROP TABLE IF EXISTS "user";
CREATE TABLE "user" (
    userID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, -- Integer user ID / key
    userName TEXT NOT NULL,                            -- Login username
    passwordHash BLOB NOT NULL,                        -- Hashed password (bytes in python)
    isAdmin BOOLEAN NOT NULL,                          -- If user is admin or not. Ignore if not implementing admin
    creationTime INTEGER NOT NULL,                     -- Time user was created
    lastVisit INTEGER NOT NULL                         -- Users last visit, for showing new content when they return
);

--Topic table--
DROP TABLE IF EXISTS topic;
CREATE TABLE topic (
    topicID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,  -- Topic's ID number
    topicName TEXT NOT NULL,                            -- Topic's text
    postingUser INTEGER REFERENCES "user"(userID) ON DELETE SET NULL ON UPDATE CASCADE, -- FK (foreign key) of posting user
    creationTime INTEGER NOT NULL,                      -- Time topic was created
    updateTime INTEGER NOT NULL                         -- Last time a claim/reply was added
);

-- Claim table
DROP TABLE IF EXISTS claim;
CREATE TABLE claim (
    claimID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,  -- Claim ID number
    topic INTEGER NOT NULL REFERENCES topic(topicID) ON DELETE CASCADE ON UPDATE CASCADE, -- FK of topic
    postingUser INTEGER REFERENCES "user"(userID) ON DELETE SET NULL ON UPDATE CASCADE, -- FK of posting user
    creationTime INTEGER NOT NULL,                      -- Time claim was created
    updateTime INTEGER NOT NULL,                        -- Last time a reply was added
    text TEXT NOT NULL                                  -- Actual text
);

-- Claim relationship types
DROP TABLE IF EXISTS claimToClaimType;
CREATE TABLE claimToClaimType (
    claimRelTypeID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    claimRelType TEXT NOT NULL
);
INSERT INTO claimToClaimType (claimRelTypeID, claimRelType) VALUES (1, 'Opposed');
INSERT INTO claimToClaimType (claimRelTypeID, claimRelType) VALUES (2, 'Equivalent');

-- Claim relationships
DROP TABLE IF EXISTS claimToClaim;
CREATE TABLE claimToClaim (
    claimRelID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,        -- Claim relationship ID
    first INTEGER NOT NULL REFERENCES claim(claimID) ON DELETE CASCADE ON UPDATE CASCADE, -- FK of first related claim
    second INTEGER NOT NULL REFERENCES claim(claimID) ON DELETE CASCADE ON UPDATE CASCADE, -- FK of second related claim
    claimRelType INTEGER NOT NULL REFERENCES claimToClaimType(claimRelTypeID) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT claimToClaimUnique UNIQUE (first, second)         -- Ensure unique relationships
);

-- Reply text table
DROP TABLE IF EXISTS replyText;
CREATE TABLE replyText (
    replyTextID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,      -- Reply ID
    postingUser INTEGER REFERENCES "user"(userID) ON DELETE SET NULL ON UPDATE CASCADE, -- FK of posting user
    creationTime INTEGER NOT NULL,                               -- Posting time
    text TEXT NOT NULL                                           -- Text of reply
);

-- Reply to claim types
DROP TABLE IF EXISTS replyToClaimType;
CREATE TABLE replyToClaimType (
    claimReplyTypeID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    claimReplyType TEXT NOT NULL
);
INSERT INTO replyToClaimType (claimReplyTypeID, claimReplyType) VALUES (1, 'Clarification');
INSERT INTO replyToClaimType (claimReplyTypeID, claimReplyType) VALUES (2, 'Supporting Argument');
INSERT INTO replyToClaimType (claimReplyTypeID, claimReplyType) VALUES (3, 'Counterargument');

-- Reply to claim relationships
DROP TABLE IF EXISTS replyToClaim;
CREATE TABLE replyToClaim (
    replyToClaimID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,                                       -- Relationship ID
    reply INTEGER NOT NULL REFERENCES replyText (replyTextID) ON DELETE CASCADE ON UPDATE CASCADE,   -- FK of related reply
    claim INTEGER NOT NULL REFERENCES claim (claimID) ON DELETE CASCADE ON UPDATE CASCADE,           -- FK of related claim
    replyToClaimRelType INTEGER NOT NULL REFERENCES replyToClaimType(claimReplyTypeID) ON DELETE CASCADE ON UPDATE CASCADE -- FK of relation type
);

-- Reply to reply types
DROP TABLE IF EXISTS replyToReplyType;
CREATE TABLE replyToReplyType (
    replyReplyTypeID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    replyReplyType TEXT NOT NULL
);
INSERT INTO replyToReplyType (replyReplyTypeID, replyReplyType) VALUES (1, 'Evidence');
INSERT INTO replyToReplyType (replyReplyTypeID, replyReplyType) VALUES (2, 'Support');
INSERT INTO replyToReplyType (replyReplyTypeID, replyReplyType) VALUES (3, 'Rebuttal');

-- Reply to reply relationships
DROP TABLE IF EXISTS replyToReply;
CREATE TABLE replyToReply (
    replyToReplyID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,                                     -- Relationship ID
    reply INTEGER NOT NULL REFERENCES replyText(replyTextID) ON DELETE CASCADE ON UPDATE CASCADE, -- FK of reply
    parent INTEGER NOT NULL REFERENCES replyText(replyTextID) ON DELETE CASCADE ON UPDATE CASCADE,-- FK of parent reply
    replyToReplyRelType INTEGER NOT NULL REFERENCES replyToReplyType(replyReplyTypeID) ON DELETE CASCADE ON UPDATE CASCADE -- FK of relation type
);
