create table if not exists amt_task(
       amt_task_id text primary key,
       hitId text not null,
       assignmentId text not null
);
