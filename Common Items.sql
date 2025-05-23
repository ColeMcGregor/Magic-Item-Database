CREATE TABLE "CommonCons" (
	"itemID"	INTEGER UNIQUE,
	"name"	TEXT NOT NULL,
	"price"	INTEGER,
	"amount"	INTEGER,
	PRIMARY KEY("itemID" AUTOINCREMENT)
);

SELECT name, price, amount
FROM   CommonCons
ORDER  BY RANDOM()
LIMIT 10; 


INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Healing', '50', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Healing', '50', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Healing', '50', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Healing', '50', '4');
INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Healing', '50', '4');
INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Healing', '50', '4');
INSERT INTO CommonCons(name, price, amount) VALUES('Arrow of Acid', '25', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Arrow of Acid', '25', '3');
INSERT INTO CommonCons(name, price, amount) VALUES('Arrow of Fire', '25', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Arrow of Fire', '25', '3');
INSERT INTO CommonCons(name, price, amount) VALUES('Arrow of Ice', '25', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Arrow of Ice', '25', '3');;
INSERT INTO CommonCons(name, price, amount) VALUES('Arrow of Lightning', '25', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Arrow of Lightning', '25', '3');
INSERT INTO CommonCons(name, price, amount) VALUES('Arrow of Slaying', '20', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Arrow of Slaying', '20', '3');
INSERT INTO CommonCons(name, price, amount) VALUES('Arrow of Slaying', '20', '4');
INSERT INTO CommonCons(name, price, amount) VALUES('Arrow of Punching', '30', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Arrow of Punching', '30', '3');
INSERT INTO CommonCons(name, price, amount) VALUES('Arrow of Darkness', '75', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Arrow of Ilmater', '50', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Arrow of Roaring Thunder', '75', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Dust of Disappearance', '350', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Dust of Tracelessness', '250', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Oil of Slipperiness', '250', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Oil of Sharpness', '500', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Oil of Accuracy', '150', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Oil of Bane', '300', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Oil of Freezing', '400', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Wizardsbane Oil', '350', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Vial of Basic Poison', '25', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Vial of Basic Poison', '25', '3');
INSERT INTO CommonCons(name, price, amount) VALUES('Vial of Advanced Poison', '75', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Vial of Advanced Poison', '75', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Alchemists Fire', '75', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Alchemists Fire', '75', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Skull Liquer', '150', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Medicinal Salve', '75', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Medicinal Salve', '75', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Elixir of Mana', '75', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Elixir of Mana', '75', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Elixir of Bloodlust', '500', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Elixir of Peerless Focus', '250', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Elixir of Barkskin', '400', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Elixir of Vigilance', '200', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Elixir of Darkvision', '200', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Climbing', '75', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Glorious Vaulting', '100', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Water Breathing', '100', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Fire Breath', '250', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Animal Friendship', '75', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Resistance', '500', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Hill Giant Strength', '125', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Growth', '400', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Mind Reading', '400', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Gaseous Form', '500', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Remedial Potion', '250', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Greater Healing', '200', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Greater Healing', '200', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Spell Scroll (Cantrip)', '20', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Spell Scroll (Cantrip)', '20', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Spell Scroll (1st Level)', '50', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Spell Scroll (1st Level)', '50', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Spell Scroll (1st Level)', '50', '3');
INSERT INTO CommonCons(name, price, amount) VALUES('Spell Scroll (2nd Level)', '100', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Spell Scroll (2nd Level)', '100', '2');
INSERT INTO CommonCons(name, price, amount) VALUES('Spell Scroll (3rd Level)', '200', '1');



CREATE TABLE "CommonItem" (
	"itemID"	INTEGER UNIQUE,
	"name"	TEXT NOT NULL,
	"price"	INTEGER,
	"attune"	INTEGER NOT NULL,
	PRIMARY KEY("itemID" AUTOINCREMENT),
	CHECK(attune IN ('Y','N'))
);


CREATE TABLE "UncommonItem" (
	"itemID"	INTEGER UNIQUE,
	"name"	TEXT NOT NULL,
	"price"	INTEGER,
	"attune"	TEXT NOT NULL,
	PRIMARY KEY("itemID" AUTOINCREMENT),
	CHECK("attune" IN ('Y', 'N'))
);