enum Role{
    Student,
    Lecturer,
    LabTech
}

export interface User {
    authID: string,
    role: Role
}

export interface Class {
    classID: number,
    className: string,
    lecturerID: string
}

interface StudentTakingClass{
    classID: number,
    studentID: string
}

enum ProgrammingLanguage {
    Java,
    Python
}

export interface Task {
    ID: number,
    name: string,
    questionCount: number,
    programmingLanguage: ProgrammingLanguage,
    message: string
}

interface studentAttempt{
    ID: number,
    studentID: string,
    taskID: number,
    timeStamp: EpochTimeStamp,
    codeSubmitted: string,
    questionsCorrect: number
}

interface Question {
    attemptID: number,
    ID: number,
    question: string,
    studentAnswer: null | number,
    answer: number
}

export interface Option{
    questionID: number,
    ID: number,
    option: string,
}