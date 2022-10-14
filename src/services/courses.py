import json
import os
from typing import List
from uuid import uuid4
from pydantic import BaseModel
from src.services.users import PublicUser, User
from src.services.database import create_config_collection, check_database, create_database, learnhouseDB, learnhouseDB
from src.services.security import *
from fastapi import FastAPI, HTTPException, status, Request, Response, BackgroundTasks, UploadFile, File
from datetime import datetime

#### Classes ####################################################


class Course(BaseModel):
    name: str
    mini_description: str
    description: str
    photo: str
    learnings: List[str]
    thumbnail : str 
    public: bool
    chapters: List[str]
    org_id: str


class CourseInDB(Course):
    course_id: str
    creationDate: str
    updateDate: str
    authors: List[str]

#####


class CourseElement(BaseModel):
    element_id: str
    content: str
    content_type: str
    position: int


class CourseChapter(BaseModel):
    name: str
    description: str
    course: str
    elements: List[CourseElement]
    position: int


class CourseChapterInDB(CourseChapter):
    coursechapter_id: str
    course_id: str
    creationDate: str
    updateDate: str


#### Classes ####################################################

# TODO : Add courses photo & cover upload and delete


# Courses

async def get_course(course_id: str, org_id :str , current_user: PublicUser):
    await check_database()
    courses = learnhouseDB["courses"]

    course = courses.find_one({"course_id": course_id , "org_id" : org_id})

    # verify course rights
    await verify_rights(course_id, current_user, "read")

    if not course:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Course does not exist")

    course = Course(**course)
    return course


async def create_course(course_object: Course, org_id : str , current_user: PublicUser):
    await check_database()
    courses = learnhouseDB["courses"]

    # generate course_id with uuid4
    course_id = str(f"course_{uuid4()}")
    
    course_object.org_id = org_id

    hasRoleRights = await verify_user_rights_with_roles("create", current_user.user_id, course_id)

    if not hasRoleRights:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Roles : Insufficient rights to perform this action")

    course = CourseInDB(course_id=course_id, authors=[
        current_user.user_id], creationDate=str(datetime.now()), updateDate=str(datetime.now()), **course_object.dict())

    course_in_db = courses.insert_one(course.dict())

    if not course_in_db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Unavailable database")

    return course.dict()

async def update_course_thumbnail(course_id: str , current_user: PublicUser, thumbnail_file: UploadFile | None = None):
    await check_database()

    # verify course rights
    await verify_rights(course_id, current_user, "update")
    
    courses = learnhouseDB["courses"]

    course = courses.find_one({"course_id": course_id})
    # TODO(fix) : the implementation here is clearly not the best one
    if course:
        creationDate = course["creationDate"]
        authors = course["authors"]
        if thumbnail_file: 
            contents = thumbnail_file.file.read()
            name_in_disk = f"{course_id}_thumbnail_{uuid4()}.{thumbnail_file.filename.split('.')[-1]}"
            course = Course(**course).copy(update={"thumbnail": name_in_disk})
            try: 
                with open(f"content/uploads/img/{name_in_disk}", 'wb') as f:
                    f.write(contents)
                    f.close()
                    
            except Exception as e:
                print(e)
                return {"message": "There was an error uploading the file"}
            finally:
                thumbnail_file.file.close()
            
            
            updated_course = CourseInDB(course_id=course_id, creationDate=creationDate, authors=authors, updateDate=str(datetime.now()) , **course.dict())

            courses.update_one({"course_id": course_id}, {
                                "$set": updated_course.dict()})

            return CourseInDB(**updated_course.dict())
                

    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Course does not exist")


async def update_course(course_object: Course, course_id: str, current_user: PublicUser):
    await check_database()

    # verify course rights
    await verify_rights(course_id, current_user, "update")
    
    courses = learnhouseDB["courses"]

    course = courses.find_one({"course_id": course_id})

    if course:
        creationDate = course["creationDate"]
        authors = course["authors"]

        # get today's date
        datetime_object = datetime.now()
        
        updated_course = CourseInDB(
            course_id=course_id, creationDate=creationDate, authors=authors, updateDate=str(datetime_object), **course_object.dict())

        courses.update_one({"course_id": course_id}, {
                        "$set": updated_course.dict()})

        return CourseInDB(**updated_course.dict())

    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Course does not exist")

    


async def delete_course(course_id: str, current_user: PublicUser):
    await check_database()

    # verify course rights
    await verify_rights(course_id, current_user, "delete")

    courses = learnhouseDB["courses"]

    course = courses.find_one({"course_id": course_id})

    if not course:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Course does not exist")

    isDeleted = courses.delete_one({"course_id": course_id})

    if isDeleted:
        return {"detail": "Course deleted"}
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Unavailable database")


