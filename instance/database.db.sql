BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "role" (
	"id"	INTEGER NOT NULL,
	"name"	VARCHAR(25),
	UNIQUE("name"),
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "account" (
	"id"	INTEGER NOT NULL,
	"balance"	INTEGER,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "transactions" (
	"id"	INTEGER NOT NULL,
	"sequence"	INTEGER,
	"from_account_id"	INTEGER,
	"dateTime"	DATETIME,
	"to_account_id"	INTEGER,
	"amount"	INTEGER,
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "user" (
	"id"	INTEGER NOT NULL,
	"email"	VARCHAR(150),
	"password"	VARCHAR(255),
	"first_name"	VARCHAR(25),
	"role_id"	INTEGER,
	"role_approved"	BOOLEAN,
	"role_request"	BOOLEAN,
	"role_requested_on"	DATETIME,
	FOREIGN KEY("role_id") REFERENCES "role"("id"),
	PRIMARY KEY("id")
);
CREATE TABLE IF NOT EXISTS "teacher_request_history" (
	"id"	INTEGER NOT NULL,
	"user_id"	INTEGER NOT NULL,
	"status"	VARCHAR(20) NOT NULL,
	"date_resolved"	DATETIME,
	"resolved_by_id"	INTEGER,
	FOREIGN KEY("resolved_by_id") REFERENCES "user"("id"),
	FOREIGN KEY("user_id") REFERENCES "user"("id"),
	PRIMARY KEY("id")
);
INSERT INTO "role" VALUES (1,'admin');
INSERT INTO "role" VALUES (2,'teacher');
INSERT INTO "role" VALUES (3,'student');
INSERT INTO "user" VALUES (1,'admin@Kimberley.com','sha256$UPfTbq0678E7zFPi$be09ab4f5aff75d691d9495715b9d3e889e2b2b5ab4498016e16220a47389d09','Admin',1,0,0,NULL);
INSERT INTO "user" VALUES (2,'rosss9238@gmail.com','sha256$OYBgGywA9mZJed6h$dfecebcf65cd8300c3a89eec539efbde43443cc5bf40c2a6b051bf68949f629d','sam',2,1,0,'2023-03-09 09:05:28.084653');
INSERT INTO "user" VALUES (3,'rosss9237@gmail.com','sha256$v0dp5ICAWU5GhzuY$176740437efe2e63ea97edd957026558cdd938034ea0bdc25e01e77ac34e9416','sam',2,1,0,'2023-03-09 09:05:50.044032');
INSERT INTO "user" VALUES (4,'rosss9236@gmail.com','sha256$W3wPVzTcsVkHpMax$e14aba70b88345c9ac00edb3b186d0f5ad441ac36d0061ecba7bd66f98c58350','sam',3,0,0,'2023-03-09 09:06:25.953355');
INSERT INTO "teacher_request_history" VALUES (1,2,'Pending',NULL,NULL);
INSERT INTO "teacher_request_history" VALUES (2,3,'Pending',NULL,NULL);
INSERT INTO "teacher_request_history" VALUES (3,2,'accepted','2023-03-09 09:06:40.717348',1);
INSERT INTO "teacher_request_history" VALUES (4,3,'rejected','2023-03-09 09:06:42.186698',1);
INSERT INTO "teacher_request_history" VALUES (5,3,'rejected','2023-03-09 09:06:43.089338',1);
INSERT INTO "teacher_request_history" VALUES (6,3,'rejected','2023-03-09 09:06:43.642116',1);
INSERT INTO "teacher_request_history" VALUES (7,3,'rejected','2023-03-09 09:06:44.106829',1);
INSERT INTO "teacher_request_history" VALUES (8,3,'rejected','2023-03-09 09:06:44.568605',1);
INSERT INTO "teacher_request_history" VALUES (9,3,'rejected','2023-03-09 09:06:44.872519',1);
INSERT INTO "teacher_request_history" VALUES (10,3,'rejected','2023-03-09 09:06:45.593714',1);
INSERT INTO "teacher_request_history" VALUES (11,3,'rejected','2023-03-09 09:07:02.128913',1);
INSERT INTO "teacher_request_history" VALUES (12,3,'accepted','2023-03-09 09:07:05.187404',1);
CREATE UNIQUE INDEX IF NOT EXISTS "ix_user_email" ON "user" (
	"email"
);
COMMIT;
