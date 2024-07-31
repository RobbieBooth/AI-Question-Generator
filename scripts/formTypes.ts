import {Class, Option, Task, User} from "./databaseTypes";

interface UserInfo extends User{
    classes: Class[]
}

interface ClassInfo extends Class{
    tasks: Task[]
}

export interface Question {
    ID: number,
    answer:string | null,
    question:string,
    options: string[],
    studentAnswer: string | null
}

export interface Questions {
    task: Task,
    attemptID: number,
    questions: Question[]
}

export interface StudentAnswer{
    question: Question
    studentAnswer: string | null
}