async def get_courses(page: int = 1, limit: int = 10 , org_id : str | None = None):
    await check_database()
    courses = learnhouseDB["courses"]
    # TODO : Get only courses that user is admin/has roles of
    # get all courses from database
    all_courses = courses.find({"org_id": org_id}).sort("name", 1).skip(10 * (page - 1)).limit(limit)

    return [json.loads(json.dumps(course, default=str)) for course in all_courses]

# CoursesChapters

async def create_coursechapter(coursechapter_object: CourseChapter, course_id: str, current_user: PublicUser):
    await check_database()
    coursechapters = learnhouseDB["coursechapters"]

    # generate coursechapter_id with uuid4
    coursechapter_id = str(f"coursechapter_{uuid4()}")

    hasRoleRights = await verify_user_rights_with_roles("create", current_user.user_id, coursechapter_id)

    if not hasRoleRights:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Roles : Insufficient rights to perform this action")

    coursechapter = CourseChapterInDB(coursechapter_id=coursechapter_id, creationDate=str(
        datetime.now()), updateDate=str(datetime.now()), course_id=course_id, **coursechapter_object.dict())

    coursechapter_in_db = coursechapters.insert_one(coursechapter.dict())

    if not coursechapter_in_db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Unavailable database")

    return coursechapter.dict()


async def get_coursechapter(coursechapter_id: str, current_user: PublicUser):
    await check_database()
    coursechapters = learnhouseDB["coursechapters"]

    coursechapter = coursechapters.find_one(
        {"coursechapter_id": coursechapter_id})

    if coursechapter:
            # verify course rights
            await verify_rights(coursechapter["course_id"], current_user, "read")
            coursechapter = CourseChapter(**coursechapter)
            
            return coursechapter

    else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="CourseChapter does not exist")

    

async def update_coursechapter(coursechapter_object: CourseChapter,  coursechapter_id: str, current_user: PublicUser):
    await check_database()
    coursechapters = learnhouseDB["coursechapters"]

    coursechapter = coursechapters.find_one(
        {"coursechapter_id": coursechapter_id})

    if coursechapter: 
        # verify course rights
        await verify_rights(coursechapter["course_id"], current_user, "update")
        creationDate = coursechapter["creationDate"]

        # get today's date
        datetime_object = datetime.now()
        
        updated_coursechapter = CourseChapterInDB(
        coursechapter_id=coursechapter_id, creationDate=creationDate, course_id=coursechapter["course_id"], updateDate=str(datetime_object), **coursechapter_object.dict())

        coursechapters.update_one({"coursechapter_id": coursechapter_id}, {
            "$set": updated_coursechapter.dict()})

        return CourseChapterInDB(**updated_coursechapter.dict())

    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Coursechapter does not exist")

    


async def delete_coursechapter(coursechapter_id: str,  current_user: PublicUser):
    await check_database()

    coursechapters = learnhouseDB["coursechapters"]

    coursechapter = coursechapters.find_one(
        {"coursechapter_id": coursechapter_id})

    if coursechapter:
        # verify course rights
        await verify_rights(coursechapter["course_id"], current_user, "delete")
        
        isDeleted = coursechapters.delete_one(
            {"coursechapter_id": coursechapter_id})

        if isDeleted:
            return {"detail": "coursechapter deleted"}
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Unavailable database")

    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Course does not exist")

    


async def get_coursechapters(course_id: str, page: int = 1, limit: int = 10):
    await check_database()
    courses = learnhouseDB["coursechapters"]
    # TODO : Get only courses that user is admin/has roles of
    # get all courses from database
    all_coursechapters = courses.find({"course_id": course_id}).sort(
        "name", 1).skip(10 * (page - 1)).limit(limit)

    return [json.loads(json.dumps(coursechapter, default=str)) for coursechapter in all_coursechapters]

#### Security ####################################################


async def verify_rights(course_id: str, current_user: PublicUser, action: str):
    await check_database()
    courses = learnhouseDB["courses"]

    course = courses.find_one({"course_id": course_id})

    if not course:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Course/CourseChapter does not exist")

    hasRoleRights = await verify_user_rights_with_roles(action, current_user.user_id, course_id)
    isAuthor = current_user.user_id in course["authors"]

    if not hasRoleRights and not isAuthor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Roles/Ownership : Insufficient rights to perform this action")

    return True

#### Security ####################################################
