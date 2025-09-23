CREATE TABLE "VRareCons" (
	"itemID"	INTEGER UNIQUE,
	"name"	TEXT NOT NULL,
	"price"	INTEGER,
	"amount"	INTEGER,
	PRIMARY KEY("itemID" AUTOINCREMENT)
);


INSERT INTO VRareCons(name, price, amount) VALUES('Potion of Greater Healing', '200', '8');
INSERT INTO VRareCons(name, price, amount) VALUES('Potion of Superior Healing', '800', '3');
INSERT INTO VRareCons(name, price, amount) VALUES('Potion of Superior Healing', '800', '3');
INSERT INTO VRareCons(name, price, amount) VALUES('Potion of Superior Healing', '800', '5');
INSERT INTO VRareCons(name, price, amount) VALUES('Potion of Supreme Healing', '1500', '2');
INSERT INTO VRareCons(name, price, amount) VALUES('Potion of Supreme Healing', '1500', '1');
INSERT INTO VRareCons(name, price, amount) VALUES('Arrow of True Slaying', '500', '2');
INSERT INTO VRareCons(name, price, amount) VALUES('Arrow of True Slaying', '500', '3');
INSERT INTO VRareCons(name, price, amount) VALUES('Smokepowder Arrow', '750', '2');
INSERT INTO RareCons(name, price, amount) VALUES('Oil of Etherealness', '2000', '1');
INSERT INTO RareCons(name, price, amount) VALUES('Vial of Deadly Poison', '750', '2');
INSERT INTO VRareCons(name, price, amount) VALUES('Vial of Deadly Poison', '750', '3');
INSERT INTO VRareCons(name, price, amount) VALUES('Vial of Deadly Poison', '750', '4');
INSERT INTO VRareCons(name, price, amount) VALUES('Vial of Purple Worm Toxin', '1000', '2');
INSERT INTO VRareCons(name, price, amount) VALUES('Flashblinder', '1750', '1');
INSERT INTO VRareCons(name, price, amount) VALUES('Runepowder Vial', '3000', '1');
INSERT INTO VRareCons(name, price, amount) VALUES('Elixir of Liquid Luck', '3000', '1');
INSERT INTO VRareCons(name, price, amount) VALUES('Elixir of the Colossus', '4000', '1');
INSERT INTO VRareCons(name, price, amount) VALUES('Elixir of Superior Mana', '1000', '2');
INSERT INTO VRareCons(name, price, amount) VALUES('Elixir of Superior Mana', '1000', '3');
INSERT INTO VRareCons(name, price, amount) VALUES('Elixir of Supreme Mana', '2000', '1');
INSERT INTO VRareCons(name, price, amount) VALUES('Potion of Angelic Slumber', '5000', '1');
INSERT INTO VRareCons(name, price, amount) VALUES('Potion of Invulnerability', '4000', '1');
INSERT INTO VRareCons(name, price, amount) VALUES('Potion of Invulnerability', '4000', '2');
INSERT INTO VRareCons(name, price, amount) VALUES('Potion of Fire Giant Strength', '1500', '1');
INSERT INTO VRareCons(name, price, amount) VALUES('Potion of Fire Giant Strength', '1500', '2');
INSERT INTO VRareCons(name, price, amount) VALUES('Potion of Cloud Giant Strength', '3000', '1');
INSERT INTO VRareCons(name, price, amount) VALUES('Potion of Storm Giant Strength', '5000', '1');
INSERT INTO VRareCons(name, price, amount) VALUES('Potion of Longevity', '3000', '1');
INSERT INTO VRareCons(name, price, amount) VALUES('Necklace of Fireballs', '6000', '1');
INSERT INTO VRareCons(name, price, amount) VALUES('Bead of Force', '1250', '2');
INSERT INTO VRareCons(name, price, amount) VALUES('Bead of Force', '1250', '3');
INSERT INTO VRareCons(name, price, amount) VALUES('Sovereign Glue', '1500', '2');
INSERT INTO VRareCons(name, price, amount) VALUES('Universal Solvent', '1000', '2');
INSERT INTO VRareCons(name, price, amount) VALUES('Reincarnation Dust', '4000', '1');
INSERT INTO VRareCons(name, price, amount) VALUES('Marvelous Pigments', '2000', '1');
INSERT INTO VRareCons(name, price, amount) VALUES('Candle of Invocation', '10000', '1');
INSERT INTO VRareCons(name, price, amount) VALUES('Spell Scroll (6th Level)', '1500', '2');
INSERT INTO VRareCons(name, price, amount) VALUES('Spell Scroll (6th Level)', '1500', '3');
INSERT INTO VRareCons(name, price, amount) VALUES('Spell Scroll (7th Level)', '3000', '2');
INSERT INTO VRareCons(name, price, amount) VALUES('Spell Scroll (8th Level)', '5000', '1');
INSERT INTO VRareCons(name, price, amount) VALUES('Spell Scroll (9th Level)', '10000', '1');
INSERT INTO VRareCons(name, price, amount) VALUES('Supreme Rejuvenating Draft', '4000', '1');


CREATE TABLE "VRareItem" (
	"itemID"	INTEGER UNIQUE,
	"name"	TEXT NOT NULL,
	"price"	INTEGER,
	"attune"	TEXT NOT NULL,
	PRIMARY KEY("itemID" AUTOINCREMENT),
	CHECK("attune" IN ('Y', 'N'))
);
