import {Class, Option, Task, User} from "./databaseTypes";

interface UserInfo extends User{
    classes: Class[]
}

interface ClassInfo extends Class{
    tasks: Task[]
}

export interface Question {
    ID: number,
    answer:string,
    question:string,
    options: string[]
}

export interface Questions {
    task: Task,
    attemptID: number,
    questions: Question[]
}