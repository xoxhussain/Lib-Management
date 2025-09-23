from datetime import date, timedelta
import psycopg2
import streamlit as st 
import pandas as pd


class Database:
    def __init__(self, host="localhost", port=5432, dbname="Library", user="postgres", password="password"):
        self.host = host
        self.port = port
        self.db = dbname
        self.user = user
        self.pwd = password
        
    def dbconnect(self):
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=self.db,
            user=self.user,
            password=self.pwd,
        )

    def add_book(self, title, author, genre_id, row_number, shelf_number):
        query = """
            INSERT INTO books (title, author, genre_id, row_number, shelf_number, is_available)
            VALUES (%s, %s, %s, %s, %s, TRUE)
            RETURNING book_id;
        """
        with self.dbconnect() as conn:
            cur = conn.cursor()
            cur.execute(query, (title, author, genre_id, row_number, shelf_number))
            book_id = cur.fetchone()[0]
            conn.commit()
        return f"Book added successfully with ID {book_id}"

    def remove_book(self, book_id):
        query = "DELETE FROM books WHERE book_id = %s"
        with self.dbconnect() as conn:
            cur = conn.cursor()
            cur.execute(query, (book_id,))
            conn.commit()
        return f"Book ID {book_id} removed successfully."

    def update_book(self, book_id, title=None, author=None, genre_id=None, row_number=None, shelf_number=None):
        query = """
            UPDATE books
            SET title = COALESCE(%s, title),
                author = COALESCE(%s, author),
                genre_id = COALESCE(%s, genre_id),
                row_number = COALESCE(%s, row_number),
                shelf_number = COALESCE(%s, shelf_number)
            WHERE book_id = %s
        """
        with self.dbconnect() as conn:
            cur = conn.cursor()
            cur.execute(query, (title, author, genre_id, row_number, shelf_number, book_id))
            conn.commit()
        return f"Book ID {book_id} updated successfully."
    
    def fetch_df(self, query, params=None):
            with self.dbconnect() as conn:
                return pd.read_sql(query, conn, params=params)
            
    def get_books(self):
        return self.fetch_df("SELECT * FROM books ORDER BY book_id")

    def get_genres(self):
        return self.fetch_df("SELECT * FROM genres ORDER BY name")



