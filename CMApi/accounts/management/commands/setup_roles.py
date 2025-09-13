# mainapp/management/commands/setup_roles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps

# mapping role_name -> { model_label: [permcodenames] }
ROLE_MAP = {
    "Teacher": {
        "mainapp.course": ["view_course", "add_course", "change_course", "delete_course"],
        "mainapp.lesson": ["view_lesson", "add_lesson", "change_lesson", "delete_lesson"],
        "mainapp.assignment": ["view_assignment", "add_assignment", "change_assignment", "delete_assignment", "grade_assignment"],
        "mainapp.submission": ["view_submission", "change_submission"],
        "mainapp.progress": ["view_progress", "change_progress"],
    },
    "Student": {
        "mainapp.course": ["view_course"],
        "mainapp.lesson": ["view_lesson"],
        "mainapp.assignment": ["view_assignment"],
        "mainapp.submission": ["view_submission", "add_submission", "change_submission"],
        "mainapp.progress": ["view_progress"],
    },
    "Admin": "ALL",  # shorthand — give all permissions
    "Guest": {
        "mainapp.course": ["view_course"]
    }
}

class Command(BaseCommand):
    help = "Create groups and set permissions for roles"

    def handle(self, *args, **options):
        # create groups
        for role in ROLE_MAP:
            group, _ = Group.objects.get_or_create(name=role)
            self.stdout.write(f"Ensured group: {role}")

            if ROLE_MAP[role] == "ALL":
                # all permissions
                perms = Permission.objects.all()
                group.permissions.set(perms)
                self.stdout.write(f"  -> set ALL permissions for {role}")
                continue

            # collect Permission objects
            perm_objs = []
            for model_label, codename_list in ROLE_MAP[role].items():
                app_label, model = model_label.split(".")
                try:
                    ct = ContentType.objects.get(app_label=app_label, model=model)
                except ContentType.DoesNotExist:
                    self.stderr.write(f"ContentType not found: {model_label}. Did you run migrations?")
                    continue
                for codename in codename_list:
                    try:
                        perm = Permission.objects.get(content_type=ct, codename=codename)
                        perm_objs.append(perm)
                    except Permission.DoesNotExist:
                        self.stderr.write(f"Permission not found: {codename} for {model_label}")
            group.permissions.set(perm_objs)
            self.stdout.write(f"  -> set {len(perm_objs)} permissions for {role}")

        self.stdout.write(self.style.SUCCESS("Groups and permissions setup complete."))
