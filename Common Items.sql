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
	)
ORDER BY cc1.name ASC;


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
INSERT INTO CommonItem(name, price, attune) VALUES('Bulletin Buckler', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Sun and Moon Shield', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Dealmaker''s Ring', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Doodle Ring', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Pair of Tiny Violin Rings', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Ring of Gestures', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Ring of Names', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Ring of Perching', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Ring of Roses', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Ring of Silverware', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Ring of the Candle Keeper', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Ring of the Distant Digit', '0', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Ring of the Fowl Sentinel', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Ring of the Printless', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Rings of the Secret Scribe', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Status Signets', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Vial Ring', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Instigator''s Rod', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Periscope Rod', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Worker''s Wondrous Ladder', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Hedgewitch''s Gardening Cane', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Stalwart Staff', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Borbos Joyous Wand of Color', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Cherry Blossom Wand', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Wand of Bubbles', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Wand of Torchlight', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Bird''s-Eye Bolt', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Fanfare Ammunition', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Scarring Axe', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Bonfire Blade', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Weapon of Showmanship', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Torpedo Arrow', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Rope Caster', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Intrepid Knife', '0', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Hammer of Nails', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Redsmith Hammer', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Campers Crutch', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Silver Star Cane', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Light Sling', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Alcoholock', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Aurora Dust', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Bag of Bellstones', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Ball of Wild Earth', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Bands of the Found and Lost', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Bard in a Box', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Bell of Alarm', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Belltower Triangle', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Bird of a Feather', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Bonfire Candle', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Bonfire Charm', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Book of Instant Copying', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Borbos''s Marvelous Magic Marker', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Bubble Collar', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Bullfrog Totem', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Candleflame Helm', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Candy Xorn', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Catnip Amulet', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Cleaning Cube', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Cloth of Instant Tables', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Companions Band', '0', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Container of Heat and Frost', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Copyquill', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Diorama Die', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Dress of Many Pockets', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Drowner''s Pearl', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Dryadleaf', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Everlasting Sugarbomb', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Featherwumpus', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Firecracker Crystals', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Forecaster''s Cloak', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Fortune''s Flower', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Foxfire Charm', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Frefil''s Scrummy Trifection', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Freshwater Pitcher', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Gardener''s Candle Holder', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Grasping Seedling Necklace', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Grass Carpet', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Gravity Goblet', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Greenthumb Whittler', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Griffon Coinpouch', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Griffon Key Loop', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Headband of the Sweatless', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Heart of the Sleeveless', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Immovable Button', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Inker''s Armband', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Journal of Dreams', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Leatherbeard', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Living Wig', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Magnificent Pocket Vanity', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Mask of the Crocodile', '0', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Merry Berry', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Mimic''s Smilemaker', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Miraculous Bread Box', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Neutralizing Spray', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Oaken Candle', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Orators Quill', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Orb of Remembrance', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Owl Helm', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Owlbear Snugglebeast', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Patch of the Mallard', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Patch of the Open Eye', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Patch of the Pail', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Patch of the Tome', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Performers Puppet', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Permanent Parchment', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Phantom Walkers', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Pipe of Delicious Smells', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Pollen Pipe', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Poltergeist Candle Holder', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Pomade of Ten Thousand Styles', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Pop-Up Business Card', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Profane Mask', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Quicksilver Clay', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Radiant Teapot', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Redsmith Carrying Pack', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Redsmith Crucible Set', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Rod of Endless Light', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Rope Cobra', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Rose Quartz Koi', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Seat Belt', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Sentry Candle', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Shapeshifters Circlet', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Shimmering Spectacles', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Shipwright''s Watch', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Silver Coin of Duvra', '0', 'Y');
INSERT INTO CommonItem(name, price, attune) VALUES('Singing Stein', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Sleepytime Sheep Stuffy', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Smash Potatoes', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Snow Rider''s Sleigh', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Snowball Mittens', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Spool of Shadow', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Stamp of Shipping', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Steps of the Trickster', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Storm Seer Lamp', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Storyteller''s Stein', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Stylists Circlet', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Tea Weird', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Tear of Gaia', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Tide Turner', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Tote of Tricky Treat Sugarbombs', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Turtle Brooch', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Uorik Juice Cup', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Vineyard Amulet', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Vox Helm', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Walking Pot', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Waterwine Goblet', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Webgrip Rucksack', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Whispergust Mote', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Widemouth Bucket', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Williwig''s Time Stopper', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Winner''s Trophy', '0', 'N');
INSERT INTO CommonItem(name, price, attune) VALUES('Wizards'' Bout Top', '0', 'N');

CREATE TABLE "UncommonItem" (
	"itemID"	INTEGER UNIQUE,
	"name"	TEXT NOT NULL,
	"price"	INTEGER,
	"attune"	TEXT NOT NULL,
	"class"		TEXT,
	PRIMARY KEY("itemID" AUTOINCREMENT),
	CHECK("attune" IN ('Y', 'N'))
);


INSERT INTO UncommonItem(name, price, attune, class) VALUES('Abjurers Gilder', '0', 'Y', 'Wizard');