create table if not exists passwords(
       username text primary key,
       hashed_password text not null,
       is_admin integer not null
);
