# Eneru Application

Modern web platform integrating multiple Django applications for financial analysis, AI services, and business management tools.

## Featured Applications

- **Financial Analyzer**: Stock market analysis and portfolio management
- **Chatbot**: AI-powered conversational interface
- **Chitfund Manager**: Chit fund administration
- **Food Recognition**: Image-based food identification
- **OCR App**: Document text extraction
- **Transcribe App**: Audio-to-text conversion
- **Legal Assistant**: Contract analysis
- **Name Generator**: Generate unique names based on specified criteria.
- **Mind Map**: Create visual representations of ideas and concepts.

## Tech Stack

- Django 4.2
- PostgreSQL
- PyTorch
- Tesseract OCR
- Django REST Framework

## Installation

To set up the Eneru Application locally, follow these steps:

```bash
# Clone & setup
gh repo clone Anudeep28/Eneru_Application
cd Eneru_Application
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

## Environment Variables

Create a `.env` file with these required API keys:

```ini
# Gemini AI (Chatbot & Financial Analysis)
GEMINI_API_KEY=your_gemini_key

# Together API (LLM Services)
TOGETHER_API_KEY=your_together_key
```

Get your keys:
- [Gemini API](https://ai.google.dev/) - Google AI Studio
- [Together API](https://api.together.xyz/) - Together AI Platform

## Model Files
The food recognition model file (`indian_food_model_v3.pth`) is too large for GitHub. You can download it from:
1. [Google Drive Link] - Coming soon
2. Or contact the repository owner for access

After downloading, place the model file in:
```
food_app/models/indian_food_model_v3.pth
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
