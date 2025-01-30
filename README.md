<<<<<<< HEAD
# NewsNepal

NewsNepal is a Django-based news aggregator that collects and displays news from various Nepali news sources in real-time. The application supports both English and Nepali languages, offering a seamless bilingual news experience.

## Features

- **Real-time News Aggregation**: Automatically fetches news from multiple Nepali news sources
- **Bilingual Support**: Toggle between English and Nepali languages
- **Category Filtering**: Filter news by categories:
=======
# NewsNepal - Nepali News Aggregator

A modern Django-based news aggregator that collects and displays news from major Nepali news portals in both English and Nepali languages.

## Features

- **Bilingual Support**: 
  - Toggle between English (EN) and Nepali (NP)
  - Interface elements and content in both languages

- **News Categories**:
>>>>>>> Prototype 2
  - Politics
  - Business
  - Technology
  - Sports
  - Entertainment
  - Health
<<<<<<< HEAD
  - World
  - Society
- **Dark/Light Mode**: User-friendly interface with theme options
- **Bookmark System**: Save and manage favorite articles
- **Search Functionality**: Search across all news articles
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Auto-refresh**: Regular updates to keep news current
=======
  - Education
  - World
  - Lifestyle

- **User Experience**:
  - Dark/Light Mode Toggle
  - Bookmark Favorite Articles
  - Search Functionality
  - Category Filtering
  - Load More Articles
  - Responsive Design
>>>>>>> Prototype 2

## News Sources

- English Online Khabar
- Setopati
- Ratopati
- Kathmandu Post
- Nagarik News

<<<<<<< HEAD
## Technologies Used

- **Backend**:
  - Django 5.0.2
  - Python 3.x
  - BeautifulSoup4
  - Newspaper3k
  - Requests

- **Frontend**:
  - HTML5/CSS3
  - JavaScript/jQuery
  - Font Awesome
  - Google Fonts

## Setup and Installation
1. Clone the repository:
bash
git clone https://github.com/arjun28-ach/NewsNepal.git
cd NewsNepal

2. Create and activate virtual environment:
bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

3. Install required packages:
 bash
pip install -r requirements.txt


4. Run migrations:
bash
python manage.py migrate



5. Start the development server:
bash
python manage.py runserver


6. Visit `http://127.0.0.1:8000` in your browser

## Usage

- **Language Switch**: Click the language button (EN/NP) to toggle between English and Nepali
- **Dark Mode**: Use the moon/sun icon to switch between dark and light themes
- **Bookmarks**: 
  - Click the bookmark icon on any article to save it
  - Access saved articles through the bookmark button in the navbar
- **Categories**: Use the category buttons to filter news by topic
- **Search**: Use the search bar to find specific news articles
=======
## Tech Stack

### Backend
- Django 5.0.2
- Python 3.x
- BeautifulSoup4
- Newspaper3k
- Requests
- PyTZ

### Frontend
- HTML5/CSS3
- JavaScript/jQuery
- Font Awesome Icons
- Google Fonts (Poppins)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/NewsNepal.git
cd NewsNepal
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start development server:
```bash
python manage.py runserver
```

6. Visit `http://127.0.0.1:8000` in your browser

## Project Structure

```
NewsNepal/
├── news/
│   ├── templates/
│   │   └── news/
│   │       └── home.html
│   ├── scraper.py
│   ├── urls.py
│   └── views.py
├── newsnepal/
│   └── settings.py
├── .gitignore
├── requirements.txt
└── README.md
```

## Features in Detail

### News Scraping
- Concurrent fetching from multiple sources
- Category-based article classification
- Automatic language detection
- Image and summary extraction
- Caching system for performance

### User Interface
- Clean, modern design
- Responsive grid layout
- Smooth animations
- Intuitive navigation
- Cross-browser compatibility

### Bookmarking System
- Local storage for bookmarks
- Add/remove functionality
- Persistent across sessions
- Quick access through navbar
>>>>>>> Prototype 2

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

<<<<<<< HEAD
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

Arjun Acharya - [@arjun28_ach](https://github.com/arjun28-ach)

Project Link: [https://github.com/arjun28-ach/NewsNepal](https://github.com/arjun28-ach/NewsNepal)

## Acknowledgments

- News content is sourced from various Nepali news websites
- Thanks to all the news providers for their RSS feeds and content
- Special thanks to the Django and Python communities for their excellent documentation
  

=======
This project is licensed under the MIT License.

## Acknowledgments

- News content is sourced from various Nepali news portals
- Thanks to all the news providers
- Built with Django and modern web technologies
>>>>>>> Prototype 2