class Library:
    def __init__(self, db: Database):
        self.db = db

    def add_book(self, *args): return self.db.add_book(*args)
    def remove_book(self, book_id): return self.db.remove_book(book_id)
    def update_book(self, *args): return self.db.update_book(*args)
    def get_books(self): return self.db.get_books()
    def get_genres(self): return self.db.get_genres()

    def login(self, email, password):
        with self.db.dbconnect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT user_id, role FROM users WHERE email=%s AND password=%s", (email, password))
            user = cur.fetchone()
            if user:
                return {"user_id": user[0], "role": user[1]}
            return None        

    def borrow_book(self, book_id, user_id):
        with self.db.dbconnect() as conn:
            cur = conn.cursor()
        
            cur.execute("SELECT COALESCE(SUM(fine), 0) FROM b_borrowed WHERE user_id=%s AND NOT fine_paid", (user_id,))
            total_fines = cur.fetchone()[0]
            if total_fines > 0:
                return "You have outstanding fines. Please pay them before borrowing."

            
            cur.execute("SELECT is_available FROM books WHERE book_id = %s", (book_id,))
            result = cur.fetchone()
            if not result:
                return "Book not found."
            if not result[0]:
                return "Book is already borrowed."
            
            
            cur.execute("""
                SELECT * FROM b_borrowed 
                WHERE book_id = %s AND user_id = %s AND return_date IS NULL
            """, (book_id, user_id))
            if cur.fetchone():
                return "You have already borrowed this book."

            borrow_date = date.today()
            due_date = borrow_date + timedelta(days=0)
            try:
                cur.execute(
                    "INSERT INTO b_borrowed (book_id, user_id, borrow_date, due_date, fine, fine_paid) VALUES (%s, %s, %s, %s, 0, FALSE)",
                    (book_id, user_id, borrow_date, due_date)
                )
                cur.execute("UPDATE books SET is_available=FALSE WHERE book_id=%s", (book_id,))
                conn.commit()
                return "Book borrowed successfully!"
            except Exception as e:
                conn.rollback()
                return f"Error borrowing book: {str(e)}"

    def return_book(self, borrow_id):
        with self.db.dbconnect() as conn:
            cur = conn.cursor()
            today = date.today()
            cur.execute("UPDATE b_borrowed SET return_date=%s WHERE borrow_id=%s", (today, borrow_id))
            cur.execute("SELECT book_id FROM b_borrowed WHERE borrow_id=%s", (borrow_id,))
            book_id = cur.fetchone()[0]
            cur.execute("UPDATE books SET is_available=TRUE WHERE book_id=%s", (book_id,))
            conn.commit()
        return "Book returned!"
    
    def get_policy(self):
        return self.db.fetch_df("SELECT rules FROM policies")

    def get_borrow_history(self, user_id):
        return self.db.fetch_df("SELECT * FROM b_borrowed WHERE user_id=%s ORDER BY borrow_date DESC", (user_id,))
    

    def fines(self, user_id, recalc = True):
        today = date.today()
        daily_fine = 100

        with self.db.dbconnect() as conn:
            cur = conn.cursor()

            if recalc:
            
                cur.execute("""
                    SELECT borrow_id, due_date, return_date, fine_paid 
                    FROM b_borrowed 
                    WHERE user_id=%s AND NOT fine_paid
                """, (user_id,))
                records = cur.fetchall()
                
                for borrow_id, due_date, return_date, fine_paid in records:
                
                    check_date = return_date if return_date else today
                    overdue_days = (check_date - due_date).days
                    

                    if overdue_days > 0:
                        fine = overdue_days * daily_fine
                        cur.execute("UPDATE b_borrowed SET fine = %s WHERE borrow_id = %s", (fine, borrow_id))
                    else:

                        cur.execute("UPDATE b_borrowed SET fine = 0 WHERE borrow_id = %s", (borrow_id,))

                conn.commit()

        return self.db.fetch_df("SELECT * FROM b_borrowed WHERE user_id = %s ORDER BY borrow_date DESC",(user_id,))


    def clear_user_fines(self, user_id):
        with self.db.dbconnect() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE b_borrowed SET fine = 0, fine_paid = True WHERE user_id = %s", (user_id,))
        conn.commit()
        return "All fines have been cleared successfully!"


    def get_total_fines(self, user_id):
        with self.db.dbconnect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COALESCE(SUM(fine), 0) FROM b_borrowed WHERE user_id = %s", (user_id,))
            total = cur.fetchone()[0]
        return total
    
    def search(self):
        return self.db.fetch_df("SELECT * FROM searching")




st.title(" My Library")
st.subheader("Where Knowledge Never Ends.", divider= 'blue')

db = Database()
library = Library(db)



if "user" not in st.session_state:
    st.session_state.user = None



if st.session_state.user is None:
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = library.login(email, password)
        if user:
            st.session_state.user = user
            st.success(f"Welcome! Role: {user['role']}")
        else:
            st.error("Invalid credentials.")

