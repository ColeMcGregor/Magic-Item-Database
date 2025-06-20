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
INSERT INTO CommonCons(name, price, amount) VALUES('Elixir of Vigilance', '200', '1');
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
INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Bottled Talent', '100', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Oozo Potion', '100', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Potion of Natures Growth', '400', '1');
INSERT INTO CommonCons(name, price, amount) VALUES('Rejuvenating Draft','175','1');
INSERT INTO CommonCons(name, price, amount) VALUES('Snake Oil', '500', '1');

SELECT cc1.name,
       cc1.price
FROM   CommonCons AS cc1
	WHERE  cc1.itemID = (
	   SELECT MIN(cc2.itemID)
	   FROM   CommonCons AS cc2
	   WHERE  cc2.name = cc1.name
);


CREATE TABLE "Drinks" (
	"itemID"	INTEGER UNIQUE,
	"name"	TEXT NOT NULL,
	"price"	INTEGER,
	PRIMARY KEY("itemID" AUTOINCREMENT)
);

INSERT INTO Drinks(name, price) VALUES('Celestial Sunrise', '200');
INSERT INTO Drinks(name, price) VALUES('Shifters Shine', '75');
INSERT INTO Drinks(name, price) VALUES('Aged Goodberry Wine', '1000');
INSERT INTO Drinks(name, price) VALUES('Bloody Marilith', '75');
INSERT INTO Drinks(name, price) VALUES('Djinn and Tonic', '20');
INSERT INTO Drinks(name, price) VALUES('Orostead Iced Tea', '25');
INSERT INTO Drinks(name, price) VALUES('Wispy Sour', '30');
INSERT INTO Drinks(name, price) VALUES('Chi-Balancing Tea', '150');


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
INSERT INTO CommonItem(name, price, attune) VALUES('Amulet of the Pleasing Bouquet', '50', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Anthology of Enhanced Radiance', '50', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Archaic Creed', '60', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Atlas to Libation', '35', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Birdsong Whistle', '85', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Borrowers Bookmark', '40', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Cage of Folly', '75', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Compendium of Many Colors', '60', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Contract of Indentured Service', '150', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Draconic Diorama', '45', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Enchanted Music Sheet', '55', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Essay on Efficient Armor Management', '80', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Explorers Chalk', '95', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Fan of Whispering', '25', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Fathomers Ring', '85', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Finder Gremlin', '20', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Flask of Inebriation', '90', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Fools Hat', '60', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Glowing Body Paint', '15', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Harlequins Cards', '40', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Hat of Grand Entrances', '40', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Humour Realignment Transfiguration', '30', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Inkpot of the Thrifty Apprentice', '75', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Legerdemain Gloves', '95', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Letter-Lift Paper', '40', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Library Scarf', '50', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Lockpicks of Memory', '150', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Marble of Direction', '50', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Mask of Anonymity', '80', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Matemal Cameo', '90', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Message Whistle', '95', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Midnight Pearls', '95', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Mug of Warming', '50', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Oil of Cosmetic Enhancement', '50', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Opera-Goers Guise', '95', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Organizer Gremline', '90', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Perdita Ravenwings True Name', '90', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Preserved Imps Head', '35', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Prismatic Gown', '90', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Quick Canoe Paddle', '75', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Sack of Sacks', '55', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Scrap of Forbidden Text', '20', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Security Gremlin', '100', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Shoulder Dragon Brooch', '90', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Signal Rings', '60', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Sinners Ashes', '35', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Snake-Eye Bones', '55', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Tailored Suit of Armor', '80', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Timekeeper Gremlin', '50', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Tome of the Endless Tale', '50', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Tools of the Hidden Hand', '30', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('True Weight Gloved', '50', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Unliving Rune', '75', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Wand of the Scribe', '75', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Waystone', '50', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Wig of Styling', '15', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Wood Woad Amulet', '100', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Zlicks Message Cushion', '40', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Freerunners Leather Armor', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('', '0', 'N');


CREATE TABLE "UncommonItem" (
	"itemID"	INTEGER UNIQUE,
	"name"	TEXT NOT NULL,
	"price"	INTEGER,
	"attune"	TEXT NOT NULL,
	PRIMARY KEY("itemID" AUTOINCREMENT),
	CHECK("attune" IN ('Y', 'N'))
);