# Eneru Application

Eneru Application is a web platform that provides access to various sub-applications tailored to meet different use cases based on user needs. This application integrates functionalities such as Optical Character Recognition (OCR), name generation, mind mapping, and more.

## Features

- **OCR App**: Upload images and PDFs to extract text using advanced OCR technology.
- **Name Generator**: Generate unique names based on specified criteria.
- **Mind Map**: Create visual representations of ideas and concepts.
- **Chatbot**: Interact with an AI-powered chatbot for assistance and queries.

## Installation

To set up the Eneru Application locally, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/Anudeep28/Eneru_Application.git
   cd Eneru_Application
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv myenv
   myenv\Scripts\activate  # On Windows
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Create a `.env` file in the root directory and add the necessary configurations (refer to the example in `.env.example`).

5. Run database migrations:
   ```bash
   python manage.py migrate
   ```

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Usage

- Access the application by navigating to `http://127.0.0.1:8000` in your web browser.
- Use the navigation bar to access different sub-applications.

## Contributing

Contributions are welcome! Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit them (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the Django community for their excellent framework.
- Special thanks to all contributors and users for their support and feedback.
