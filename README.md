## Task Manager API

### WIP (work in progress)

---

### TODO / ROADMAP

* add pagination and sorting

* add priority (low, medium, high)

* tags/categories

  * POST /tags
  * GET /tags
  * POST /task/{task_id}/tags
  * GET /tasks?tag=work

* deadlines/reminders

  * GET /tasks?due_today=true
  * GET /tasks?overdue=true

* stats/analytics

  * GET /stats
  * GET /user/{user_id}/stats

#### refactor

* dedicated action routes

  * /task/{task_id}/complete
  * /task/{task_id}/uncomplete

---

### final structure (planned)

```
/auth

/users
/users/{id}
/users/{id}/tasks

/tasks
/tasks/{id}
/tasks/{id}/complete

/tags

/stats
```
