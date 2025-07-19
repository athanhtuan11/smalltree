# Nursery Website

Welcome to the Nursery Website project! This project is a simple Flask web application designed for a nursery, providing information about classes, a gallery, and contact options for parents.

## Project Structure

```
nursery-website
├── app
│   ├── __init__.py
│   ├── routes.py
│   ├── models.py
│   ├── forms.py
│   ├── static
│   │   ├── css
│   │   │   └── style.css
│   │   └── js
│   │       └── main.js
│   └── templates
│       ├── base.html
│       ├── index.html
│       ├── about.html
│       ├── classes.html
│       ├── gallery.html
│       └── contact.html
├── config.py
├── requirements.txt
├── run.py
└── README.md
```

## Features

- **Home Page**: An overview of the nursery and its mission.
- **About Page**: Information about the nursery, its staff, and philosophy.
- **Classes Page**: Details about the different classes offered for children.
- **Gallery Page**: A collection of images showcasing activities and events at the nursery.
- **Contact Page**: A form for parents to reach out with inquiries.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/nursery-website.git
   cd nursery-website
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Configure the application settings in `config.py` as needed.

## Running the Application

To run the application, execute the following command:
```
python run.py
```

The application will start on `http://127.0.0.1:5000/`.

## Contributing

Feel free to submit issues or pull requests if you have suggestions or improvements for the project.

## License

This project is licensed under the MIT License. See the LICENSE file for details.