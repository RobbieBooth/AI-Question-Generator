-- Create the studentTaskAttempt table
# CREATE TABLE user (
#     ID INT AUTO_INCREMENT PRIMARY KEY,
#     AuthID VARCHAR(255) not null
# );


CREATE TABLE studentTaskAttempt (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CodeSubmitted TEXT,
    QuestionsCorrect INT DEFAULT NULL,
    StudentID VARCHAR(255) NOT NULL
#     FOREIGN KEY (StudentID) REFERENCES user(ID) -- Assuming there is a 'students' table with an 'ID' column
);

-- Create the option table first
CREATE TABLE optionTable (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    optionText TEXT
);

-- Now create the question table
CREATE TABLE question (
    attemptID INT,
    ID INT AUTO_INCREMENT PRIMARY KEY,
    Question TEXT,
    StudentAnswer INT DEFAULT NULL,
    Answer INT NOT NULL,
    FOREIGN KEY (attemptID) REFERENCES studentTaskAttempt(ID),
    FOREIGN KEY (StudentAnswer) REFERENCES optionTable(ID),
    FOREIGN KEY (Answer) REFERENCES optionTable(ID)
);

-- Create the table to link questions and options (if needed)
CREATE TABLE questionOptions (
    QuestionID INT,
    OptionID INT,
    PRIMARY KEY (QuestionID, OptionID),
    FOREIGN KEY (QuestionID) REFERENCES question(ID),
    FOREIGN KEY (OptionID) REFERENCES optionTable(ID)
);