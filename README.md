# TowneCodex

TowneCodex is a Python application for managing a growing D&D 5e item database.  
It provides tools for searching, filtering, adding, editing, deleting, and exporting entries.  
The system includes scrapers for Reddit and D&D Beyond to automatically import homebrew and official items, and it generates structured HTML documents for reference and printing.

---

## Features

- **Database Management**  
  - Add, edit, and delete items  
  - Search and filter by name, type, rarity, and attunement  
  - Export items to CSV  

- **Scrapers**  
  - Import items from Reddit posts (e.g., *The Griffon’s Saddlebag*)  
  - Import items from D&D Beyond  
  - Automated parsing of title, rarity, attunement, description, and image  

- **Output Generation**  
  - Generate structured HTML documents for item sets  
  - Designed for clean formatting, easy reference, and printing  

- **Design**  
  - Clean abstractions for scrapers, queries, and storage  
  - Scalable architecture for thousands of entries  

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ColeMcGregor/TowneCodex.git
   cd TowneCodex
