# cs50-finance
Web application to lookup, buy and sell stocks
Developed as part of **CS50 2025**.

## Description

CS50 Finance allows users to:  
- Register and log in  
- Check real-time stock prices  
- Buy and sell stocks  
- View their portfolio and transaction history  

The project focuses on full-stack web development, database management, and application logic in Python.

## Technologies and Languages

- **Python 3**: Core application logic and backend  
- **Flask**: Web framework for routing, forms, and session management  
- **HTML / CSS / Bootstrap**: User interface and responsive design  
- **JavaScript**: Interactive frontend features  
- **SQL / SQLite**: Database creation and management  

## Databases

Several databases were created and integrated to support different functionalities:

1. **Users**: Stores registration info, hashed passwords, and initial cash balance.  
2. **Stocks**: Keeps track of stock holdings per user, including price and quantity.  
3. **History**: Logs all transactions with type, quantity, price, and user reference.  

These tables enable managing portfolios, calculating balances, and generating transaction history efficiently and securely.

## Installation and Running

Clone the repository:

git clone https://github.com/yourusername/cs50-finance.git
cd cs50-finance

Install dependencies:

pip install -r requirements.txt

Run the application:

flask run

Open in browser:

http://127.0.0.1:5000/

## Additional Features

User input validation

Error handling for buying/selling stocks

Real-time balance and price calculations

## Contributions

Individual project completed as part of CS50 2025.
