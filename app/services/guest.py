from app.repositories import CourseRepository, GroupRepository


class GuestService:
    def __init__(self, course_repo: CourseRepository, group_repo: GroupRepository):
        self._course_repo = course_repo
        self._group_repo = group_repo

    def get_all_courses(self):
        return self._course_repo.get_all()

    def get_course_groups(self, course_id):
        return self._group_repo.get_by_course_id(course_id)

    def get_course_name_by_id(self, course_id):
        return self._course_repo.get_by_id(course_id).name

    def get_group_name_by_id(self, group_id):
        return self._group_repo.get_by_id(group_id).name
