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

INSERT INTO CommonItem(name, price, attune) VALUES('Breastplate of Gleaming', '150', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Half Plate of Gleaming', '200', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Hauberk of Gleaming', '150', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Splint of Gleaming', '200', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Platemail of Gleaming', '400', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Boots of False Tricks', '60', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Candle of the Deep', '40', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Charlatans Die', '100', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Cloak of Billowing', '30', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Cloak of Many Fashions', '40', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Clockwork Amulet', '150', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Clothes of Mending', '30', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Dark Shard Amulet', '150', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Dread Helm', '75', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Ear Horn of Hearing', '50', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Enduring Spellbook', '100', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Ersatz Eye', '50', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Hat of Vermin', '100', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Hat of Wizardry', '150', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Hewards Handy Spice Pouch', '100', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Horn of Silent Alarm', '75', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Instrument of Illusions', '40', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Instrument of Scribing', '40', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Lock of Tickery', '30', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Moon-Touched Shortsword', '40', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Moon-Touched Longsword', '75', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Moon-Touched Rapier', '100', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Moon-Touched Greatsword', '150', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Mystery Key', '25', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Orb of Direction', '25', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Orb of Time', '20', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Perfume of Bewitching', '50', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Pipe of Smoke Monsters', '20', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Pole of Angling', '30', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Pole of Collapsing', '20', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Pot of Awakening', '20', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Rope of Mending', '35', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Ruby of the War Mage', '75', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Medium Shield of Expression', '75', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Heavy Shield of Expression', '100', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Staff of Adornment', '40', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Staff of Birdcalls', '50', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Staff of Flowers', '40', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Talking Doll', '20', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Tankard of Sobriety', '20', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Unbreakable Arrow', '10', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Veterans Cane', '45', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Wand of Conducting', '40', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Wand of Pyrotechnics', '75', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Wand of Scowls', '50', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Wand of Smiles', '50', 'N');



CREATE TABLE "UncommonItem" (
	"itemID"	INTEGER UNIQUE,
	"name"	TEXT NOT NULL,
	"price"	INTEGER,
	"attune"	TEXT NOT NULL,
	PRIMARY KEY("itemID" AUTOINCREMENT),
	CHECK("attune" IN ('Y', 'N'))
);