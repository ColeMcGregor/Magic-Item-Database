CREATE TABLE "LegendItem" (
	"itemID"	INTEGER UNIQUE,
	"name"	TEXT NOT NULL,
	"price"	INTEGER,
	"attune"	TEXT NOT NULL,
	PRIMARY KEY("itemID" AUTOINCREMENT),
	CHECK("attune" IN ('Y', 'N'))
);

