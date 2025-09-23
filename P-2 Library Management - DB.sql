-- -- DROP TABLE IF EXISTS payments CASCADE;
-- -- DROP TABLE IF EXISTS b_borrowed CASCADE;
-- -- DROP TABLE IF EXISTS books CASCADE;
-- -- DROP TABLE IF EXISTS users CASCADE;
-- -- DROP TABLE IF EXISTS genres CASCADE;

-- -- USERS table****
-- CREATE TABLE users (
--     user_id SERIAL PRIMARY KEY,
--     name VARCHAR(100) NOT NULL,
--     email VARCHAR(100) UNIQUE NOT NULL,
--     role VARCHAR(20) NOT NULL CHECK (role IN ('member','librarian')),
--     created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );

-- -- GENRES table****
-- CREATE TABLE genres (
--     genre_id SERIAL PRIMARY KEY,
--     name VARCHAR(100) UNIQUE NOT NULL
-- );

-- -- BOOKS table***
-- CREATE TABLE books (
--     book_id SERIAL PRIMARY KEY,
--     title VARCHAR(200) NOT NULL,
--     author VARCHAR(200),
--     genre_id INT REFERENCES genres(genre_id) ON DELETE SET NULL,
--     row_number INT,
--     shelf_number INT,
--     is_available BOOLEAN NOT NULL DEFAULT TRUE
-- );

-- -- BORROWED table***
-- CREATE TABLE b_borrowed (
--     borrow_id SERIAL PRIMARY KEY,
--     book_id INT REFERENCES books(book_id) ON DELETE SET NULL,
--     user_id INT REFERENCES users(user_id) ON DELETE SET NULL,
--     borrow_date DATE NOT NULL,
--     due_date DATE NOT NULL,
--     return_date DATE,
--     fine NUMERIC(10,2) DEFAULT 0,
--     fine_paid BOOLEAN DEFAULT FALSE
-- );

-- -- PAYMENTS table***
-- CREATE TABLE payments (
--     payment_id SERIAL PRIMARY KEY,
--     borrow_id INT REFERENCES b_borrowed(borrow_id) ON DELETE CASCADE,
--     amount_paid NUMERIC(10,2) NOT NULL,
--     payment_date DATE DEFAULT CURRENT_DATE
-- );

-- -- INSERTING genres data***
-- INSERT INTO genres (name) VALUES
-- ('Fiction'),
-- ('Non-Fiction'),
-- ('Science'),
-- ('History'),
-- ('Fantasy'),
-- ('Mystery');

-- -- INSERT into USERS
-- INSERT INTO users (name, email, role) VALUES
-- ('Alice Librarian', 'alice.lib@gmail.com', 'librarian'),
-- ('Bob Reader', 'bob.reads@gmail.com', 'member'),
-- ('Charlie Reader', 'charlie.reads@gmail.com', 'member');

-- -- BOOKS DATA***
-- INSERT INTO books (title, author, genre_id, row_number, shelf_number, is_available) VALUES
-- ('To Kill a Mockingbird', 'Harper Lee', (SELECT genre_id FROM genres WHERE name = 'Fiction'), 1, 1, TRUE),
-- ('Sapiens: A Brief History of Humankind', 'Yuval Noah Harari', (SELECT genre_id FROM genres WHERE name = 'Non-Fiction'), 1, 2, TRUE),
-- ('Dune', 'Frank Herbert', (SELECT genre_id FROM genres WHERE name = 'Science'), 2, 1, TRUE),
-- ('A People''s History of the United States', 'Howard Zinn', (SELECT genre_id FROM genres WHERE name = 'History'), 2, 2, TRUE),
-- ('The Lord of the Rings', 'J.R.R Tolkien', (SELECT genre_id FROM genres WHERE name = 'Fantasy'), 3, 1, TRUE),
-- ('Sherlock Holmes: The Complete Novels', 'Arthur Conan Doyle', (SELECT genre_id FROM genres WHERE name = 'Mystery'), 3, 2, TRUE);

-- -- BORROWING A BOOK*** 
-- INSERT INTO b_borrowed (book_id, user_id, borrow_date, due_date, return_date, fine)
-- VALUES (
--     (SELECT book_id FROM books WHERE title = 'To Kill a Mockingbird'),
--     (SELECT user_id FROM users WHERE name = 'Bob Reader'),
--     DATE '2025-09-01',
--     DATE '2025-09-06',
--     NULL,
--     0
-- );

-- -- BOOK AVAILAILIBITY CHECK***
-- UPDATE books
-- SET is_available = FALSE
-- WHERE book_id = (SELECT book_id FROM books WHERE title = 'To Kill a Mockingbird');

-- ALTER TABLE users ADD COLUMN password VARCHAR(100) NOT NULL DEFAULT '1234';


-- UPDATE users SET password = 'alice123' WHERE email = 'alice.lib@gmail.com';
-- UPDATE users SET password = 'bob123' WHERE email = 'bob.reads@gmail.com';
-- UPDATE users SET password = 'charlie123' WHERE email = 'charlie.reads@gmail.com';

-- CREATE TABLE policies(
-- policy_id SERIAL PRIMARY KEY,
-- rules TEXT NOT NULL
-- );

-- INSERT INTO policies(rules) VALUES 
-- ('Books can be Borrowed for 7 days.'),
-- ('There is a fine of Rs. 100 every day after the due date.'),
-- ('Maximum 3 Books can be borrowed once.'),
-- ('Handle books with care - damage will incur extra cjarges.')


CREATE OR REPLACE VIEW searching AS
SELECT b.book_id,
b.title,
b.author,
g.genre_type
FROM books b
JOIN genres g ON b.genre_id = g.genre_id

SELECT * FROM searching

-- ALTER TABLE genres
-- RENAME COLUMN name TO genre_type; 


-- ALTER TABLE b_borrowed ADD COLUMN fine_paid BOOLEAN DEFAULT FALSE;
-- SELECT * FROM b_borrowed