else:
    role = st.session_state.user["role"]
    user_id = st.session_state.user["user_id"]




    if role == "member":
        menu = st.sidebar.radio("Menu", ["Catalogue", "Borrow a Book", "Return a Book", "Policies", "My Fines", "Search Book", "My Borrow History", "Logout"])


        if menu == "Catalogue":
            st.subheader("Book Catalogue", divider= 'violet')
            st.dataframe(library.get_books())

        elif menu == "Borrow a Book":
            st.subheader("Borrow a Book", divider= 'violet')
            books = library.get_books()
            available = books[books["is_available"] == True]
            book_id = st.selectbox("Choose a Book", available["book_id"])
            if st.button("Borrow"):
                msg = library.borrow_book(book_id, user_id)
                if msg == "Book borrowed successfully!":
                    st.success(msg)
                else:
                    st.error(msg)

        elif menu == "Return a Book":
            st.subheader("Return a Book", divider= 'gray')
            borrow_id = st.number_input("Borrow ID", min_value=1, step=1)
            if st.button("Return"):
                st.success(library.return_book(borrow_id))





        elif menu == "Policies":
            st.subheader("Rules and Regulations", divider= 'rainbow')
            policies = library.get_policy()
            st.table(policies)
        



        elif menu == "My Fines":
            st.subheader("Fines", divider= 'violet')
            fines = library.fines(user_id, recalc= True)
            if fines.empty:
                st.success("No Fines")
            else:
                fines["Status"] = fines["fine_paid"].apply(lambda x: "Paid" if x else "Unpaid")
                st.dataframe(fines[["borrow_id", "book_id", "borrow_date", "due_date", "return_date", "fine", "Status"]])

            if st.button("Clear All Fines."):
                result = library.clear_user_fines(user_id)
                st.success(result)
                st.rerun()

        elif menu == "Search Book":
            st.subheader("Search a Book", divider= 'violet')
            search = st.text_input("Enter Book Title, Author or Genre")

            if st.button ("Search"):
                query = """
                    SELECT * FROM searching
                    WHERE title ILIKE %s OR author ILIKE %s OR genre_type ILIKE %s

                """
                results = library.db.fetch_df(query, (f"%{search}%", f"%{search}%", f"%{search}%"))

                if not results.empty:
                    st.dataframe(results)
                else:
                    st.warning("No macth found.")

        elif menu == "My Borrow History":
            st.subheader("My Borrowing History", divider= 'violet')
            history = library.get_borrow_history(user_id)
            if not history.empty:
                st.dataframe(history)
            else:
                st.info("Np Borrowing History")




        elif menu == "Logout":
            st.session_state.user = None
            st.rerun()



    elif role == "librarian":
        menu = st.sidebar.radio("Menu", ["Catalogue", "Add/Remove Books", "Manage Catalogue", "Logout"])


        if menu == "Add/Remove Books":
            st.subheader("Add a Book", divider= 'violet')
            with st.form("add_book_form"):
                title = st.text_input("Title")
                author = st.text_input("Author")
                genres = library.get_genres()
                genre_id = st.selectbox("Genre", genres["genre_id"],
                                        format_func=lambda x: genres.loc[genres["genre_id"] == x, "name"].values[0])
                row = st.number_input("Row", min_value=1, step=1)
                shelf = st.number_input("Shelf", min_value=1, step=1)
                if st.form_submit_button("Add Book"):
                    st.success(library.add_book(title, author, genre_id, row, shelf))

            books = library.get_books()
            st.subheader("Remove a Book", divider='violet')
            if not books.empty:
                book_id = st.selectbox("Remove Book", books["book_id"],
                                       format_func=lambda x: books.loc[books["book_id"] == x, "title"].values[0])
                if st.button("Remove"):
                    st.success(library.remove_book(book_id))
        


        elif menu == "Catalogue":
            st.subheader("Catalogue", divider= 'violet')
            st.dataframe(library.get_books())



        elif menu == "Manage Catalogue":
            st.subheader("Update Book Details", divider='violet')
            books = library.get_books()
            if not books.empty:
                book_id = st.selectbox("Choose a Book To Update", books["book_id"],
                                       format_func=lambda x: books.loc[books["book_id"] == x, "title"].values[0])
                new_title = st.text_input("New Title")
                new_author = st.text_input("New Author")
                genres = library.get_genres()
                new_genre_id = st.selectbox(
                    "New Genre", [None] + list(genres["genre_id"]),
                    format_func=lambda x: "None" if x is None else genres.loc[genres["genre_id"] == x, "name"].values[0]
                )
                new_row = st.number_input("New Row Number", min_value=1, step=1)
                new_shelf = st.number_input("New Shelf Number", min_value=1, step=1)
                if st.button("Update Book"):
                    msg = library.update_book(book_id, new_title or None, new_author or None, new_genre_id, new_row, new_shelf)
                    st.success(msg)
            else:
                st.info("No Books Available To Update")



        elif menu == "Logout":

            st.session_state.user = None
            st.rerun()




